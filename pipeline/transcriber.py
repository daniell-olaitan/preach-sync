import os
import asyncio
import json
import websockets

from typing import Any
from signals import shutdown_event


class TranscriberConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DeepgramTranscriber:
    def __init__(
        self,
        sample_rate,
        model=os.getenv('DEEPGRAM_MODEL', 'nova-3')
    ):
        self._track = 0
        self._sentence = ''
        self._model = model
        self._api_key = os.getenv('DEEPGRAM_API_KEY')
        self._url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"model={self._model}&punctuate=true&language=en&encoding=linear16&sample_rate={sample_rate}&channels=1"
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
            try:
                async for msg in self._ws:
                    data = json.loads(msg)
                    if data['is_final']:
                        transcript = data['channel']['alternatives'][0]['transcript']

                        if transcript:
                            await queue.put(transcript)

                            ## For test
                            start = data['start']
                            end = start + data['duration']
                            print(f'{start:<3.3f}-{end:<3.3f}: {transcript}')
            except Exception as e:
                print("Receiver crashed:", e)
            finally:
                shutdown_event.set()
                await queue.put(None)
                await self.stop()

        # Start the receiver task
        asyncio.create_task(receiver())

    async def transcribe(self, queue: Any):
        if self._ws is None:
            raise TranscriberConnectionError('WebSocket connection not established. Call start() first.')

        try:
            while True:
                chunk = await queue.get()
                if chunk is None:
                    await self.stop()

                    break

                await self._ws.send(chunk)
        except Exception as err:
            print('Error in sending', err)
            await self.stop()
            shutdown_event.set()

    async def stop(self):
        """Gracefully close the stream."""
        if self._ws:
            try:
                await self._ws.send(json.dumps({"type": "CloseStream"}))
                await self._ws.close()
            except Exception as e:
                print(f"Error while closing connection: {e}")
