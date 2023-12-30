import boto3
import requests
import time
from pdf2image import convert_from_path
from concurrent.futures import ThreadPoolExecutor
import asyncio
import io

import tracemalloc
tracemalloc.start()
import functools


# Function to process a single page
async def process_page(executor, client, image):
    loop = asyncio.get_event_loop()
    with io.BytesIO() as image_bytes:
        image.save(image_bytes, format='JPEG')
        image_bytes_val = image_bytes.getvalue()

    # Prepare the function call with functools.partial
    func = functools.partial(client.detect_document_text, Document={'Bytes': image_bytes_val})

    # Call Textract using run_in_executor
    response = await loop.run_in_executor(executor, func)
    text = '\n'.join([block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE'])
    # for block in response['Blocks']:
    #     if block['BlockType'] != 'WORD':
    #         print(block['BlockType'])
    #     if block['BlockType'] == 'LINE':
    #         print(block['Text'])
        
    return text

async def load_pdf_with_textract(class_name, properties=None):
    print(properties)
    start_time = time.time()
    url = properties["url"]    

    response = requests.get(url)
    with open('document.pdf', 'wb') as file:
        file.write(response.content)

    # Convert PDF to images
    images = convert_from_path('document.pdf')
    
    time_after_pdf_to_image = time.time()
    print("time elapsed after pdf to image: " + str(time_after_pdf_to_image - start_time))

    # Setup AWS Textract client
    session = boto3.Session()
    client = session.client('textract')

    # Setup thread pool for running I/O tasks in parallel within a context manager
    with ThreadPoolExecutor(max_workers=len(images)) as executor:
        tasks = [process_page(executor, client, image) for image in images]
        results = await asyncio.gather(*tasks)
    
    # Combine text from all pages
    full_text = "\n".join(results)
    
    end_time = time.time()
    print("time elapsed: " + str(end_time - start_time))
    
    return full_text

# import pypdf
# from pdf2image import convert_from_path
# import pytesseract
# import json
# import os
# import requests
# import datetime
# from utils import utils
# import tempfile
# import time
# from WeaviateClient import add_item

# import concurrent.futures

# def load_pdf(class_name, properties=None):
#     print(properties)
#     start_time = time.time() 
#     try:
#         url = properties["url"]
#         print("loading pdf: " + url + "...")
#         # load file from a given url
#         response = requests.get(url)
#         print(response)
#         response.raise_for_status()
#         with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
#             tmp_file.write(response.content)


#         with open(tmp_file.name, "rb") as pdf_file:
#             pdf_reader = pypdf.PdfReader(pdf_file)
#             print("file loaded")
#             num_pages = len(pdf_reader.pages)
#             pages_text = []
#             pageCounter = 0
#             print("file has " + str(num_pages) + " pages")

#             def process_page(page):
#                 print("reading page: " + str(page + 1) + "...")
#                 local_path = os.path.abspath(tmp_file.name)
#                 images = convert_from_path(
#                     local_path, first_page=page + 1, last_page=page + 1)
#                 # if there are images in the page, use OCR to extract text
#                 if images:
#                     page_image = images[0]
#                     page_text = pytesseract.image_to_string(page_image)
#                     page_text = ""
#                     # pages_text.append(page_text)
#                 # if there are no images in the page, use PyPDF2 to extract text
#                 else:
#                     print("no images found in page " + str(page + 1) + "...")
#                     page_obj = pdf_reader.getPage(page)
#                     page_text = page_obj.extractText()
#                     pages_text.append(page_text)

#                 # print("page " + str(page + 1) + ": " + page_text)

#                 # split text into into chunks of 1000 characters when the word ends
#                 text_chunks = utils.get_chunks(page_text)

#                 for chunk in text_chunks:
#                     modified_properties = properties.copy()
#                     modified_properties["page_number"] = str(page)
#                     modified_properties["text"] = chunk

#                     # add_item(class_name=class_name, item=modified_properties)
                    

#             # parallelize the process_page function
#             # with concurrent.futures.ThreadPoolExecutor() as executor:
#             #     executor.map(process_page, range(num_pages))

#             for page in range(num_pages):
#                 process_page(page)
                
#             pageCounter += num_pages
            
#         # end timer
#         end_time = time.time()
#         print("time elapsed: " + str(end_time - start_time))
#         return "Success"
#     except Exception as e:
#         print("Error loading pdf:", e)
#         return "Failure"
async def main():
    url_8page = "https://emoimoycgytvcixzgjiy.supabase.co/storage/v1/object/sign/documents/23c88506-31e5-43c7-911c-d6df61fbbf7b/curve-stablecoin.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJkb2N1bWVudHMvMjNjODg1MDYtMzFlNS00M2M3LTkxMWMtZDZkZjYxZmJiZjdiL2N1cnZlLXN0YWJsZWNvaW4ucGRmIiwiaWF0IjoxNzAzOTA4MzA3LCJleHAiOjE3MDQ1MTMxMDd9.PVXyAmoZqWlrSt2-v5ma6P9oZrFlm-7vqTSytAAkcNo&t=2023-12-30T03%3A51%3A47.332Z"
    url_29page = "https://emoimoycgytvcixzgjiy.supabase.co/storage/v1/object/sign/documents/06ca3fba-93e4-493d-9c22-5c5ddc15d352/G3-2023-404312_Merged_PDF.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJkb2N1bWVudHMvMDZjYTNmYmEtOTNlNC00OTNkLTljMjItNWM1ZGRjMTVkMzUyL0czLTIwMjMtNDA0MzEyX01lcmdlZF9QREYucGRmIiwiaWF0IjoxNzAzOTA4Mjc3LCJleHAiOjE3MDQ1MTMwNzd9.3CJFZeo6s7XchyaWmyD-6rkxU-JqnQPulZfgLOc5KB8&t=2023-12-30T03%3A51%3A17.288Z"
    result = await load_pdf_with_textract("test", {"url": url_29page})
    # print(result)



# Running the main function
if __name__ == "__main__":
    asyncio.run(main())

