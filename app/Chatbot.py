from fastapi import WebSocket
from app.GPTTools import create_client, GPTRole, GPTChatCompletion, GPTAssistant
from time import sleep
from typing import List
import io, json, re, fitz

TRANSLATION_PROMPT = 'Must return the answer in'
CHAR_LIMIT = 1500
CHAR_LIMIT_MESSAGE = f'Limit your response to {CHAR_LIMIT} characters.'
SF_HANDBOOK_FILE_ID = 'file-gj95bmlJ6MLyVuSpmLTuKqk7'
L2_PROMPT_MSG = "What are five questions to ask ChatGPT specifically about my child's IEP? Provide questions that would give concise, easily understandable answers that are most pressing to the topic. Respond with each question on a new line."
L3_PROMPT_MSG_ASST = "Summarize 5 of the most pressing issues in the child's IEP in no more than 200 words. Give a block of text and nothing more."
L3_PROMPT_MS_SYS = "You are given a summary of a child's performance from an IEP. You give the most pressing questions about the IEP whose answers cannot be found in the summary in JSON Format labelled by 'question 1', 'question 2' etc respectively."
TRANSLATION_PROMPT_SYS = "You are a helpful assistant designed to display .txt files in an aesthetically pleasing way."
TRANSLATION_PROMPT_USR = "Take this string of text and clean it up into an HTML file that is legible. The original document includes checkboxes and redacted information. Only output HTML code."
CHATBOT_ASST_INSTRUCTIONS_ATT = "IEP Chatbot that answers parents' questions regarding their child's Individualized Education Plan (Document Attached) according to San Francisco's Educational Rules and Guidelines (Handbook Attached)." + CHAR_LIMIT_MESSAGE
CHATBOT_ASST_INSTRUCTIONS_EMPTY = "IEP Chatbot that answers parents' questions regarding their child's Individualized Education Plan and Process specific to San Francisco's Educational Rules and Guidelines (Handbook Attached)." + \
    CHAR_LIMIT_MESSAGE
DEFAULT_PROMPTS = ["Can you summarize the first page of my IEP document?",
                   "What are the key components of an IEP?",
                   "How do I know if my child is eligible for an IEP?",
                   "What should I expect during an IEP meeting?",
                   "How can I prepare for my child's IEP meeting?",
                   "What are my child's legal rights concerning IEPs?",
                   "How often will my child's IEP be reviewed?",
                   "Who will be involved in creating my child's IEP?",
                   "Can you explain the different sections of an IEP?",
                   "What if I disagree with the IEP recommendations?",
                   "How do I track my child's progress on IEP goals?",
                   "What services are available to my child with an IEP?",
                   "How can I modify my child's IEP if necessary?",
                   "Who do I contact if I have concerns about my child's IEP?",
                   "Can family members attend the IEP meeting?",
                   "What are SMART goals in an IEP, and why are they important?"]


