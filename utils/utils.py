def get_chunks(text):
    text_chunks = []
    temp_string = ""
    for word in text.split():
        temp_string += word + " "
        if(len(temp_string) > 1000):
            text_chunks.append(temp_string)
            temp_string = ""

    if(len(temp_string) > 0):
        text_chunks.append(temp_string)
        temp_string = ""
    return text_chunks
