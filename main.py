from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from IEPAssistant import IEPAssistant
from IEPTranslator import IEPTranslator
from time import sleep
from openai import OpenAI
import io, json, os

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
    await websocket.accept()
    print('Websocket Accepted')
    api_key = os.getenv("OPENAI_KEY")
    client = OpenAI(api_key=api_key)
    assistant = IEPAssistant(client)
    translator = IEPTranslator(client, api_key)
    file_data, language = None, None
    try:
        while True:
            try:
                websocket_data = await websocket.receive()
                if "bytes" in websocket_data:
                    file_data = websocket_data["bytes"]
                    print('File Data Parsed')
                    iep_data = io.BufferedReader(io.BytesIO(file_data))
                    assistant.config_iep(iep_data)
                    print('File Data Configured for chatbot')
                elif "text" in websocket_data:
                    text_data = json.loads(websocket_data["text"])
                    text_type = text_data["type"]
                    if text_type == "message":
                        print(text_data)
                        message = text_data["data"]
                        print('Message Data Parsed')
                        assistant.add_message(message)
                        print('Message Data Configured')
                        if assistant.assistant_id:
                            assistant.run()
                            print('Running Assistant...')
                            while not assistant.has_finished():
                                print('Retrieving Data...')
                                sleep(3)
                            response = assistant.get_latest_message()
                            print('Got Response')
                            await websocket.send_text(json.dumps({"type": "response", "message": response}))
                            print('Response Sent')
                    elif text_type == 'translation':
                        print('Translation Request Received')
                        if not file_data: raise Exception('Need to Upload File First')
                        translator.add_iep(io.BytesIO(file_data))
                        print("Added IEP to Translator")
                        total_page_num = translator.get_total_page_num()
                        print("Running Translator...")
                        for page_num in range(total_page_num):
                            print(f"Translating Page {page_num + 1}/{total_page_num}")
                            translated_page = translator.get_page_translation(page_num, language)
                            print("Page Translation Complete")
                            await websocket.send_text(json.dumps({"type": "translation", "message": translated_page}))
                            print('Response Sent')
                        print('All Translations Complete, Generating Summary...')
                        summary = translator.get_summary(language)
                        print('Summary Generated')
                        await websocket.send_text(json.dumps({"type": "summary", "message": summary}))
                        print('Response Sent')
                    elif text_type == 'language':
                        print("Language Request Received")
                        language = text_data["data"]
                        print("Language Configured")
            except WebSocketDisconnect:
                print("Client disconnected")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

