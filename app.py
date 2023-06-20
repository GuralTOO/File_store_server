from flask import Flask, request
import requests
import WeaviateClient
import json

app = Flask(__name__)

class_name = "File_store"


# expects a 'path' 'url' and 'type' in the request body
@app.route('/upload', methods=['POST'])
def upload():
    print("got request: " + str(request.json) + "\n")
    document_type = request.json.get('type')
    path = request.json.get('path')
    url = request.json.get('url')
    print(path, document_type)
    response = {
        "type": document_type,
        "path": path,
        "url": url,
        "message": "Data received!"
    }

    return jsonify(response), 200
    # try:
    #     WeaviateClient.load_pdf(class_name=class_name, properties={
    #         "type": document_type, "path": path, "url": url})
    #     return f"Uploaded: Type={document_type}, Path={path}, URL={url}", 200

    # except:
    #     print("Error loading page")
    #     return f"Error loading page", 500


# expects a json object of properties to search for. Possible properties are: type, path, url, text, and page_number
@app.route('/delete', methods=['POST'])
def delete():
    # default to empty dictionary if not present
    properties = json.loads(request.args.get('properties', '{}'))
    print(properties)
    try:
        WeaviateClient.delete_items(
            class_name=class_name, properties=properties)
        return f"Deleted: path={properties['path']}", 200
    except:
        print("Error deleting entry")
        return f"Error deleting entry", 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
