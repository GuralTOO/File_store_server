from dotenv import load_dotenv
import openai
import WeaviateClient
import os
class_name = "File_store"
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_context_for_authors(properties=[""], k=3, path=""):
    properties.append("path")
    properties.append("page_number")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    page_filter = {"path": "page_number",
                   "operator": "Equal", "valueText": "0"}
    client = WeaviateClient.get_client()
    text_query = "A list of authors of this research paper"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where({
            "operator": "And",
            "operands": [pathFilter, page_filter]
        })
        .with_near_text({"concepts": text_query})
        .with_limit(k)
        .do()
    )

    # results = (
    #     client.query
    #     .get(class_name=class_name, properties=properties)
    #     .with_where(pathFilter)
    #     .with_near_text({"concepts": text_query})
    #     .with_limit(k)
    #     .do()
    # )

    # print("search results: ", results)
    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    # change this to
    return search_result


def get_context_for_methods(properties=[""], k=3, path=""):
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    client = WeaviateClient.get_client()
    text_query = "The section of a research paper that describes the methods used to conduct the research"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where(pathFilter)
        .with_near_text({"concepts": text_query})
        .with_limit(k)
        .do()
    )
    # print("search results: ", results)
    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    return search_result


def get_context_for_key_results(properties=[""], k=3, path=""):
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    client = WeaviateClient.get_client()
    text_query = "The section of a research paper that describes the key results and outcomes of the research"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where(pathFilter)
        .with_near_text({"concepts": text_query})
        .with_limit(k)
        .do()
    )
    # print("search results: ", results)
    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    return search_result


def analyze_research(path=""):

    questions = ["Based on the following excerpts from this research paper, return the list of the authors of this research paper?",
                 "Based on the following excerpts from this research paper, return the list of the research methods used in this research paper.",
                 "Based on the following excerpts from this research paper, return the list of the key results presented in this research paper."]

    contexts = [get_context_for_authors(properties=["text"], k=3, path=path), get_context_for_methods(
        properties=["text"], k=3, path=path), get_context_for_key_results(properties=["text"], k=3, path=path)]

    OPENA_AI_MODEL = "gpt-3.5-turbo-instruct"

    for i in range(len(questions)):
        question = questions[i]
        context = contexts[i]
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Question: {question}\nContext: {context}\n",
            max_tokens=3000,
            temperature=0.9,
        )
        if i == 0:
            authors = response["choices"][0]["text"]
        elif i == 1:
            methods = response["choices"][0]["text"]
        elif i == 2:
            key_results = response["choices"][0]["text"]
        print(response["choices"][0]["text"])

    # make a json object with the following properties: authors, methods, key_results
    # return the json object
    return {"authors": authors, "methods": methods, "key_results": key_results}


def upload(document_type, path, url, contentType):
    # Load the file to Weaviate
    result = WeaviateClient.load_pdf(class_name=class_name, properties={
                                     "type": document_type, "path": path, "url": url})

    if(contentType != "research"):
        return result

    return analyze_research(path=path)


# create functions to test the context retrieving functions
# testing_path = "c75767dd-172c-463c-aafc-1e2dfddc1b32/yolo/1706.03762.pdf"
testing_path = "c75767dd-172c-463c-aafc-1e2dfddc1b32/yolo/SSRN-id4453685.pdf"
# get_context_for_authors(properties=["text"], k=3, path=testing_path)
# get_context_for_methods(properties=["text"], k=3, path="")
# get_context_for_key_results(properties=["text"], k=3, path="")

print(analyze_research(path=testing_path))
