# API Message Models
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
### Uploading a File:
```
file binary data // ws.send(event.target.result)*;
```
*The read-only target property of the Event interface is a reference to the object onto which the event was dispatched. It is different from Event.currentTarget when the event handler is called during the bubbling or capturing phase of the event.
### Configuring Chatbot and Translation Language
```
request msg: {type: "language", data: str}
```
### Sending a Message to the Chatbot
```
request msg: {type: "message", data: str }
response msg: {type: "response", message: str }
```
After sending a message to the chatbot, the backend server will return a generated message using the configured OpenAI Assistants object with the uploaded file attached. This is an asynchonous action
