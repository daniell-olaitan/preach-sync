import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__),'..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from pipeline.transcriber import DeepgramTranscriber, VoskTranscriber, FastWhisperTranscriber

from pipeline.transcriber import VADAudioBuffer

import asyncio
from typing import Dict
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")

sessions: Dict[str, Dict[str, WebSocket]] = {}

audio_buffer = VADAudioBuffer()

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.websocket("/ws/audio/{session_id}")
async def audio_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()
    transcriber = DeepgramTranscriber()
    text_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    BYTES_PER_SECOND = 16000 * 2

    while True:
        if session_id in sessions:
            sessions[session_id]["audio"] = websocket
            break

    await transcriber.start(text_queue)

    # text_ws = sessions[session_id].get("text")

    # _data = bytearray()

    try:
        while True:
            audio_data = await websocket.receive_bytes()
            # _data.extend(audio_data)
            await audio_queue.put(audio_data)
            audio_chunk = await audio_queue.get()

            await transcriber.transcribe(audio_chunk)

            # Calculate how much "real time" this chunk represents
            real_time_duration = len(audio_chunk) / BYTES_PER_SECOND

            # Sleep for that amount of time to simulate real-time
            await asyncio.sleep(real_time_duration)

            # matches = detector.detect_references(text)
            # formatted_refs = [format_reference(m) for m in matches]

            # for ref in formatted_refs:
            #     await websocket.send_text(f"Detected: {ref}")
    except:
        # asyncio.create_task(websocket.send_text('Client Disconnected'))
        await transcriber.stop()
        sessions.pop(session_id, None)

#     except Exception:
#         print('He;')
#         import wave

#         with wave.open(f'record.wav', 'wb') as wf:
#             wf.setnchannels(1)       # mono
#             wf.setsampwidth(2)       # 16-bit PCM = 2 bytes
#             wf.setframerate(16000)   # match frontend sample rate
#             wf.writeframes(_data)

# transcriber = VoskTranscriber()


# @app.websocket("/ws/audio/{session_id}")
# async def audio_stream(websocket: WebSocket, session_id: str):
#     await websocket.accept()

#     input_chunks = asyncio.Queue(maxsize=100)
#     audio_chunks = asyncio.Queue(maxsize=100)

#     # asyncio.create_task(audio_buffer.split_audio(input_chunks, audio_chunks))

#     while True:
#         if session_id in sessions:
#             sessions[session_id]["audio"] = websocket
#             break

#     try:
#         while True:
#             audio_data = await websocket.receive_bytes()
#             await input_chunks.put(audio_data)
#             audio_chunk = await audio_chunks.get()
#             transcript = await transcriber.transcribe(audio_data)
#     except WebSocketDisconnect:
#         print(f"Audio socket disconnected")

# transcriber = FastWhisperTranscriber()

# async def receiver(websocket, input_chunks):
#     buffer = bytearray()
#     try:
#         while True:
#             audio_data = await websocket.receive_bytes()
#             buffer.extend(audio_data)
#             if len(buffer) > 16000 * 2:  # 16k samples/sec * 2 bytes/sample
#                 pcm_chunk = bytes(buffer[:32000])  # First ~1 sec
#                 buffer = buffer[32000:]
#                 # print("Received audio chunk")
#                 await input_chunks.put(pcm_chunk)
#     except Exception as e:
#         print(f"Receiver error: {e}")

# async def processor(input_chunks, transcriber):
#     while True:
#         audio_chunk = await input_chunks.get()
#         # print("Processing audio chunk...")
#         try:
#             transcript = await asyncio.to_thread(transcriber.transcribe, audio_chunk)
#             # print("Transcript:", transcript)
#         except Exception as e:
#             print(f"Processing error: {e}")
#         finally:
#             input_chunks.task_done()

# @app.websocket("/ws/audio/{session_id}")
# async def audio_stream(websocket: WebSocket, session_id: str):
#     await websocket.accept()
#     while True:
#         if session_id in sessions:
#             sessions[session_id]["audio"] = websocket
#             break

#     input_chunks = asyncio.Queue()

#     receiver_task = asyncio.create_task(receiver(websocket, input_chunks))
#     processor_task = asyncio.create_task(processor(input_chunks, transcriber))

#     done, pending = await asyncio.wait(
#         [receiver_task, processor_task],
#         return_when=asyncio.FIRST_COMPLETED,
#     )

#     for task in pending:
#         task.cancel()


# @app.websocket("/ws/audio/{session_id}")
# async def audio_stream(websocket: WebSocket, session_id: str):
#     await websocket.accept()
#     while True:
#         if session_id in sessions:
#             sessions[session_id]["audio"] = websocket
#             break

#     # input_chunks = asyncio.Queue(maxsize=100)
#     audio_chunks = asyncio.Queue()

#     # asyncio.create_task(audio_buffer.split_audio(input_chunks, audio_chunks))
#     buffer = bytearray()
#     try:
#         while True:
#             audio_data = await websocket.receive_bytes()
#             buffer.extend(audio_data)
#             if len(buffer) > 16000 * 2:  # 16k samples/sec * 2 bytes/sample
#                 pcm_chunk = bytes(buffer[:32000])  # First ~1 sec
#                 buffer = buffer[32000:]
#                 await audio_chunks.put(audio_data)
#             # audio_chunk = await audio_chunks.get()

#     except WebSocketDisconnect:
#         print(f"Audio socket disconnected")


@app.websocket("/ws/text/{session_id}")
async def text_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    sessions[session_id] = {"text": websocket}
