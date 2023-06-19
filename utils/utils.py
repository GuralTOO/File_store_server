def get_chunks(text):
    text_chunks = []
    temp_string = ""
    for word in text.split():
        temp_string += word + " "
        if(temp_string.length() > 1000):
            text_chunks.append(temp_string)
            temp_string = ""
        if(temp_string.length() > 0):
            text_chunks.append(temp_string)
            temp_string = ""
    return text_chunks
