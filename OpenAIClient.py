import WeaviateClient
import openai

class_name = "File_store"


def get_answer(query: str, path: str):
    context = WeaviateClient.search_items(class_name=class_name, properties=[
        "text"], text_query=query, k=5, path=path)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + str(context)},
                  {"role": "user", "content": "This is my question: " + query}],
        max_tokens=2000,
        temperature=0.3,
    )
    return response.choices[0].message.content


def get_answer_stream(question: str, path: str):
    context = WeaviateClient.search_items(class_name=class_name, properties=[
        "text"], text_query=question, k=5, path=path)
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + str(context)},
                  {"role": "user", "content": "This is my question: " + question}],
        max_tokens=2500,
        temperature=0.3,
        stream=True,
    )
    for part in response:
        print(part)
        # check if part['choices'][0]['delta'] has 'content' key
        if part.choices[0].delta.content is not None:
            yield part.choices[0].delta.content

