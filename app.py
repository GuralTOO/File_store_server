from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send
import WeaviateClient
import OpenAIClient
import json


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


class_name = "File_store"


@socketio.on('searchStream')
def handleSearchStream(data):
    # extract "path" and "query" from data
    path = data.get('path')
    query = data.get('query')
    print("got request: " + str(data) + "\n")
    print("path: " + path + "\n")
    print("query: " + query + "\n")
    # socketio.emit('searchStream', "hello")
    result = OpenAIClient.get_answer_stream(question=query, path=path)
    for part in result:
        print(part)
        socketio.emit('searchStream', part)


# expects a 'path' 'url' and 'type' in the request body
@app.route('/upload', methods=['POST'])
def upload():
    print("got request: " + str(request.json) + "\n")
    document_type = request.json.get('type')
    path = request.json.get('path')
    url = request.json.get('url')

    # make the weaviate call
    result = WeaviateClient.load_pdf(class_name=class_name, properties={
        "type": document_type, "path": path, "url": url})
    print(result)
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
    properties = {"path": path}
    try:
        WeaviateClient.delete_items(
            class_name=class_name, properties=properties)
        return f"Deleted: path={properties['path']}", 200
    except Exception as e:
        print("Error deleting entry" + str(e) + "\n")
        return f"Error deleting entry" + str(e), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
