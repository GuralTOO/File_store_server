import weaviate
import dotenv
import os
import pypdf
from pdf2image import convert_from_path
import pytesseract
import json
import io
import requests
import datetime
from utils import utils
import tempfile
import time

dotenv.load_dotenv()
client = weaviate.Client(
    # url="http://localhost:8080",
    url="http://206.189.199.72:8080/",  # Replace with your endpoint
    additional_headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
    }
)


def get_client():
    return client


classes = client.schema.get().get("classes")


def get_class_names():
    class_names = [c["class"] for c in classes]
    return class_names


def add_class(class_name, description="", variables=[]):
    try:
        properties = []
        for var in variables:
            properties.append(
                {"dataType": ["text"], "name": var, "description": var})
        class_obj = {
            "class": class_name,
            "description": description,
            "properties": properties,
            "vectorizer": "text2vec-openai"
        }
        client.schema.create_class(class_obj)
    except:
        print("Class already exists")


def delete_class(class_name):
    try:
        client.schema.delete_class(class_name=class_name)
    except:
        print("Class does not exist")


def add_item(class_name, item):
    uuid = client.data_object.create(class_name=class_name, data_object=item)
    print("adding item...", item, uuid)



# Delete document takes in a classname and a path and deletes all items with that path
def delete_items(className, path):
    client.batch.consistency_level = weaviate.data.replication.ConsistencyLevel.ALL  # default QUORUM
    try:
        conditions = {"path": ["path"], "operator": "Equal", "valueText": path}
        
        result = client.batch.delete_objects(
            class_name=className,
            where=conditions,
            output="verbose",
            dry_run=False
        )
        print("result: ", result)
        return "Success"
    except Exception as e:
        print("Error deleting items:", e)
        return "Failure"
    


# search for items in a class using nearest neighbor search
def search_items(class_name, properties=[""], text_query="", k=10, path=""):
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    results = (client.query.get(class_name=class_name, properties=properties)
               .with_where(pathFilter)
               .with_near_text({"concepts": text_query})
               .with_limit(k)
               .do()
               )
    print("search results: ", results)
    # concatenate all text from the results in ["data"]["Get"][class_name][i][properties[0]]
    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"
    return search_result



# print(get_class_names())
def find_specific_item(className, path):
    conditions = {"path": "path", "operator": "Equal", "valueText": path}
    results = client.query.get(class_name=className, properties=["text"]).with_where(
        conditions).do()
    # print the results in ["data"]["Get"][class_name][i][properties[0]]
    for i in range(len(results["data"]["Get"][className])):
        print(results["data"]["Get"][className][i]["text"])
    print(len(results["data"]["Get"][className]))    
    return results


