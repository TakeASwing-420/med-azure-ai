import json
import re
from azure.identity import InteractiveBrowserCredential
from azure.ai.projects import AIProjectClient

# 1. Configuration
ENDPOINT = "https://med-rag.services.ai.azure.com/api/projects/med-rag-openai"
AGENT_NAME = "med-rag-assistant"
AGENT_VERSION = "5"
TENANT_ID = "114351e2-dfd8-4893-bc43-7ba1e6c8b781"

# 2. Authenticate
credential = InteractiveBrowserCredential(tenant_id=TENANT_ID)
project_client = AIProjectClient(
    endpoint=ENDPOINT,
    credential=credential,
)
openai_client = project_client.get_openai_client()

# 3. Request
user_query = "Which acetylcholinesterase inhibitors are used for treatment of myasthenia gravis?"
print(f"User: {user_query}\n")
print("Waiting for response...")

response = openai_client.responses.create(
    input=[
        {
            "type": "message",
            "role": "user",
            "content": user_query,
        }
    ],
    extra_body={
        "agent_reference": {
            "name": AGENT_NAME,
            "version": AGENT_VERSION,
            "type": "agent_reference",
        }
    },
)

# 4. Print Generated Response
print("\n" + "=" * 60)
print("AGENT RESPONSE")
print("=" * 60)
print(response.output_text)

# 5. Extract and Format Retrieved Context Texts
print("\n" + "=" * 60)
print("RETRIEVED CONTEXT PASSAGES")
print("=" * 60)

retrieved_docs = []

if hasattr(response, "output"):
    for item in response.output:
        raw_text = None
        
        # Check standard tool/step output attributes
        for attr in ["output", "result", "content", "details"]:
            val = getattr(item, attr, None)
            if val:
                raw_text = str(val)
                break
                
        # Parse MCP citation chunks: 【index†source】 { json_body }
        if raw_text and "†source】" in raw_text:
            chunks = re.split(r"(【\d+:\d+†source】)", raw_text)
            for i in range(1, len(chunks), 2):
                marker = chunks[i].strip()
                payload_str = chunks[i + 1].strip() if i + 1 < len(chunks) else ""
                
                try:
                    # Extract the JSON body for the document
                    json_match = re.search(r"\{.*\}", payload_str, re.DOTALL)
                    if json_match:
                        doc_data = json.loads(json_match.group(0))
                        retrieved_docs.append({
                            "marker": marker,
                            "id": doc_data.get("id", "N/A"),
                            "description": doc_data.get("description", "").strip()
                        })
                except Exception:
                    retrieved_docs.append({
                        "marker": marker,
                        "id": "Unknown",
                        "description": payload_str
                    })

# 6. Display Parsed Contexts
if retrieved_docs:
    print(f"Successfully extracted {len(retrieved_docs)} retrieved knowledge documents:\n")
    for doc in retrieved_docs:
        print(f"--- Document ID: {doc['id']} (Marker: {doc['marker']}) ---")
        print(f"{doc['description']}\n")
else:
    print("No structured context documents found in the response payload.")