class Chatbot:
    def __init__(self, api_key=str) -> None:
        self.client = create_client(api_key)
        self.assistant = GPTAssistant(self.client)
        self.language_config = None
        self.assistant.add_file(SF_HANDBOOK_FILE_ID)
        
    def _validate_language_config(self):
        if not self.language_config:
            raise Exception('Chatbot Language Not Configured')
    
    def _validate_assistant_build_status(self):
        if not self.assistant.language:
            self.assistant.build(CHATBOT_ASST_INSTRUCTIONS_EMPTY)

    def _generate_l2_prompts(self):
        def extract_ordered_list(text) -> List[str]:
            matches = re.findall(r'^[1-5]\. (.*)$', text, re.MULTILINE)
            if len(matches) != 5:
                raise Exception("Couldn't find 5 prompts")
            return matches
        self._validate_assistant_build_status()
        self.assistant.add_message(L2_PROMPT_MSG)
        self.assistant.run()
        while not self.assistant.has_finished():
            print('Retrieving Data...')
            sleep(4)
        response = self.assistant.get_latest_message()
        return extract_ordered_list(response)

    def _generate_l3_prompts(self):
        self._validate_assistant_build_status()
        self.assistant.add_message(L3_PROMPT_MSG_ASST)
        self.assistant.run()
        while not self.assistant.has_finished():
            print('Retrieving Data...')
            sleep(4)
        res = self.assistant.get_latest_message()
        chat_completion = GPTChatCompletion(
            self.client, self.language_config, True)
        chat_completion.add_message(GPTRole.SYSTEM, L3_PROMPT_MS_SYS)
        chat_completion.add_message(GPTRole.USER, 'Summary: ' + res)
        return chat_completion.get_completion()

    async def configure_language(self, ws: WebSocket, language_config: str):
        self.language_config = language_config
        self.assistant.config_language(language_config)
        print('Language Configured')
        await ws.send_text(json.dumps({"type": "language_configuration", "status": "complete"}))

    async def _generate_translation(self, ws: WebSocket, file_data: io.BytesIO):
        def extract_html(input_string: str) -> str:
            print(input_string)
            match = re.search(r"```html(.*?)```", input_string, re.DOTALL)
            return match.group(1) if match else input_string
        print('Translation Request Received')
        doc = fitz.open(stream=file_data, filetype='pdf')
        for page_number in range(doc.page_count):
            print(f'Translating Page {page_number + 1}')
            page = doc[page_number]
            text = page.get_text()
            print('Text Retreived')
            chat_completion = GPTChatCompletion(self.client, self.language_config, False)
            chat_completion.add_message(GPTRole.SYSTEM, TRANSLATION_PROMPT_SYS + '. Please Translate into Spanish.')
            chat_completion.add_message(GPTRole.USER, f"{TRANSLATION_PROMPT_USR} Here is the string of text: {text}")
            translated_text_response = chat_completion.get_completion()
            translated_text_html = extract_html(translated_text_response)
            print('Response Received')
            await ws.send_text(json.dumps({"type": "file_translation", "page_number": page_number + 1, "content": translated_text_html}))
        print('Translation Sent')

    async def add_file(self, ws: WebSocket, file_id: str):
        self._validate_language_config()
        self.assistant.add_file(file_id)
        print("Configuring IEP")
        await ws.send_text(json.dumps({"type": "file_id", "value": file_id}))
        self.assistant.build(CHATBOT_ASST_INSTRUCTIONS_ATT)
        print('File Data Configured for chatbot')
        image_data_bytes = self.client.files.retrieve_content(file_id)
        await self._generate_translation(ws, io.BytesIO(image_data_bytes))

    async def upload_file(self, ws: WebSocket, file_data: io.BytesIO):
        print('Uploading File')
        self._validate_language_config()
        iep_id = self.assistant.upload_file(file_data)
        self.assistant.add_file(iep_id)
        print("Configuring IEP")
        await ws.send_text(json.dumps({"type": "file_id", "value": iep_id}))
        self.assistant.build(CHATBOT_ASST_INSTRUCTIONS_ATT)
        await self.generate_prompts(ws)
        print('File Data Configured for chatbot')
        await self._generate_translation(ws, file_data)

    async def generate_prompts(self, ws: WebSocket):
        self._validate_language_config()
        questions = self._generate_l2_prompts(
        ) if self.assistant.hasBuilt else DEFAULT_PROMPTS
        print('Prompts Calculated')
        await ws.send_text(json.dumps({"type": "generated_prompts", "content": questions}))
        print(questions)
        print("Prompts Sent Over")

    async def generate_response(self, ws: WebSocket, message: str):
        self._validate_language_config()
        if not self.assistant.hasBuilt:
            self.assistant.build(CHATBOT_ASST_INSTRUCTIONS_EMPTY)
        self.assistant.add_message(message)
        print('Message Data Configured')
        self.assistant.run()
        print('Running Assistant...')
        while not self.assistant.has_finished():
            print('Retrieving Data...')
            sleep(3)
        response = self.assistant.get_latest_message()
        print('Got Response')
        await ws.send_text(json.dumps({"type": "chat_completion", "content": response}))
        print('Response Sent')
