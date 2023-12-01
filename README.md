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
request msg: {type: "language", data: str}
```
After sending the above message, the backend will configure the chatbot and translation functionalities to use the provided string as the target language

### Uploading a File:
```
request: file binary data // ws.send(event.target.result)*;
response msg: {"type": "file_id", "message": str}
response msg: {"type": "prompts", "message": list[str]}
```
After sending file binary byte data to the backend server,the server will generate top 5 l2/l3 prompts using the configured OpenAI Assistants object.

*The read-only target property of the Event interface is a reference to the object onto which the event was dispatched. It is different from Event.currentTarget when the event handler is called during the bubbling or capturing phase of the event.

### Requesting Translation
```
request msg: { type: "translation" }
response msg: {"type": "translation", "page": int, "message": str}
```

### Sending a Message to the Chatbot
```
request msg: {type: "message", data: str }
response msg: {type: "response", message: str }
```
After sending a message to the chatbot, the backend server will return a generated message using the configured OpenAI Assistants object with the uploaded file attached. This is an asynchonous action
