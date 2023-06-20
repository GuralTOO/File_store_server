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

dotenv.load_dotenv()
client = weaviate.Client(
    url="http://localhost:8080",
    # url="http://206.189.199.72:8080/",  # Replace with your endpoint
    additional_headers={
        "X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"],
    }
)

classes = client.schema.get().get("classes")
print(classes)

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
    print("adding item...", item)
    client.data_object.create(class_name=class_name, data_object=item)


# def load_text(class_name, text, url):
#     try:
#         # split text into into chunks of 1000 characters
#         text_chunks = [text[i:i + 1000] for i in range(0, len(text), 1000)]
#         print("loading page: "+url+"...")
#         for chunk in text_chunks:
#             add_item(class_name=class_name, item={
#                      "page_text": chunk, "url": url})
#     except:
#         print("Error loading page")


def load_pdf(class_name, properties=None):
    print(properties)
    try:
        url = properties["url"]
        print("loading pdf: " + url + "...")
        # load file from a given url
        response = requests.get(url)
        print(response)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.content)
        with open(tmp_file.name, "rb") as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            print("file loaded")
            num_pages = len(pdf_reader.pages)
            pages_text = []
            pageCounter = 0
            print("file has " + str(num_pages) + " pages")
            for page in range(num_pages):
                print("reading page: " + str(pageCounter + 1) + "...")
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

                print("page " + str(pageCounter + 1) + ": " + page_text)

                # split text into into chunks of 1000 characters when the word ends
                text_chunks = utils.get_chunks(page_text)

                for chunk in text_chunks:
                    modified_properties = properties
                    modified_properties["page_number"] = str(pageCounter)
                    modified_properties["text"] = chunk
                    add_item(class_name=class_name, item=modified_properties)

                pageCounter += 1

        return "Success"
    except Exception as e:
        print("Error loading pdf:", e)
        return "Failure"


def delete_items(class_name, properties=[]):
    try:
        conditions = [{'path': [key], 'operator': 'Equal',
                       'valueText': value} for key, value in properties]
        client.batch.delete_objects(
            class_name=class_name,
            where=conditions,
        )
        return "Success"
    except:
        print("Error deleting items")
        return "Failure"


# search for items in a class using nearest neighbor search
def search_items(class_name, properties=[""], text_query="", k=10):
    results = client.query.get(class_name=class_name, properties=properties).with_near_text(
        {"concepts": text_query}).with_limit(k).do()
    return results["data"]["Get"][class_name]

# return all items in a class


def get_all_items(class_name, properties=[""]):
    results = client.query.get(
        class_name=class_name, properties=properties).do()
    return results["data"]["Get"][class_name]


# add_class(class_name="file_store", description="vectorized files",
#           variables=["type", "path", "url", "text", "page_number"])

print(get_class_names())
