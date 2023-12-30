import os
import dotenv
from supabase import create_client, Client
dotenv.load_dotenv()

url: str = os.environ["SUPABASE_URL"]
key: str = os.environ["SUPABASE_SERVICE_KEY"]
supabase: Client = create_client(url, key)


def update_metadata_in_database(path, metadata):
    try:
        response = supabase.table("doc_data") \
            .update({"metadata": metadata}) \
            .eq("path", path) \
            .execute()

        data = response.data if hasattr(response, 'data') else []
        count = len(data)

        if count == 0:
            raise Exception("No rows were updated.")

        return data

    except Exception as e:
        print("Detailed error:", e)
        raise Exception("Error updating row.")
    

def pull_metadata_from_database(path):
    try:
        response = supabase.table("doc_data") \
            .select("metadata") \
            .eq("path", path) \
            .execute()

        data = response.data if hasattr(response, 'data') else []
        count = len(data)
        
        if count == 0:
            raise Exception("No rows were found.")

        return data

    except Exception as e:
        print("Detailed error:", e)
        raise Exception("Error pulling row.")
    
    
def call_edge_function(functionName, params):
    try:
        response = supabase.functions.invoke(
            function_name=functionName, 
            invoke_options=
            {
                "body": params,
            }
        )
        print("response: ", response)
        return response
    except Exception as e:
        print("Detailed error:", e)
        raise Exception("Error calling edge function.")
    
# call_edge_function("load_pdf", 
#                    {"url": "https://emoimoycgytvcixzgjiy.supabase.co/storage/v1/object/sign/documents/c75767dd-172c-463c-aafc-1e2dfddc1b32/Med%20Research/1706.03762.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJkb2N1bWVudHMvYzc1NzY3ZGQtMTcyYy00NjNjLWFhZmMtMWUyZGZkZGMxYjMyL01lZCBSZXNlYXJjaC8xNzA2LjAzNzYyLnBkZiIsImlhdCI6MTcwMzM5MDgxNCwiZXhwIjoxNzAzOTk1NjE0fQ.2-JomgyxVpc9V5qkTQE1KQQeh_YsPkmHgeXTlhRz0N4&t=2023-12-24T04%3A06%3A55.633Z",
#                     "firstPage": 1,
#                     "lastPage": 2,
#                     })


# call_edge_function("load_pdf", {"imageUrl": "https://emoimoycgytvcixzgjiy.supabase.co/storage/v1/object/sign/temp_files/1706.03762_page-0001.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJ0ZW1wX2ZpbGVzLzE3MDYuMDM3NjJfcGFnZS0wMDAxLmpwZyIsImlhdCI6MTcwMzYxMDQzMiwiZXhwIjoxNzA0MjE1MjMyfQ.UGEx0AakQKrqaDSvZdVFBkldLuM365_s7BlSa72PuUQ&t=2023-12-26T17%3A07%3A13.935Z"})