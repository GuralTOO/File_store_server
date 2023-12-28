import WeaviateClient
import openai
from HelperFunctions import getFileTitleFromPath

class_name = "File_store"

def get_answer(query: str, path: str):
    contexts = WeaviateClient.search_items(class_name=class_name, properties=[
        "text"], text_query=query, k=5, path=path)
    # response = openai.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + str(context)},
    #               {"role": "user", "content": "This is my question: " + query}],
    #     max_tokens=2000,
    #     temperature=0.3,
    # )
    # return response.choices[0].message.content

    result = ""

    for filePath in contexts.keys():
        fileTitle = getFileTitleFromPath(filePath)
        print("File title :", fileTitle)
        print("File context :", contexts[filePath])
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + str(contexts[filePath])},
                    {"role": "user", "content": "This is my question: " + query}],
            max_tokens=2500,
            temperature=0.3,
            stream=True,
        )

        for part in response:
            # print()
            # check if part['choices'][0]['delta'] has 'content' key
            if part.choices[0].delta.content is not None:
                result += part.choices[0].delta.content
        result += "\n"
    
    return result


def get_answer_stream(question: str, path: str):
    # print("$$$")
    contexts = WeaviateClient.search_items(class_name=class_name, properties=[
        "text"], text_query=question, k=5, path=path)
    # print("CONTEXT ::: ", context)
    for filePath in contexts.keys():
        fileTitle = getFileTitleFromPath(filePath)
        print("File title :", fileTitle)
        print("File context :", contexts[filePath])
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + str(contexts[filePath])},
                    {"role": "user", "content": "This is my question: " + question}],
            max_tokens=2500,
            temperature=0.3,
            stream=True,
        )

        for part in response:
            # print()
            # check if part['choices'][0]['delta'] has 'content' key
            if part.choices[0].delta.content is not None:
                yield part.choices[0].delta.content
        print("\n")
# print("ASDSAD")
# if __name__ == '__main__':
#     get_answer_stream("Give me the list of authors?", "test")
            
# result = get_answer_stream(question="Extract the primary authors of all the papers as shown in the first page of each paper. Do not make any assumptions.", path="test")
# for part in result:
#     print(part, end="")
# print(get_answer(query="Extract the primary authors of all the papers as shown in the first page of each paper. Do not make any assumptions.", path="test"))