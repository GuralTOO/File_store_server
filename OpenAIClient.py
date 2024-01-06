import WeaviateClient
import openai

class_name = "File_store_ver2"

def get_answer_stream(question: str, path: str):
    context = WeaviateClient.search_items(class_name=class_name, properties=[
        "text"], text_query=question, k=5, path=path, all_props=True)
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant that answers questions based on excerpts from the following documents:" + context},
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

