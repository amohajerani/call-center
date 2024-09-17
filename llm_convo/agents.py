from typing import List, Optional
from abc import ABC, abstractmethod

from llm_convo.audio_input import WhisperMicrophone
from llm_convo.audio_output import TTSClient, GoogleTTS
from llm_convo.twilio_io import TwilioCallSession
import requests


class ChatAgent(ABC):
    @abstractmethod
    def get_response(self, transcript: List[str]) -> str:
        pass

    def start(self):
        pass


class MicrophoneInSpeakerTTSOut(ChatAgent):
    def __init__(self, tts: Optional[TTSClient] = None):
        self.mic = WhisperMicrophone()
        self.speaker = tts or GoogleTTS()

    def get_response(self, transcript: List[str]) -> str:
        if len(transcript) > 0:
            self.speaker.play_text(transcript[-1])
        return self.mic.get_transcription()


class TerminalInPrintOut(ChatAgent):
    def get_response(self, transcript: List[str]) -> str:
        if len(transcript) > 0:
            print(transcript[-1])
        return input(" response > ")


class AIAgent(ChatAgent):
    def __init__(
        self,
        system_message: str,
        init_phrase: Optional[str] = None,
    ):
        self.init_phrase = init_phrase
        self.url = "http://probable-instantly-crab.ngrok-free.app/run_agent"
        self.system_message = system_message

    def get_response(self, transcript: List[str]) -> str:
        if len(transcript) > 0:
            try:
                res = requests.post(
                    self.url,
                    json={
                        "system_message": self.system_message,
                        "transcript": transcript,
                    },
                )
                response = res.json()["result"]
            except Exception as e:
                print(f"An error occurred while making the request: {str(e)}")
                response = "I'm sorry, but there is a technical issue."
        else:
            response = self.init_phrase
        return response


class TwilioCaller(ChatAgent):
    def __init__(
        self,
        session: TwilioCallSession,
        tts: Optional[TTSClient] = None,
        thinking_phrase: str = "OK",
    ):
        self.session = session
        self.speaker = tts or GoogleTTS()
        self.thinking_phrase = thinking_phrase

    def _say(self, text: str):
        key, tts_fn = self.session.get_audio_fn_and_key(text)
        self.speaker.text_to_mp3(text, output_fn=tts_fn)
        duration = self.speaker.get_duration(tts_fn)
        self.session.play(key, duration)
        # uncomment the line below to use Twilio's TTS (high latency)
        # self.session.say(text)

    def get_response(self, transcript: List[str]) -> str:
        if not self.session.media_stream_connected():
            raise CallEndedException("The call has ended.")
        if len(transcript) > 0:
            self._say(transcript[-1])
        resp = self.session.sst_stream.get_transcription()
        # self._say(self.thinking_phrase)
        return resp


class CallEndedException(Exception):
    """Exception raised when the call has ended."""

    pass
