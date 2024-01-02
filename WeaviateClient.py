import weaviate
import dotenv
import os

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
    # print("adding item...", item, uuid)

def add_batch_items(class_name, batch_items):
    client.batch.configure(batch_size=100)  # Configure batch
    with client.batch as batch:
        for item in batch_items:
            batch.add_data_object(
                data_object=item,
                class_name=class_name,
            )


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
# TODO #5 Modify this function so that the return type remains the former wherever this function is used outside OpenAIClient.py fiile. Use the "all_props" bool for it.
def search_items(class_name, properties=[""], text_query="", k=10, path="", all_props = False):
    properties.append("path")
    properties.append("page_number")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    results = (client.query.get(class_name=class_name, properties=properties)
               .with_where(pathFilter)
               .with_near_text({"concepts": text_query})
               .with_limit(k)
               .do()
               )
    if all_props:
        # print("search results: ", results)
        # concatenate all text from the results in ["data"]["Get"][class_name][i][properties[0]]
        search_result = {}
        for i in range(len(results["data"]["Get"][class_name])):
            if search_result.get(results["data"]["Get"][class_name][i][properties[1]]) is None:
                search_result[results["data"]["Get"][class_name][i][properties[1]]] = [[results["data"]["Get"][class_name][i][properties[0]] + ".", results["data"]["Get"][class_name][i][properties[2]]]]
            else:
                search_result[results["data"]["Get"][class_name][i][properties[1]]].append([results["data"]["Get"][class_name][i][properties[0]] + ".", results["data"]["Get"][class_name][i][properties[2]]])
        return search_result
    else:
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

# find_specific_item(className="File_store", path = "test")

