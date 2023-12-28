import openai
import os
from upload import get_context_for_authors
import WeaviateClient


openai.api_key = os.getenv("OPENAI_API_KEY")
class_name = "File_store"



def getGivenPageFileContextFromFilePath(path, page_number="0"):
    properties = ["text", "path", "page_number"]
    pathFilter = {"path": "path", "operator": "Equal", "valueText": path}
    page_filter = {"path": "page_number",
                   "operator": "Equal", "valueText": page_number}
    client = WeaviateClient.get_client()
    # text_query = "A list of authors of this research paper"
    # text_query = "Return the names of the authors of the paper"
    # text_query = "Can you return the names of the authors of the paper?"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where({
            "operator": "And",
            "operands": [pathFilter, page_filter]
        })
        .with_limit(1)
        .do()
    )

    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    return search_result

def getFileTitleFromPath(path):
    question = "Extract the paper's title based on the context below. Do not make any assumptions."
    context = getGivenPageFileContextFromFilePath(path)
    response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Question: \"\"\"{question}\"\"\"\nContext: \"\"\"{context}\"\"\"\n",
            max_tokens=3000,
            temperature=0.2, # reduced the temperature
        )
    return response.choices[0].text

# print(getFileTitleFromPath("539e9941-5673-4561-8f7b-ddb523a4b537/Test/Papers/Papers/Gamper_Multiple_Instance_Captioning_Learning_Representations_From_Histopathology_Textbooks_and_Articles_CVPR_2021_paper.pdf"))