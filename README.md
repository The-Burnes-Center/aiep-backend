# AI-EP Project Backend
## Quick Setup (Local Testing)
To Run Locally (Ctrl+C to Terminate & Crtl+S to Reload):
```
uvicorn app.main:app --reload
```
Backend WebSocket API can be connected at 
```
ws://localhost:8000/ws
```
## Supported Features
- High Accuracy OCR scanning with Minimum Loss of Information with PyPDF's Fitz Library (previously using ChatGPT's Vision Library)
- Supports Upload and Retrieval of Custom IEP files with unique file id
- Prompt Generation using the OpenAI's Assistant beta feature that uses the San Francisco IEP Guidebook and Uploaded Custom IEP to generate Situation Specific Prompts
- Translation using the Assistant's beta feature and GPT4-preview-1106's chat completion with Azure translation back-up option
- Chatbot messaging using the Assistant's beta feature
- Ping-pong messaging via Websocket Connection to prevent cloud server's scheduler from refreshing the application mid-communication

## Hosting Details
Back end server is host on: https://iep-backend-2422fe6f9d4d.herokuapp.com/

Websocket Endpoint: wss://iep-backend-2422fe6f9d4d.herokuapp.com/ws

## Websocket API Documentation

### Configuring Translation and Chatbot Language
```
Request: 
{type: "language_configuration", "language": str}

Response:
{type: "language_configuration", "status": "complete"}
```
After sending the above message, the backend server will configure the chatbot and translation functionalities to use the provided string as the target language. A response will be returned indicating the status as complete.

### Uploading a File:
```
Request:
file binary data // ws.send(event.target.result)*;
or
{"type": "file_retreival", "file_id": str}

Responses: 
{"type": "file_id", "value": str}
{"type": "generated_prompts", "content": list[str]}
{"type": "file_translation", "page_number": int, "content": str}
...
```
After sending file binary byte data to the backend server,the server will perform the following tasks (in order):

1. Upload the file to the OpenAI API File Storage. A response will be returned containing the file id string.
2. Generate the top 5 l2/l3 prompts based on the uploaded file using the configured OpenAI Assistants object. A response will be returned containing a list of strings representing the prompts.
3. Transcribe & Translate the file page by page using PYPDF's Fitz Library and ChatGPT's Chat Completion (model-3.5-1106). Responses will be returned containing the html string of each translated page in order.

Alternatively, clients can send a request referrencing the file_id of an existing uploaded file. Instead of uploading a file, the backend server will attempt to retreive the file using the file_id. The file is then downloaded for native transcription and translation. Responses are identical. 

*The read-only target property of the Event interface is a reference to the object onto which the event was dispatched. It is different from Event.currentTarget when the event handler is called during the bubbling or capturing phase of the event.

### Sending a Message to the Chatbot
```
Request:
{type: "chat_completion", "content": str}

Response:
{type: "chat_completion", "content": str}
```
After sending a message to the chatbot, the backend server will return a generated message using the configured OpenAI Assistants object with the uploaded file attached. This is an asynchonous action

### Error Handling
```
{"type": "error", "message": str}
```
