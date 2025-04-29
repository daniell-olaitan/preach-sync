import os
import asyncio
import webrtcvad

from typing import Any
from abc import ABC, abstractmethod
from starlette.websockets import WebSocketState
from deepgram import (
    LiveOptions,
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents
)


class VADAudioBuffer:
    def __init__(self, aggressiveness=3, sample_rate=16000, frame_duration=30):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_size = int(sample_rate * frame_duration / 1000 * 2)  # bytes

    async def split_audio(self, in_queue: asyncio.Queue, out_queue: asyncio.Queue):
        triggered = False
        temp_buffer = bytearray()

        while True:
            pcm_chunk = await in_queue.get()

            if pcm_chunk is None:
                break

            chunks = [
                pcm_chunk[i:i+self.frame_size]
                for i in range(0, len(pcm_chunk), self.frame_size)
            ]

            for chunk in chunks:
                if len(chunk) < self.frame_size:
                    break  # Ignore incomplete frames

                is_speech = self.vad.is_speech(chunk, self.sample_rate)

                if is_speech:
                    temp_buffer.extend(chunk)
                    triggered = True
                else:
                    if triggered:
                        # After speech, silence detected -> end of speech segment
                        await out_queue.put(bytes(temp_buffer))


class TranscriberConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """Convert audio bytes into transcribed text"""
        raise NotImplementedError('Method must be implemented')

    @abstractmethod
    def stop(self) -> None:
        """End the connection to the transcriber"""
        raise NotImplementedError('Method must be implemented')


# class DeepgramTranscriber:
#     def __init__(
#         self,
#         model=os.getenv('DEEPGRAM_MODEL', 'nova-3')
#     ):
#         self._track = 0
#         self._sentence = ''
#         self._client = DeepgramClient(
#             os.getenv('DEEPGRAM_API_KEY'),
#             DeepgramClientOptions(
#                 options={"keepalive": "true"}
#             )
#         )

#         self._dg_connection = self._client.listen.asyncwebsocket.v("1")
#         self._options = LiveOptions(
#             model=model,
#             punctuate=True,
#             language="en",
#             encoding="linear16",
#             sample_rate=16000,
#             channels=1,
#         )

#     async def start(self, queue: Any):
#         async def on_message(self, result, **kwargs):
#             sentence = result.channel.alternatives[0].transcript
#             print(result)
#             if sentence:
#                 await queue.put(sentence)

#         self._dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
#         if not await self._dg_connection.start(self._options):
#             raise TranscriberConnectionError('Unable to establish Deepgram connection')

#     async def transcribe(self, audio_chunk: bytes):
#         await self._dg_connection.send(audio_chunk)

#     async def stop(self):
#         await self._dg_connection.finish()


import json
import websockets


class DeepgramTranscriber:
    def __init__(
        self,
        model=os.getenv('DEEPGRAM_MODEL', 'nova-3')
    ):
        self._track = 0
        self._sentence = ''
        self._model = model
        self._api_key = os.getenv('DEEPGRAM_API_KEY')
        self._url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"model={self._model}&punctuate=true&language=en&encoding=linear16&sample_rate=16000&channels=1"
        )
        self._ws = None

    async def start(self, queue: Any):
        try:
            self._ws = await websockets.connect(
                self._url,
                additional_headers={
                    'Authorization': f'Token {self._api_key}'
                }
            )
        except Exception as e:
            raise TranscriberConnectionError(f'Unable to establish Deepgram connection: {e}')

        async def receiver():
            line_number = 0
            async for msg in self._ws:
                data = json.loads(msg)
                if 'channel' in data:
                    sentence = data['channel']['alternatives'][0]['transcript']

                    if sentence:
                        await queue.put(sentence)

                        is_final = data['is_final']
                        start = data['start']
                        end = start + data['duration']
                        line_number += 1
                        print(f'{line_number:>3} {start:<3.3f}-{end:<3.3f} ["is_final": {str(is_final).lower():<5}] {sentence}')

        # Start the receiver task
        asyncio.create_task(receiver())

    async def transcribe(self, audio_chunk: bytes):
        if self._ws is None:
            raise TranscriberConnectionError('WebSocket connection not established. Call start() first.')
        await self._ws.send(audio_chunk)

    async def stop(self):
        """Gracefully close the stream."""
        if self._ws:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
                await self._ws.close()
            except Exception as e:
                print(f"Error while closing connection: {e}")


# from google.cloud import speech

# class GoogleTranscriber(Transcriber):
#     def __init__(self):
#         self.client = speech.SpeechClient()
#         self.config = speech.RecognitionConfig(
#             encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#             sample_rate_hertz=16000,
#             language_code="en-US"
#         )

#     def transcribe(self, audio_bytes: bytes) -> str:
#         audio = speech.RecognitionAudio(content=audio_bytes)
#         response = self.client.recognize(config=self.config, audio=audio)
#         result_text = " ".join([res.alternatives[0].transcript for res in response.results])
#         return result_text


import json
import asyncio
from vosk import Model, KaldiRecognizer


class VoskTranscriber:
    def __init__(self, model_path="model-small", sample_rate=16000):
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)

    async def transcribe(self, audio_data):
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            print(result.get("text", ""))
            # else:
            #     partial = json.loads(self.recognizer.PartialResult())
            #     partial_text = partial.get("partial", "")
            #     if partial_text:
            #         # print(partial.get("partial", ""))
            #         await self.text_queue.put(partial_text)


import time
import numpy as np

from faster_whisper import WhisperModel

class FastWhisperTranscriber:
    def __init__(self, model_size='tiny', device="cpu", sample_rate=16000):
        self.sample_rate = sample_rate
        self.model = WhisperModel(model_size, local_files_only=False, device=device, compute_type='int8')

    def transcribe(self, pcm_data):
        start_time = time.perf_counter()
        if not pcm_data:
            print(time.perf_counter() - start_time)
            return ""


        audio_np = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0
        segments, _ = self.model.transcribe(
            audio_np,
            language="en",
            vad_filter=False,
            without_timestamps=True,
        )

        text = " ".join([segment.text for segment in segments])
        print(text)
        print(time.perf_counter() - start_time)
        return text.strip()
