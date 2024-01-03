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


def add_class_modified(class_name, description="", variables=[]):
    '''
    Unlike add_class, for variable "path", "tokenization" is set to "field"
    Otherwise, the function is the same
    
    '''

    try:
        properties = []

        for var in variables:
            if var == "path":
                properties.append(
                  {"dataType": ["string"], "name": var, "description": var, "tokenization":"field"}  
                )
            else:
                properties.append(
                    {"dataType": ["text"], "name": var, "description": var}
                )

            class_obj = {
            "class": class_name,
            "description": description,
            "properties": properties,
            "vectorizer": "text2vec-openai"
            }
            client.schema.create_class(class_obj)
            print("Successfully created class: ", class_name)
            return "Success"

    except Exception as e: 
        # print exception instead of only printing that the class already exists
        print("Error creating class:", e)
        return "Failure"

# # testing add_class_modified and checking properties.
# # print(add_class_modified("Another_class", variables=["path", "url"])) # creating class with field tokenization for path
# # print(add_class("Another_class_og", variables=["path", "url"])) # creating class with original word tokenization for path
    
# # both of the above are for testing delete

# # sanity checks
# print(get_class_names())
# schema = client.schema.get()
# import json
# print the class added last
# print(json.dumps(schema["classes"][-1], indent=4))


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
def delete_items(className, path, dry_run=False):
    '''
    Modified to add dry_run as a parameter for testing
    Also prints number of chunks and matches instead of result only
    number of chunks and matches should be equal

    '''
    client.batch.consistency_level = weaviate.data.replication.ConsistencyLevel.ALL  # default QUORUM
    try:
        conditions = {"path": ["path"], "operator": "Equal", "valueText": path}
        
        result = client.batch.delete_objects(
            class_name=className,
            where=conditions,
            output="verbose",
            dry_run=dry_run
        )

        num_chunks = len(result["results"]["objects"])
        num_matches = result["results"]["matches"]

        print("result: ", result, "\nNumber of chunks: ", num_chunks,
              "\nMatches: ", num_matches)

        return "Success"
    except Exception as e:
        print("Error deleting items:", e)
        return "Failure"
    
def delete_items_modified(className, path, dry_run=False):
    '''
    Same as above but valueText cannot be used for type "string"

    '''
    client.batch.consistency_level = weaviate.data.replication.ConsistencyLevel.ALL  # default QUORUM
    try:
        conditions = {"path": ["path"], "operator": "Equal", "valueString": path} # valueText cannot be used for type "string"
        
        result = client.batch.delete_objects(
            class_name=className,
            where=conditions,
            output="verbose",
            dry_run=dry_run
        )

        num_chunks = len(result["results"]["objects"])
        num_matches = result["results"]["matches"]

        print("result: ", result, "\nNumber of chunks: ", num_chunks,
              "\nMatches: ", num_matches)

        return "Success"
    except Exception as e:
        print("Error deleting items:", e)
        return "Failure"

# delete_items("File_store", path="c75767dd-172c-463c-aafc-1e2dfddc1b32/t1/2/2/short_1706.03762.pdf", dry_run=True)

'''
Testing delete with similar paths

'''
data_objects=[
    {
        "path" : "abcd/test_a.pdf",
    }, 

    {
        "path" : "abcd/test_b.pdf",
    },

    {
        "path" : "abcd/abc/test_b.pdf",
    }   
    ]

# for item in data_objects: # run only once to add
#     add_item("Another_class_og", item)
#     add_item("Another_class", item)

print("***ORIGINAL CLASS***\n", delete_items("Another_class_og", path="abcd/test_a.pdf", dry_run=True))
print("***MODIFIED CLASS***\n", delete_items_modified("Another_class", path="abcd/test_a.pdf", dry_run=True))

'''
End of preliminary testing for delete

'''

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


