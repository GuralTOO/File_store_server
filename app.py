from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from flask_socketio import SocketIO, send
import WeaviateClient
import OpenAIClient
import json
from upload import upload_file

app = Flask(__name__)
CORS(app, supports_credentials=True)  # Add CORS so that the frontend can access this server
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class_name = "File_store_ver2"


@socketio.on('searchStream')
def handleSearchStream(data):
    # extract "path" and "query" from data
    path = data.get('path')
    query = data.get('query')
    print("got request: " + str(data) + "\n")
    print("path: " + path + "\n")
    print("query: " + query + "\n")
    result = OpenAIClient.get_answer_stream(question=query, path=path)
    for part in result:
        # print(part)
        send(part)


# expects a 'path' 'url' and 'type' in the request body
@app.route('/upload', methods=['POST'])
async def upload():
    print("got request: " + str(request.json) + "\n")
    document_type = request.json.get('type')
    path = request.json.get('path')
    url = request.json.get('url')

    # if the request has a "contentType", then get it, if not, set it to ""
    contentType = request.json.get('contentType', "")

    # if the contentType is "research" then we want to extract the following information from the file:
    # authors, key results, and methods
    result = await upload_file(document_type=document_type,
                         path=path, url=url, contentType=contentType)

    response = {
        "type": document_type,
        "path": path,
        "url": url,
        "message": result
    }

    return jsonify(response), 200


@app.route('/search', methods=['POST'])
def search():
    print("got request: " + str(request.json) + "\n")
    query = request.json.get('query')
    path = request.json.get('path')
    result = OpenAIClient.get_answer(path=path, query=query)
    response = {
        "path": path,
        "query": query,
        "message": result
    }
    return jsonify(response), 200


# expects a json object of properties to search for. Possible properties are: type, path, url, text, and page_number
@app.route('/delete', methods=['POST'])
def delete():
    # default to empty dictionary if not present
    path = request.json.get('path')
    print("Received a delete request for path: " + path + "\n")

    try:
        WeaviateClient.delete_items(
            className=class_name, path=path)
        return jsonify({"message": f"Deleted path={path}"}), 200
    except Exception as e:
        print("Error deleting entry" + str(e) + "\n")
        return jsonify({"error": f"Error deleting entry: {e}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
