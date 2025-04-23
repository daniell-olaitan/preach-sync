from pipeline.transcriber import Transcriber

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.websocket("/ws/audio")
async def audio_stream(websocket: WebSocket):
    transcriber = Transcriber()
    await websocket.accept()
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            text = transcriber.transcribe(audio_data)

            # matches = detector.detect_references(text)
            # formatted_refs = [format_reference(m) for m in matches]

            # for ref in formatted_refs:
            #     await websocket.send_text(f"Detected: {ref}")
    except WebSocketDisconnect:
        websocket.send_text('Client Disconnected')