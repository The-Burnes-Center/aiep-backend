from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.ConnectionManager import ConnectionManager
import json, os, asyncio

app = FastAPI()
api_key = os.getenv("OPENAI_KEY")
manager = ConnectionManager(api_key)

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
    await manager.connect(websocket)
    asyncio.create_task(send_ping_message())
    print('Websocket Accepted')
    try:
        while True:
            message = await websocket.receive()
            print('Message Received')
            asyncio.ensure_future(manager.handle_messages(message, websocket))
    except Exception as e:
        print(f'Error occured: {str(e)}')
    finally:
        manager.disconnect(websocket)
