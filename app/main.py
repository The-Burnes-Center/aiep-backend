from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.GPTTools import GPTRole, GPTChatCompletion, GPTAssistant
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
            await websocket.send_text(json.dumps({"type": "ping"}))
        except:
            break  # Connection is closed or encountered an error

def extract_html(input_string: str) -> str:
    print(input_string)
    match = re.search(r"```html(.*?)```", input_string, re.DOTALL)
    if match:
        print('MATCH')
        # Extract and return the text between triple single quotes
        extracted_text = match.group(1)
        return extracted_text
    else:
        print('NOPE')
        return input_string

def get_l2_prompts(assistant: GPTAssistant) -> list[str]:
    def extract_ordered_list(text) -> list[str]:
        matches = re.findall(r'^[1-5]\..*$', text, re.MULTILINE)
        if len(matches) != 5: raise Exception("Couldn't find 5 prompts")
        return matches
    print('Got Response')
    msg = "What are five questions to ask ChatGPT specifically about my child's IEP? Provide questions that would give concise, easily understandable answers that are most pressing to the topic. Respond in English with each question on a new line."
    assistant.add_message(msg)
    assistant.run()
    while not assistant.has_finished():
        print('Retrieving Data...')
        sleep(4)
    response = assistant.get_latest_message()
    return extract_ordered_list(response)

def get_l3_prompts(client:OpenAI, assistant: GPTAssistant, language: str) -> object:
    msg = "Summarize 5 of the most pressing issues in the child's IEP in no more than 200 words. Give a block of text and nothing more."
    assistant.add_message(msg)
    assistant.run()
    while not assistant.has_finished():
        print('Retrieving Data...')
        sleep(4)
    res = assistant.get_latest_message()
    chat_completion = GPTChatCompletion(client, True, language)
    chat_completion.add_message(GPTRole.SYSTEM, "You are given a summary of a child's performance from an IEP. You give the most pressing questions about the IEP whose answers cannot be found in the summary in JSON Format labelled by 'question 1', 'question 2' etc respectively.")
    chat_completion.add_message(GPTRole.USER, 'Summary: ' + res)
    return chat_completion.get_completion()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    asyncio.create_task(send_ping_message(websocket))
    print('Websocket Accepted')
    api_key = os.getenv("OPENAI_KEY")
    client = OpenAI(api_key=api_key)
    assistant = GPTAssistant(client)
    file_data, language = None, None
    try:
        while True:
            try:
                websocket_data = await websocket.receive()
                if "bytes" in websocket_data:
                    if not language: raise Exception('Please Configure Language First')
                    file_data = websocket_data["bytes"]
                    print('File Data Parsed')
                    iep_data = io.BufferedReader(io.BytesIO(file_data))
                    iep_id = assistant.upload_file(iep_data)
                    assistant.add_file(iep_id)
                    print("Configuring IEP")
                    await websocket.send_text(json.dumps({"type": "file_id", "message": iep_id}))
                    assistant.build()
                    print('File Data Configured for chatbot')
                    questions = get_l2_prompts(assistant)
                    print('Prompts Calculated')
                    await websocket.send_text(json.dumps({"type": "prompts", "message": ['haha', 'baba']}))
                    print(questions)
                    print("Prompts Sent Over")
                elif "text" in websocket_data:
                    text_data = json.loads(websocket_data["text"])
                    text_type = text_data["type"]
                    if text_type == 'pong':
                        print("Pong Received")
                    elif text_type == 'language':
                        print("Language Request Received")
                        language = text_data["data"]
                        print("Language Configured")
                    else:
                        #if not assistant.assistant_id: raise Exception('Assistant Not Configured Yet')
                        if text_type == "message":
                            print(text_data)
                            message = text_data["data"]
                            print('Message Data Parsed')
                            assistant.add_message(message)
                            print('Message Data Configured')
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
                            doc = fitz.open(stream=io.BytesIO(file_data), filetype='pdf')
                            for page_number in range(doc.page_count):
                                print(f'Translating Page {page_number + 1}')
                                page = doc[page_number]
                                text = page.get_text()
                                print('Text Retreived')
                                chat_completion = GPTChatCompletion(client, False, language)
                                chat_completion.add_message(GPTRole.SYSTEM, "You are a helpful assistant designed to display .txt files in an aesthetically pleasing way.")
                                chat_completion.add_message(GPTRole.USER, "Take this string of text and clean it up into an HTML file that is legible. The original document includes checkboxes and redacted information. Here is the"+ f"string of text: {text}")
                                translated_text = chat_completion.get_completion()
                                translated_text_inner_html = extract_html(translated_text)
                                #print(translated_text_inner_html)
                                print('Response Received')
                                await websocket.send_text(json.dumps({"type": "translation", "page": page_number + 1, "message": translated_text_inner_html}))
                            print('Translation Sent')
            except WebSocketDisconnect:
                print("Client disconnected")
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

