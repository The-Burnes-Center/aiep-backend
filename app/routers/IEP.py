import base64, requests, os
from openai import OpenAI
from PIL import Image
from pathlib import Path
from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse

API_KEY ='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'
client = OpenAI(api_key=API_KEY)

router = APIRouter()

def image_to_text(image_path):
  def encode_image(image_path):
      with open(image_path, "rb") as image_file:
          return base64.b64encode(image_file.read()).decode('utf-8')
  base64_image = encode_image(image_path)
  headers = {"Content-Type": "application/json",
             "Authorization": f"Bearer {API_KEY}"}
  payload = {"model": "gpt-4-vision-preview",
             "messages": [{"role": "user","content": [
                {"type": "text",
                 "text": "This is a page from a student's (possibly redacted) Individualized Education Plan. Try to provide a text transcription of the image while preserving its structure and logic but excluding any redacted information. Use the 'the student' equivalent in the translation to refer to the student."},
                {"type": "image_url",
                 "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"}}]}],
              "max_tokens": 300}
  response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
  return response.json().get('choices')[0].get('message').get('content')

def translate_text(text: str, language: str='Spanish'):
    return chatgpt_response('Please Translate the following text to '+ language +' without loss of information:', text)

def summarize_text(text: str, language: str='Spanish'):
    return chatgpt_response('Please Summarize the Following IEP Breakdown in ' + language, text)

def chatgpt_response(prompt:str, text: str) -> str:
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": prompt},
        {"role": "user", "content": text}])
    return response.choices[0].message.content

def translate_summarize(pdf_path: str, image_folder:str, image_format:str='jpeg'):
    # Open the PDF file
    pdf = fitz.open(pdf_path)
    translated_pages = []
    full_translation = ''
    if not os.path.exists(image_folder):
        # If it does not exist, create it
        os.makedirs(image_folder)
    # Iterate over each page
    for page_num in range(len(pdf)):
        # Get the page
        page = pdf[page_num]
        # Render page to an image
        pix = page.get_pixmap()
        # Define the output image path
        image_path = f"{image_folder}/page_{page_num + 1}.{image_format}"
        # Save the image
        pix.save(image_path)
        text = image_to_text(image_path)
        translated_text = translate_text(text,'Simplified Chinese')
        translated_pages.append(translated_text)
        full_translation += f"Page {page_num + 1}:\n" + translated_text
    # Close the PDF after processing
    summarized_text = summarize_text(text, 'Simplified Chinese')
    pdf.close()
    return translated_pages, summarized_text

@router.post("/upload/")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        file_location = f"{'iep.pdf'}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        translated_pages, summarized_text = translate_summarize('iep.pdf', './pages')
        return JSONResponse(content={"pageData": translated_pages, 'summary': summarized_text}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=500)