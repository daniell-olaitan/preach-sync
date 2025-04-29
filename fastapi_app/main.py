import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__),'..', '.env')
load_dotenv(dotenv_path=dotenv_path)

from pipeline.transcriber import DeepgramTranscriber
from pipeline.fetcher import BibleFetcher
from pipeline.detector import DetectorAI

import asyncio
from typing import Dict
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, Request

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

templates = Jinja2Templates(directory="frontend/templates")

sessions: Dict[str, Dict[str, WebSocket]] = {}


# @app.get("/", response_class=HTMLResponse)
# async def get_index(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="index.html"
#     )
from signals import shutdown_event

@app.get('/test')
async def test_app():
    import wave

    def read_pcm_data_from_wav(path):
        with wave.open(path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            raw_data = wf.readframes(wf.getnframes())  # raw PCM data

        return raw_data, channels, sample_width, sample_rate

    REALTIME_RESOLUTION = 0.100
    audio_data, channels, sample_width, sample_rate = read_pcm_data_from_wav('audio_sample.wav')
    byte_rate = sample_width * sample_rate * channels

    transcriber = DeepgramTranscriber(sample_rate=sample_rate)
    fetcher = BibleFetcher()
    detector = DetectorAI(
        model=os.getenv('MISTRAL_MODEL'),
        api_key=os.getenv('MISTRAL_API_KEY')
    )

    text_queue = asyncio.Queue()
    audio_queue = asyncio.Queue()

    async def run_detection():
        try:
            while True:
                transcript = await text_queue.get()
                if transcript is None:
                    break

                content = await detector.detect_verse(transcript)
                scripture = fetcher.fetch_verse(**content)

                print('scripture:', scripture)
        except Exception as e:
            print("run_detection crashed:", e)
        finally:
            shutdown_event.set()

    await transcriber.start(text_queue)
    asyncio.create_task(run_detection())
    asyncio.create_task(transcriber.transcribe(audio_queue))

    try:
        while len(audio_data) and not shutdown_event.is_set():
            i = int(byte_rate * REALTIME_RESOLUTION)
            chunk, audio_data = audio_data[:i], audio_data[i:]

            await audio_queue.put(chunk)

            # Sleep for that amount of time to simulate real-time
            await asyncio.sleep(REALTIME_RESOLUTION)

        await audio_queue.put(None)
        await transcriber.stop()
        print('End of transcription')

    except Exception as err:
        print('Websocket error')
        raise

    return {'status': 'ok'}


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


@app.websocket("/ws/text/{session_id}")
async def text_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    sessions[session_id] = {"text": websocket}
