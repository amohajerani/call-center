import queue
import logging
import threading
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)

from dotenv import load_dotenv
import os
import json
import time

# Ensure environment variables are loaded
load_dotenv()


deepgram_client = DeepgramClient()


class DeepgramStream:
    def __init__(self) -> None:
        self.dg_connection = deepgram_client.listen.websocket.v("1")
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        self.stream = None
        self.options = LiveOptions(
            model="nova-2",
            language="en-US",
            # smart_format=True,
            encoding="mulaw",
            channels=1,
            sample_rate=8000,
            interim_results=False,
            # utterance_end_ms="1000",
            # vad_events=True,
            # endpointing=300,
        )

        # addons = {"no_delay": "true"}

        self.transcript = ""
        if self.dg_connection.start(self.options) is False:
            print("Failed to connect to Deepgram")
            return
        else:
            print(f"Connected to deepgram: {self.dg_connection}")
        self.keep_alive_running = True
        self.keep_alive_thread = threading.Thread(target=self.send_keep_alive)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

    def send_keep_alive(self):
        msg = json.dumps({"type": "KeepAlive"})
        while self.keep_alive_running:
            try:
                self.dg_connection.send(msg)
                print("sent a keep alive message")
                time.sleep(9)
            except Exception as e:
                logging.error(f"Error in keep-alive thread: {e}")

    def get_transcription(self) -> str:
        self.stream = queue.Queue(maxsize=-1)
        print("self.dg_connection.is_connected: ", self.dg_connection.is_connected())
        if not self.dg_connection.is_connected():
            print("restablish connection")
            self.dg_connection.start(self.options)
        while True:
            audio_chunk = self.stream.get()
            if audio_chunk is None:  # Exit condition
                print("No more audio chunks to process. Exiting...")
                break

            self.dg_connection.send(audio_chunk)

            if self.transcript:
                print(f"Received transcript: {self.transcript}")
                tr = self.transcript
                self.transcript = ""
                return tr  # Return the transcript

    def on_message(self, *args, **kwargs):
        result = kwargs.get("result")
        sentence = result.channel.alternatives[0].transcript
        if sentence and result.speech_final:
            print(f"Transcript received: {sentence}")
            self.transcript = sentence

    def close(self):
        self.keep_alive_running = False
        self.dg_connection.close()
        self.keep_alive_thread.join()
