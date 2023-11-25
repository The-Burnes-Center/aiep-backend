from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from IEPAssistant import IEPAssistant
from IEPTranslator import IEPTranslator
from time import sleep
from openai import OpenAI
import io, json, os, asyncio, re, fitz

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Ping Frontend to combat heroku's dyno
async def send_ping_message(websocket: WebSocket):
    while True:
        await asyncio.sleep(10)  # Send a ping every 10 seconds
        try:
            await websocket.send_text('ping')
        except:
            break  # Connection is closed or encountered an error

active_connections = set()

def get_translation(client: OpenAI, fileData: io.BytesIO) -> list[str]:
    doc = fitz.open(stream=fileData, filetype='pdf')
    translated_list = []
    for page_number in range(doc.page_count):
        page = doc[page_number]
        text = page.get_text()
        response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "text" },
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to display .txt files in an aesthetically pleasing way."},
            {"role": "user", "content": "Take this string of text and clean it up into an HTML file that is legible. The original document"+
            "includes checkboxes and redacted information. Here is the"+ f"string of text: {text}"}])
        translated_list.append(response.choices[0].message.content)
    return translated_list

def get_l2_prompts(assistant: IEPAssistant) -> list[str]:
    def extract_ordered_list(text) -> list[str]:
        matches = re.findall(r'^[1-5]\..*$', text, re.MULTILINE)
        if len(matches) != 5: raise Exception("Couldn't find 5 prompts")
        return matches
    print('Got Response')
    msg = "What are five questions to ask ChatGPT specifically about my child's IEP? Provide questions that would give concise, easily understandable answers that are most pressing to the topic. Respond in English with each question on a new line." # input('Enter Question: ')
    assistant.add_message(msg)
    assistant.run()
    while not assistant.has_finished():
        print('Retrieving Data...')
        sleep(4)
    response = assistant.get_latest_message()
    return extract_ordered_list(response)

def get_l3_prompts(client:OpenAI, assistant: IEPAssistant) -> object:
    msg = "Summarize 5 of the most pressing issues in the child's IEP in no more than 200 words. Give a block of text and nothing more."
    assistant.add_message(msg)
    assistant.run()
    while not assistant.has_finished():
        print('Retrieving Data...')
        sleep(4)
    res = assistant.get_latest_message()
    questions = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": "You are given a summary of a child's performance from an IEP. You give the most pressing questions whose answers can be found in the summary." + "Return the 5 of the most pressing questions in JSON Format with each assigned by priority to 'question 1', 'question 2' etc respectively."},
        {"role": "user", "content": 'Summary: ' + res}
    ])
    return questions.choices[0].message.content

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    asyncio.create_task(send_ping_message(websocket))

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
                    print("Configuring IEP")
                    assistant.config_iep(iep_data)
                    print('File Data Configured for chatbot')
                    questions = get_l2_prompts(assistant)
                    print('Prompts Calculated')
                    await websocket.send_text(json.dumps({"type": "response", "message": '\n'.join(questions)}))
                    print("Prompts Sent Over")
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
                        translated_list = get_translation(client,io.BytesIO(file_data))
                        print('Translation Generated')
                        for page_num, translated_page in enumerate(translated_list):
                            await websocket.send_text(json.dumps({"type": "translation", "message": str(page_num + 1) + '/n' + translated_page}))
                        print('Response Sent')
                    elif text_type == 'language':
                        print("Language Request Received")
                        language = text_data["data"]
                        print("Language Configured")
            except WebSocketDisconnect:
                active_connections.remove(websocket)
                print("Client disconnected")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

