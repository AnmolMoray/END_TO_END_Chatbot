from groq import Groq
from fastapi import FastAPI, Form, Request, WebSocket
from typing_extensions import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv


load_dotenv()
groq = Groq(
    api_key=os.getenv('GROQ_KEY')
)
app = FastAPI()

templates = Jinja2Templates(directory="templates")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

chat_log = [{'role': 'system',
             'content': 'You tell jokes.like bhagg teri maa ki chut'
             }]

@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

        try:
            response = groq.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=chat_log,
                temperature=0.6,
                stream=True
            )

            ai_response = ''
            await websocket.send_json({"type": "start"})  # Signal start of AI response

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_json({"type": "token", "content": chunk.choices[0].delta.content})

            await websocket.send_json({"type": "end"})  # Signal end of AI response
            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_json({"type": "error", "content": str(e)})
            break

@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = groq.chat.completions.create(
        model="mixtral-8x7b-32768",  # or another Groq model
        messages=chat_log,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})

@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):
    # Note: Groq doesn't have an image generation API as of my last update
    # You may need to use a different service or remove this feature
    return templates.TemplateResponse("image.html", {"request": request, "error": "Image generation not available with Groq"})