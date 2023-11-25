import os
import dotenv
from supabase import create_client, Client
dotenv.load_dotenv()

url: str = os.environ["SUPABASE_URL"]
key: str = os.environ["SUPABASE_SERVICE_KEY"]
supabase: Client = create_client(url, key)

print(supabase)

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
    