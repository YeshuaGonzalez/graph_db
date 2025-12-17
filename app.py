import sys
sys.path.append(r"./gratools")
from gratools.cy_uti import ex_qry
from gratools.cy_uti import query
from gratools.cy_uti import graph_to_lists

import os
import neo4j
import networkx as nx
import pandas as pd

from flask import Flask, flash, request, redirect, url_for, render_template, Response, jsonify
from flask_excel import make_response_from_array, make_response_from_dict, make_response_from_records
from neo4j import GraphDatabase, basic_auth
from neo4j import Result
from neo4j import RoutingControl
from werkzeug.utils import secure_filename
#from typing_extensions import LiteralString
#from typing import cast
#from textwrap import dedent
from json import dumps

UPLOAD_FOLDER = r"C:\Users\Sistemas\Documents\Python\graphs\upload_folder"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_development_key')

url_n4j = os.getenv("NEO4J_URI", "bolt://192.168.50.12:7687")
port_n4j = int(os.getenv("PORT", 8000))
#driver_n4j = GraphDatabase.driver(url_n4j, auth=("neo4j", "N8jJXntl"))
driver_n4j = GraphDatabase.driver(url_n4j, auth=("neo4j", "password"))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
def query(q: LiteralString) -> LiteralString:
    # this is a safe transform:
    # no way for cypher injection by trimming whitespace
    # hence, we can safely cast to LiteralString
    return cast(LiteralString, dedent(q).strip())
