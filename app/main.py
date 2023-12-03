from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.Chatbot import Chatbot
from starlette.websockets import WebSocketState
import io
import json
import os
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Ping Frontend to combat heroku's dyno
    async def send_ping_message():
        while True:
            await asyncio.sleep(10)  # Send a ping every 10 seconds
            try:
                await websocket.send_text(json.dumps({"type": "ping"}))
            except:
                break
    await websocket.accept()
    asyncio.create_task(send_ping_message())
    print('Websocket Accepted')
    api_key = os.getenv("OPENAI_KEY")
    chatbot = Chatbot(api_key)
    try:
        while True:
            try:
                websocket_message = await websocket.receive()
                if "bytes" in websocket_message:
                    print('Byte Data Received')
                    file_data = io.BytesIO(websocket_message["bytes"])
                    await chatbot.upload_file(websocket, file_data)
                    file_data.close()  # Close the stream after using it
                elif "text" in websocket_message:
                    message_data = json.loads(websocket_message["text"])
                    print(message_data)
                    message_type = message_data["type"]
                    if message_type == 'pong':
                        print("Pong Received")
                    elif message_type == 'file_retreival':
                        await chatbot.add_file(websocket, message_data["file_id"])
                    elif message_type == 'language_configuration':
                        print("Language Configuration Request Received")
                        await chatbot.configure_language(websocket, message_data["language"])
                    elif message_type == 'chat_completion':
                        await chatbot.generate_response(websocket, message_data["content"])
                    else:
                        raise Exception('Invalid Text Message')
            except Exception as e:
                print(f"Error: {e}")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        error_message = str(e)
        try:
            # Attempt to send an error message only if the websocket is still open
            if websocket.application_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps({'type': 'error', 'message': error_message}))
        except Exception as send_exception:
            print(f"Error sending message: {send_exception}")
    finally:
        print("WebSocket endpoint closed")
        # Perform any cleanup if necessary
