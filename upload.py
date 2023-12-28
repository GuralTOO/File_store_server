from dotenv import load_dotenv
import openai
import WeaviateClient
import os
import SupabaseClient
class_name = "File_store"
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_context_for_authors(properties=[""], k=3, path=""):
    properties.append("path")
    properties.append("page_number")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path}
    page_filter = {"path": "page_number",
                   "operator": "Equal", "valueText": "0"}
    client = WeaviateClient.get_client()
    # text_query = "A list of authors of this research paper"
    # text_query = "Return the names of the authors of the paper"
    text_query = "Can you return the names of the authors of the paper?"
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

    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    return search_result


def get_context_for_methods(properties=[""], k=3, path=""):
 
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    client = WeaviateClient.get_client()
    # text_query = "The section of a research paper that describes the methods used to conduct the research"
    # text_query = "Return the methods, contributions, implementation details, methodology of the paper"
    text_query = "Can you provide the research methods, significant contributions, practical applications, and detailed methodology described in the paper?"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where(pathFilter)
        .with_near_text({"concepts": text_query})
        .with_limit(k)
        .do()
    )

    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"

    return search_result


def get_context_for_key_results(properties=[""], k=3, path=""):
    print("path in results: ", path)
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Equal", "valueText": path}
    client = WeaviateClient.get_client()
    # text_query = "The section of a research paper that describes the key results and outcomes of the research"
    # text_query = "Return the results, discussion, outcomes, evaluation of the paper"
    # text_query = "Can you return the results, discussion, and outcomes of the paper?"
    text_query = "Can you provide the main results, discussion, outcomes, and findings described in the paper?"
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where(pathFilter)
        .with_near_text({"concepts": text_query})
        .with_limit(k)
        .do()
    )
    print("path after filter: ", path)
    print()
    search_result = ""
    for i in range(len(results["data"]["Get"][class_name])):
        search_result += results["data"]["Get"][class_name][i][properties[0]] + ".\n"
        for p in properties:
            print(results["data"]["Get"][class_name][i][p] + ".\n")

    return search_result


def analyze_research(path=""):

    '''
    questions = ["Based on the following excerpts from this research paper, return the list of the authors of this research paper",
                 "Based on the following excerpts from this research paper, return the list of the research methods used in this research paper.",
                 "Based on the following excerpts from this research paper, return the list of the key results presented in this research paper."]
    '''
    questions = [
                 "Extract the paper's title based on the context below. Do not make any assumptions.",
                 "Extract the authors of the paper based on the context below. Do not make any assumptions.",
                 "Extract the main methods described in the context below. Do not make any assumptions.",
                 "Extract the key results described in the context below. Do not make any assumptions."] # "extract" works better than "return a list of"

    context_author = get_context_for_authors(properties=["text"], k=3, path=path)
    context_method = get_context_for_methods(properties=["text"], k=3, path=path)
    context_result = get_context_for_key_results(properties=["text"], k=3, path=path)
    contexts = [context_author, context_author, context_method, context_result]
    
    
    print("CONTEXT (Authors as well as Title): ", contexts[0])
    print("CONTEXT (Methods): ", contexts[2])
    print("CONTEXT (Results): ", contexts[3])

    OPENA_AI_MODEL = "gpt-3.5-turbo-instruct"

    for i in range(len(questions)):
        question = questions[i]
        context = contexts[i]
        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Question: \"\"\"{question}\"\"\"\nContext: \"\"\"{context}\"\"\"\n",
            max_tokens=3000,
            temperature=0.2, # reduced the temperature
        )
        if i == 0:
            title = response.choices[0].text
        elif i == 1:
            authors = response.choices[0].text
        elif i == 2:
            methods = response.choices[0].text
        elif i == 3:
            key_results = response.choices[0].text

    # make a json object with the following properties: authors, methods, key_results
    # return the json object
    return {"title" : title, "authors": authors, "methods": methods, "key_results": key_results}


def upload_file(document_type, path, url, contentType="research"):
    # Load the file to Weaviate
    result = WeaviateClient.load_pdf(class_name=class_name, properties={
                                     "type": document_type, "path": path, "url": url})


    contentType = "research"
    print("uploaded file with path: ", path, " and content type: ", contentType)
    # if contentType is not "research" then we don't need to extract the authors, methods, and key results
    if contentType != "research":
        return

    analysis = analyze_research(path=path)
    print("analysis: ", analysis)
    
    # instead of returning the metadata, save it directly to the db
    SupabaseClient.update_metadata_in_database(path=path, metadata=analysis)
    print("updated metadata in database for path: ", path)
        
    return


# create functions to test the context retrieving functions
# testing_path = "c75767dd-172c-463c-aafc-1e2dfddc1b32/yolo/1706.03762.pdf"
# testing_path = "c75767dd-172c-463c-aafc-1e2dfddc1b32/yolo/SSRN-id4453685.pdf"
# get_context_for_authors(properties=["text"], k=3, path=testing_path)
# get_context_for_methods(properties=["text"], k=3, path="")
# get_context_for_key_results(properties=["text"], k=3, path="")
# print(analyze_research(testing_path))
# print(analyze_research(path=testing_path))
# testing_path_1 = "c75767dd-172c-463c-aafc-1e2dfddc1b32/t1/1/3/short_1706.03762.pdf"

# testing_path = "539e9941-5673-4561-8f7b-ddb523a4b537/Test/test_a.pdf" # context is empty for some papers (test_c.pdf)- why?
testing_path = "c75767dd-172c-463c-aafc-1e2dfddc1b32/Entrepclass/testing_1/inside_testing_1/short_1706.03762.pdf"
# test_a.pdf returns the answers of test_d.pdf?
# testing_path = "84077a0c-0b0f-43f5-96a5-5c517d1c6d13/Folder X/YOLO.pdf" 

# print(analyze_research(path=testing_path))

def print_weaviate(properties=[""], path="",k=5):
    # print everything that matches this
    properties.append("path")
    pathFilter = {"path": "path", "operator": "Like", "valueText": path+"*"}
    client = WeaviateClient.get_client()
    results = (
        client.query
        .get(class_name=class_name, properties=properties)
        .with_where(pathFilter)
        .with_limit(k)
        .do()
    )

    search_result = ""
    # print("CLIENT in Upload.py", client)
    # print("results :::", results)
    for i in range(len(results["data"]["Get"][class_name])):
        for p in properties: 
            search_result += results["data"]["Get"][class_name][i][p] + ".\n"

    return search_result


#print(print_weaviate(properties=["text"], path=testing_path))
# print(print_weaviate(properties=["text"], path="test"))
print(analyze_research("test"))
