#                                                                            #
import networkx as nx
from neo4j import RoutingControl
from typing_extensions import LiteralString
from typing import cast
from textwrap import dedent


def ex_qry(driver_n4j, db_name, cypher_query):
    '''
    cypher_query >> comando de consulta cypher
         C o m a n d o   M A T C H 
        Se requiere que esta consulta se englobe en una variable "p"
        para poder iterar sonre el resultado
    '''
    records, summary, keys = driver_n4j.execute_query(
        query(cypher_query),
        database_=db_name,
        routing_=RoutingControl.READ,
    )

    #confirmar que se uso la variable dentro de la consulta
    graph = nx.Graph()
    if 'p' in keys:
        for record in records:
            #register nodes
            nodes = record['p'].nodes
            for node in nodes:
                data_node = node._properties #dictionary type
                labels_node = list(node._labels)
                if 'Mat' in labels_node: #Material
                    id_node = data_node['geo'] + "/" + data_node['mat']
                    data_node['group'] = 'Mat'
                elif 'Test' in labels_node: #Prueba
                    id_node = data_node['ref_aesa']
                    data_node['group'] = 'Test'
                elif 'Spec' in labels_node: #Especificación
                    id_node = data_node['des_spec']
                    data_node['group'] = 'Spec'
                graph.add_nodes_from([(f'{id_node}', data_node)])

            #register relationships
            relationships = record['p'].relationships
            for relation in relationships:
                data_rel = relation._properties
                nodes_tmp = relation.nodes
                #only related two nodes
                id_nodes = []
                for i_nod, node in enumerate(nodes_tmp):
                    labels_node = list(node._labels)
                    data_node = node._properties
                    if 'Mat' in labels_node: #Material
                        id_node = data_node['geo'] + "/" + data_node['mat']
                    elif 'Test' in labels_node: #Prueba
                        id_node = data_node['ref_aesa']
                    elif 'Spec' in labels_node: #Especificación
                        id_node = data_node['des_spec']
                    id_nodes.append(id_node)

                graph.add_edges_from([
                    (f'{id_nodes[0]}', f'{id_nodes[1]}', data_rel),
                ])
    return graph

def graph_to_lists(graph):
    # Paso 2: Convertir los datos a una lista de diccionarios para vis.js
    nodes_list = []
    for n,a in graph.nodes(data=True):
        dict_tmp = {}
        dict_tmp['id'] = n
        dict_tmp['label'] = f"{n}"
        
        key_lst = list(a.keys())
        if 'fecha' in key_lst:
            key_lst.remove('fecha')
            dict_tmp['fecha'] = a['fecha'].strftime("%Y-%m-%d")

        for key in key_lst:
            dict_tmp[key] = a[key]
        nodes_list.append(dict_tmp)
        
    edges_list = []
    for u,v, data in graph.edges(data=True):
        dict_tmp = {}
        dict_tmp['from'] = u
        dict_tmp['to'] = v
        
        key_lst = list(data.keys())
        for key in key_lst:
            dict_tmp[key] = data[key]
        edges_list.append(dict_tmp)
    #edges_list = [{"from": u, "to": u} for u, v, data in graph.edges(data=True)]

    return nodes_list, edges_list


def query(q: LiteralString) -> LiteralString:
    # this is a safe transform:
    # no way for cypher injection by trimming whitespace
    # hence, we can safely cast to LiteralString
    return cast(LiteralString, dedent(q).strip())