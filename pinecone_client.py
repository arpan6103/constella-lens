import os
from pinecone import Pinecone,ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

pc=Pinecone(api_key=os.getenv("PINECONE_API_KEY"));

INDEX_NAME=os.getenv("PINECONE_INDEX","constella-logs")
DIMENSION=384

def init_index():
    existing=[i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws",region="us-east-1")
        )
        print(f"Created index: {INDEX_NAME}")
    else:
        print(f"Index already exists: {INDEX_NAME}")

    return pc.Index(INDEX_NAME)

index=init_index()

def upsert_log(log_id:str,embedding:list[float],metadata:dict):
    index.upsert(vectors=[{
        "id":log_id,
        "values":embedding,
        "metadata":metadata
    }])

def query_logs(embedding:list[float],top_k:int=10)->list[dict]:
    results=index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results["matches"]