import json
import logging
import re
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Foundry Agent and Project Settings
PROJECT_ENDPOINT = "https://med-rag.services.ai.azure.com/api/projects/med-rag-openai"
AGENT_NAME = "med-rag-assistant"
AGENT_VERSION = "5"

# Initialize singletons for client and credential
credential = DefaultAzureCredential()
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential
)
openai_client = project_client.get_openai_client()


@app.route(route="chat", methods=["POST"])
def chat_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing incoming Agentic chat request.")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json"
        )

    chat_history = req_body.get("chat_history")
    
    if not chat_history or not isinstance(chat_history, list):
        return func.HttpResponse(
            body=json.dumps({"error": "Missing or invalid 'chat_history' array"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        # 1. Format input messages for the response API
        formatted_input = [
            {
                "type": "message",
                "role": msg.get("role"),
                "content": msg.get("content"),
            }
            for msg in chat_history
            if msg.get("role") in ["system", "user", "assistant"]
            and isinstance(msg.get("content"), str)
            and msg.get("content", "").strip()
        ]

        # 2. Invoke the Agent via the Responses API
        response = openai_client.responses.create(
            input=formatted_input,
            extra_body={
                "agent_reference": {
                    "name": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "type": "agent_reference",
                }
            },
        )

        # 3. Extract and parse retrieved MCP knowledge documents
        retrieved_docs = []
        if hasattr(response, "output"):
            for item in response.output:
                raw_text = None
                
                # Check potential output attributes for tool step details
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

        # 4. Construct JSON payload
        result_payload = {
            "response": response.output_text,
            "retrieved_contexts": retrieved_docs
        }

        return func.HttpResponse(
            body=json.dumps(result_payload),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error executing agent request: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to process request", "details": str(e)}),
            status_code=500,
            mimetype="application/json"
        )