from flask import Flask, send_file, request, jsonify
import os

app = Flask(__name__)
BASE_SERVERS_DIR = "./servers"

def server_path(server: str):
    return os.path.join(BASE_SERVERS_DIR, server)

# Recursively build directory tree with download URLs
@app.route('/list/<server>', methods=['GET'])
def list_all_files(server):
    root = server_path(server)

    if not os.path.exists(root):
        return jsonify({"error": "Server not found"}), 404

    def list_dir_recursive(path):
        output = {}
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                output[entry] = list_dir_recursive(full)
            else:
                rel_path = os.path.relpath(full, root)
                output[entry] = f"/download/{server}/{rel_path.replace(os.sep, '/')}"
        return output

    return jsonify(list_dir_recursive(root))
@app.route('/srvlist', methods=['GET'])
def list_servers():
    ls = os.listdir(BASE_SERVERS_DIR)
    return jsonify(ls), 200
@app.route("/info/<server>", methods=["GET"])
def get_srv_info(server):
    with open(f"{BASE_SERVERS_DIR}/{server}/server.json","r") as f:
        data = f.read()
    return data, 200

# Serve any file from the given server
@app.route('/download/<server>/<path:filepath>', methods=['GET'])
def download_file(server, filepath):
    filepath = filepath.replace("..", "")  # avoid path traversal
    full_path = os.path.join(server_path(server), filepath)

    if os.path.exists(full_path) and os.path.isfile(full_path):
        return send_file(full_path)
    else:
        return "", 404

# Optional: Serve client.py
@app.route('/update', methods=["GET"])
def update():
    try:
        with open("./client.py", "r") as f:
            return f.read(), 200
    except FileNotFoundError:
        return "", 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    print(request.headers)
    return "", 404

if __name__ == '__main__':
    app.run(host="127.0.0.3", port=4700)
