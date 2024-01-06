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


# Modified add_class function to add a class with field tokenization all variables except text
def add_class(class_name, description="", variables=[]):
    try:
        properties = []

        for var in variables:
            if var == "text":
                properties.append(
                    {"dataType": ["text"], "name": var, "description": var}
                )
            else:
                properties.append(
                  {"dataType": ["string"], "name": var, "description": var, "tokenization":"field"}  
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
        print("Error creating class:", e)
        return "Failure"


def delete_class(class_name):
    try:
        client.schema.delete_class(class_name=class_name)
        print("Successfully deleted class: ", class_name)
    except:
        print("Class does not exist")
        

def add_item(class_name, item):
    uuid = client.data_object.create(class_name=class_name, data_object=item)
   
    
def add_batch_items(class_name, batch_items):
    client.batch.configure(batch_size=100)  # Configure batch
    with client.batch as batch:
        for item in batch_items:
            batch.add_data_object(
                data_object=item,
                class_name=class_name,
            )


# New delete_items function for class with field tokenization for path
def delete_items(className, path, dry_run=False):
    client.batch.consistency_level = weaviate.data.replication.ConsistencyLevel.ALL  # default QUORUM
    try:
        conditions = {"path": ["path"], "operator": "Equal", "valueString": path}
        
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


'''
Testing delete with similar paths
'''

def add_test_items(class_name):
    
    data_objects=[
    {
        "path" : "abcd/test_a.pdf",
        "text" : "This is a test file",
        "page_number" : "1",
        "title" : "Test file",
        "url" : "https://www.google.com"
    }, 

    {
        "path" : "abcd/test_b.pdf",
        "text" : "This is a test file",
        "page_number" : "2",
        "title" : "Test file",
        "url" : "https://www.google.com"
        
    },

    {
        "path" : "abcd/abc/test_b.pdf",
        "text" : "This is a test file",
        "page_number" : "3",
        "title" : "Test file",
        "url" : "https://www.google.com"
    }   
    ]
    for item in data_objects:
        add_item(class_name, item)



'''
End of preliminary testing for delete

'''

# search for items in a class using nearest neighbor search
# returns the first property of the first k results concatenated 
def search_items(class_name, properties=[""], text_query="", k=10, path=""):
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueString": path+"*"}
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


# Filters search results by path 
def get_filter_search(properties=["path"], path="", class_name = "File_store_ver2"):
    response = (
    client.query
    .get(class_name=class_name, properties=properties)
    .with_where({
        "path": ["path"],
        "operator": "Equal",
        "valueString": path
    }).do()
    )
    return response["data"]["Get"][class_name]

