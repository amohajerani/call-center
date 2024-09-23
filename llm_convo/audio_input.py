import io
import os
import tempfile
import queue
import functools
import logging

from pydub import AudioSegment
import speech_recognition as sr
import whisper


@functools.cache
def get_whisper_model(size: str = "large"):
    logging.info(f"Loading whisper {size}")
    return whisper.load_model(size)


class WhisperMicrophone:
    def __init__(self):
        self.audio_model = get_whisper_model()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 500
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = False

    def get_transcription(self) -> str:
        with sr.Microphone(sample_rate=16000) as source:
            logging.info("Waiting for mic...")
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = os.path.join(tmp, "mic.wav")
                audio = self.recognizer.listen(source)
                data = io.BytesIO(audio.get_wav_data())
                audio_clip = AudioSegment.from_file(data)
                audio_clip.export(tmp_path, format="wav")
                result = self.audio_model.transcribe(tmp_path, language="english")
            predicted_text = result["text"]
        return predicted_text


class _TwilioSource(sr.AudioSource):
    def __init__(self, stream):
        self.stream = stream
        self.CHUNK = 1024
        self.SAMPLE_RATE = 8000
        self.SAMPLE_WIDTH = 2

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class _QueueStream:
    def __init__(self):
        self.q = queue.Queue(maxsize=-1)

    def read(self) -> bytes:
        return self.q.get()

    def write(self, chunk: bytes):
        self.q.put(chunk)


class WhisperTwilioStream:
    def __init__(self):
        self.audio_model = get_whisper_model()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 2.5
        self.recognizer.dynamic_energy_threshold = False
        self.stream = None

    def get_transcription(self) -> str:
        self.stream = _QueueStream()
        with _TwilioSource(self.stream) as source:
            logging.info("Waiting for twilio caller...")
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = os.path.join(tmp, "mic.wav")
                audio = self.recognizer.listen(source)
                data = io.BytesIO(audio.get_wav_data())
                audio_clip = AudioSegment.from_file(data)
                audio_clip.export(tmp_path, format="wav")
                result = self.audio_model.transcribe(tmp_path, language="english")
        predicted_text = result["text"]
        self.stream = None
        return predicted_text


import time
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

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

    def get_transcription(self) -> str:
        self.stream = _QueueStream()
        print("self.dg_connection.is_connected: ", self.dg_connection.is_connected())
        if not self.dg_connection.is_connected():
            print("restablish connection")
            self.dg_connection.start(self.options)
        while True:
            audio_chunk = self.stream.read()
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
