import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

import os
from dotenv import load_dotenv

load_dotenv('dev.env')

# Initializing my Azure Search Client
endpoint = "https://medical-rag-search-2026.search.windows.net"
key = os.getenv("AS")
index_name = "med-docs-index"
credential = AzureKeyCredential(key)
search_client = SearchClient(endpoint, index_name, credential)

df = pd.read_parquet("part.0.parquet")
df["passage"] = df["passage"].fillna("")

documents = []
for id, row in df.iterrows():
    # Convert every single row into a JSON-compatible dictionary matching index schema
    doc = {
        "id": str(id),
        "description": row["passage"]
    }
    documents.append(doc)

# Upload in chunks
batch_size = 1000
for i in range(0, len(documents), batch_size):
    chunk = documents[i:i + batch_size]
    try:
        results = search_client.upload_documents(documents=chunk)
        print(f"Successfully uploaded batch: {i} to {i + len(chunk)}")
    except Exception as e:
        print(f"Failed to upload batch: {e}")
