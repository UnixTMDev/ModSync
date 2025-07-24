from flask import Flask,send_file
from flask import request, jsonify
import shutil
import os
import json

app = Flask(__name__)

if not os.path.exists("./mods"):
    os.mkdir("./mods")

UPLOAD_FOLDER = "./mods"

@app.route('/mods', methods = ['GET', 'POST', 'DELETE'])
def mods():
    if request.method == 'GET':
        return json.dumps(os.listdir("./mods"))
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({'message': f'{file.filename} uploaded successfully!'}), 200
    if request.method == 'DELETE':
        filename = request.headers["filename"].replace("..","")
        shutil.rmtree("./mods/"+filename)
        return filename, 200
    else:
        # POST Error 405 Method Not Allowed
        return 405

@app.route('/mod/<string:filename>', methods = ['GET'])
def mod_get(filename: str):
    filename = filename.replace("..","")
    if os.path.exists("./mods/"+filename):
        return send_file("./mods/"+filename)
    else: 
        return "",404
    
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print(request.headers)
    return "", 404
app.run(host="127.0.0.3",port=4700)