"""

#   P A N T A L L A   P R I N C I P A L
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print("Subir archivos ACTIVADO")
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            print("Archivos no detectados")
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('upload_file', name=filename))
    all_files = os.listdir(UPLOAD_FOLDER)
    rows = ""
    for index,file in enumerate(all_files):
        rows = rows + f"""
                <tr><td>{index + 1}</td>
                <td>{file}</td>
                <td><button onclick = "click_file(\'{file}\')">Charge File</button></td></tr>\n
            """
    #print(f"ROWS: {rows}")
    files_table = f'''
        <table>
            <tr>
                <th>#</td>
                <th>Nombre del archivo</td>
                <th>Control</td>
            </tr>
                {rows}
        </table> 
        '''
    return render_template('excel_view_v2.html', files_table=files_table)

@app.route('/clic_file', methods=['POST', 'GET'])
def clic_file():
    if request.method == 'POST':
        data = request.get_json()
        param1 = data.get('param1')
        print(f"PARAM1 :{param1}")
        # Process parameters
        #return jsonify({"message": f"Received dynamic: {param1}"})
        return "OK"
    elif request.method == 'GET':
        name_file = request.args.get('file')
        df = pd.read_excel(UPLOAD_FOLDER + fr"\{name_file}")
        #df_rows_10 = df.iloc[:10]
        df_rows_10 = df.iloc[:]
        excel_html = df_rows_10.to_html(classes='table table-striped')

        graph = nx.Graph()
        for index, row in df.iterrows():
            #print(f"Index: {index}, Name: {row['Name']}, Age: {row['Age']}")

            ref_aesa = row['t_ref_aesa']
            spec1 = row['s1_desc_spec']
            spec2 = row['s2_desc_spec']
            geo = row['m_geo']

            '''graph.add_nodes_from([
                (f'{ref_aesa}', {
                    "type": "test", 
                    "t_ref_itsa": row['t_ref_itsa'],
                    "t_fecha": row['t_fecha'],
                    "t_age": row['t_age'],
                    "t_cli": row['t_cli'],
                    "t_ope": row['t_ope'],
                    "t_mach": row['t_mach'],
                    }), 
                (f'{spec1}', {
                    "type": "spec",
                    "desc_spec": row["s1_desc_spec"],
                    "spec": row["s1_spec"],
                    "prov": row["s1_prov"],
                    "grit": row["s1_grit"],
                    "pzas_mat": row["s1_pzas_mat"],
                    "desg": row["s1_desg"],
                    "efi": row["s1_efi"],
                    "vel": row["s1_vel"],
                    "acab": row["s1_acab"],
                    }),
                (f'{spec2}', {
                    "type": "spec", 
                    "desc_spec": row["s2_desc_spec"],
                    "spec": row["s2_spec"],
                    "prov": row["s2_prov"],
                    "grit": row["s2_grit"],
                    "pzas_mat": row["s2_pzas_mat"],
                    "desg": row["s2_desg"],
                    "efi": row["s2_efi"],
                    "vel": row["s2_vel"],
                    "acab": row["s2_acab"],
                    }),
                (f'{geo}', {
                    "type": "geo", 
                    "m_geo": row['m_geo'],
                    "m_mat": row['m_mat'],
                    }),
                ])'''

            graph.add_nodes_from([
                (f'{ref_aesa}', {
                    "type": "test", 
                    }), 
                (f'{spec1}', {
                    "type": "spec",
                    "desc_spec": row["s1_desc_spec"],
                    }),
                (f'{spec2}', {
                    "type": "spec", 
                    "desc_spec": row["s2_desc_spec"],
                    }),
                (f'{geo}', {
                    "type": "geo", 
                    "m_geo": row['m_geo'],
                    "m_mat": row['m_mat'],
                    }),
                ])

            graph.add_edges_from([
                (f'{ref_aesa}', f'{spec1}'),
                (f'{ref_aesa}', f'{spec2}'),
                (f'{ref_aesa}', f'{geo}'),
                ])
        #graph = nx.Graph()
        #graph.add_edges_from([(1, 2), (1, 3), (2, 4), (2, 5), (3, 3)])

        # Paso 2: Convertir los datos a una lista de diccionarios para vis.js
        nodes_list = []
        for n,a in graph.nodes(data=True):
            dict_tmp = {}
            dict_tmp['id'] = n
            dict_tmp['label'] = f"{n}"
            dict_tmp['group'] = a['type']
            if a["type"] == "test":
                #dict_tmp["Referencia ITSA"] = a["t_ref_itsa"]
                #dict_tmp["Fecha"] = a['t_fecha'].strftime("%Y-%m-%d")
                #dict_tmp["Agente"] = a['t_age']
                #dict_tmp["Cliente"] = a['t_cli']
                #dict_tmp["Operación"] = a['t_ope']
                #dict_tmp["Maquina"] = a['t_mach']
                pass

            if a["type"] == "spec":
                #dict_tmp["Especificación y grano"] = a["desc_spec"]
                #dict_tmp["Especificación"] = a["spec"]
                #dict_tmp["Proveedor"] = a["prov"]
                #dict_tmp["Grano"] = a["grit"]
                pass
                '''dict_tmp["Ind. piezas"] = a["pzas_mat"]
                dict_tmp["Ind. desgaste"] = a["desg"]
                dict_tmp["Ind. eficiencia"] = a["efi"]
                dict_tmp["Ind. velocidad"] = a["vel"]
                dict_tmp["Ind. acabado"] = a["acab"]'''

            if a["type"] == "geo":
                #dict_tmp["Geometria"] = a['m_geo']
                #dict_tmp["Material"] = a['m_mat']
                pass

            nodes_list.append(dict_tmp)
        '''nodes_list = [{
                "id": n, 
                "label": f"{n}", 
                "group":a['type'], 
                "Referencia_ITSA" : a["Referencia_ITSA"]} for n,a in graph.nodes(data=True)]'''

        edges_list = [{"from": u, "to": v} for u, v in graph.edges()]

        # Paso 3: Convertir a JSON
        nodes_json = dumps(nodes_list)
        print(f"Número de nodos: {len(nodes_list)}")
        edges_json = dumps(edges_list)
        print(f"Número de artistas: {len(edges_list)}")

        if name_file != "":
            return render_template(
                'excel_data_v3.html', 
                name_file=name_file, 
                data_table = excel_html,
                nodes_data = nodes_json,
                edges_data = edges_json,
                )
        else:
            return "File not specified", 400

@app.route("/searching", methods=['POST', 'GET'])
def searching():
    if request.method == 'GET':
            return render_template(
                'searching.html',
                )
    if request.method == "POST":
        data = request.json
        cypher_query = data.get('cypher_query')
        print(f"Searching >> {cypher_query}")
        graph_nx = ex_qry(driver_n4j, "neo4j", cypher_query)
        nodes_list, edges_list = graph_to_lists(graph_nx)
        # Paso 3: Convertir a JSON
        nodes_json = dumps(nodes_list)
        edges_json = dumps(edges_list)
        all_data = dumps({"nodes": nodes_list, "edges": edges_list})
        #return {"message":"Respuesta desde python"}
        return jsonify(all_data), 200

@app.route("/props", methods=['POST'])
def props():
    if request.method == "POST":
        data = request.json
        props_command = data.get('props_command')

        records, summary, keys = driver_n4j.execute_query(
            query(props_command),
            database_="neo4j",
            routing_=RoutingControl.READ,
        )
        props_list = [record['property'] for record in records]
        types_list = [record['propertyTypes'] for record in records]
        all_data = dumps({"props": props_list, "types": types_list})
        return jsonify(all_data), 200

@app.route("/filtering", methods=['POST', 'GET'])
def filtering():
    if request.method == 'GET':
            return render_template(
                'filtering_v3.html',
                )
    if request.method == "POST":
        data = request.json
        cypher_query = data.get('cypher_query')
        print(f"Filtering >> {cypher_query}")
        graph_nx = ex_qry(driver_n4j, "neo4j", cypher_query)
        nodes_list, edges_list = graph_to_lists(graph_nx)
        # Paso 3: Convertir a JSON
        nodes_json = dumps(nodes_list)
        edges_json = dumps(edges_list)
        all_data = dumps({"nodes": nodes_list, "edges": edges_list})
        return jsonify(all_data), 200

@app.route("/graph")
def get_graph():
    records, _, _ = driver_n4j.execute_query(
        query("""
            MATCH (s:Spec)-[l:TESTED_IN]-(t:Test)
            RETURN t.ref_aesa AS test, collect(s.des_spec) AS spec
            LIMIT $limit
        """),
        database_="neo4j",
        routing_=RoutingControl.READ,
        limit=request.args.get("limit", 10)
    )
    nodes = []
    rels = []
    i = 0
    for record in records:
        nodes.append({"title": record["test"], "label": "test"})
        target = i
        i += 1
        for name in record["spec"]:
            actor = {"title": name, "label": "spec"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    print(f"Number of record: {len(nodes)}")
    return Response(
        dumps({"nodes": nodes, "links": rels}),
        mimetype="application/json")

if __name__ == '__main__':
   app.run(debug=True, host='192.168.50.195', port=5000)
