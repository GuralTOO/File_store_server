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


# TODO: Delete this shiiii

# def get_filter_search(properties=["path"], path=""):
#     response = (
#     client.query
#     .get(class_name="File_store", properties=properties)
#     .with_where({
#         "path": ["path"],
#         "operator": "Equal",
#         "valueText": path
#     }).do()
#     )
#     return response["data"]["Get"]["File_store"]

# # 
# def get_bm25_search(properties=["path"], path=""):
#     response = (
#     client.query
#     .get(class_name="File_store", properties=properties)
#     .with_bm25(
#       query= path
#     )
#     .do())

#     return response["data"]["Get"]["File_store"]

# # search_result = get_bm25_search(["path"], path="c75767dd-172c-463c-aafc-1e2dfddc1b32/t1/2/2/short_1706.03762.pdf")

# # filter_search_result = get_filter_search(["path"], path="c75767dd-172c-463c-aafc-1e2dfddc1b32/t1/2/2/short_1706.03762.pdf")

# # print(filter_search_result, len(filter_search_result))



# path1 = "c75767dd-172c-463c-aafc-1e2dfddc1b32/t2/t1/short_1706.03762.pdf"
# path2 = "c75767dd-172c-463c-aafc-1e2dfddc1b32/t1/2/short_1706.03762.pdf"
# # delete_items("File_store", path2)

# def add_cool_class():
#     class_name = "dolar_sign"
#     description = "A class to store files"
#     variables = ["text", "page_number", "path"]
    
#     try:
#         properties = []
#         for var in variables:
#             if var == "path":
#                 properties.append(
#                     {"dataType": ["string"],
#                      "name": var, 
#                      "description": var, 
#                      "tokenization": "field"
#                     })
#             else:
#                 properties.append(
#                     {"dataType": ["text"], "name": var, "description": var})
#         class_obj = {
#             "class": class_name,
#             "description": description,
#             "properties": properties,
#             "vectorizer": "text2vec-openai"
#         }
#         client.schema.create_class(class_obj)
#     except Exception as e:
#         print("Class already exists", e)
        
# add_cool_class()
# delete_class("Dolar_sign")
# print(get_class_names())




