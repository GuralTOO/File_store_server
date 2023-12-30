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
# print(classes)

# region class utilities


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

# endregion


def add_item(class_name, item):
    uuid = client.data_object.create(class_name=class_name, data_object=item)
    print("adding item...", item, uuid)




import concurrent.futures

def load_pdf(class_name, properties=None):
    print(properties)
    start_time = time.time() 
    try:
        url = properties["url"]
        print("loading pdf: " + url + "...")
        # load file from a given url
        response = requests.get(url)
        print(response)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.content)

        # enable batching
        client.batch.configure(batch_size=100)

        with open(tmp_file.name, "rb") as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            print("file loaded")
            num_pages = len(pdf_reader.pages)
            pages_text = []
            pageCounter = 0
            print("file has " + str(num_pages) + " pages")

            def process_page(page):
                print("reading page: " + str(page + 1) + "...")
                local_path = os.path.abspath(tmp_file.name)
                images = convert_from_path(
                    local_path, first_page=page + 1, last_page=page + 1)
                # if there are images in the page, use OCR to extract text
                if images:
                    page_image = images[0]
                    page_text = pytesseract.image_to_string(page_image)
                    pages_text.append(page_text)
                # if there are no images in the page, use PyPDF2 to extract text
                else:
                    page_obj = pdf_reader.getPage(page)
                    page_text = page_obj.extractText()
                    pages_text.append(page_text)

                print("page " + str(page + 1) + ": " + page_text)

                # split text into into chunks of 1000 characters when the word ends
                text_chunks = utils.get_chunks(page_text)

                for chunk in text_chunks:
                    modified_properties = properties.copy()
                    modified_properties["page_number"] = str(page)
                    modified_properties["text"] = chunk

                    add_item(class_name=class_name, item=modified_properties)

                    # add to batches
                    # client.batch.add_data_object(
                    #     data_object=modified_properties, class_name=class_name)
                    

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(process_page, range(num_pages))

            pageCounter += num_pages
            
        # end timer
        end_time = time.time()
        print("time elapsed: " + str(end_time - start_time))
        return "Success"
    except Exception as e:
        print("Error loading pdf:", e)
        return "Failure"



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
    # print("search results: ", results)
    # concatenate all text from the results in ["data"]["Get"][class_name][i][properties[0]]
    search_result = {}
    for i in range(len(results["data"]["Get"][class_name])):
        if search_result.get(results["data"]["Get"][class_name][i][properties[1]]) is None:
            search_result[results["data"]["Get"][class_name][i][properties[1]]] = [[results["data"]["Get"][class_name][i][properties[0]] + ".", results["data"]["Get"][class_name][i][properties[2]]]]
        else:
            search_result[results["data"]["Get"][class_name][i][properties[1]]].append([results["data"]["Get"][class_name][i][properties[0]] + ".", results["data"]["Get"][class_name][i][properties[2]]])
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

# load_pdf(class_name="file_store", properties={
#             "type": "research", "path": "test", "url": "https://emoimoycgytvcixzgjiy.supabase.co/storage/v1/object/sign/documents/044dd9f2-929d-4bc6-b5b9-a18869c4d8ae/Self-Supervised%20Poisson-Gaussian%20Denoising.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJkb2N1bWVudHMvMDQ0ZGQ5ZjItOTI5ZC00YmM2LWI1YjktYTE4ODY5YzRkOGFlL1NlbGYtU3VwZXJ2aXNlZCBQb2lzc29uLUdhdXNzaWFuIERlbm9pc2luZy5wZGYiLCJpYXQiOjE3MDIyNTY0OTgsImV4cCI6MTcwMjg2MTI5OH0.kdneimFyliV8aZQl80Z6XGTyS0hMOXbLzIhlaS_edv0&t=2023-12-11T01%3A01%3A39.654Z"})
# delete_items(className="File_store", path = "test")