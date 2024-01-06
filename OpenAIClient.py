import WeaviateClient
import openai

class_name = "File_store_ver2"


def get_answer_stream(question: str, path: str):
    print("path in stream: ", path)
    context = WeaviateClient.search_items(class_name=class_name, properties=[], text_query=question, k=5, path=path, all_props=True)
    
    new_context = ""
    index = 0
    for obj in context:
        index += 1
        new_context += "For excerpt number " + str(index) + ":\n"
        new_context += "Title of the research paper: " + obj["title"] + "\n"
        new_context += "Page number of the excerpt: " + obj["page_number"] + "\n"
        new_context += "The excerpt: " + obj["text"] + "\n"
    

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You will be given several exerpts from research papers in the format 'title, page_number, and text: '" + new_context + "Based on the information, answer the user's question."},
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

