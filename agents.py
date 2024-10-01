from typing import List, Optional
from abc import ABC, abstractmethod

from twilio_io import TwilioCallSession
import requests
import time


class ChatAgent(ABC):
    @abstractmethod
    def get_response(self, transcript: List[str]) -> str:
        pass

    def start(self):
        pass


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
        self.url = "http://localhost:5001/run_agent"  # "http://probable-instantly-crab.ngrok-free.app/run_agent"
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
        thinking_phrase: str = "OK",
    ):
        self.session = session
        self.thinking_phrase = thinking_phrase

    def _say(self, text: str):
        self.session.stream_elevenlabs(text)

    def get_response(self, transcript: List[str]) -> str:
        if not self.session.media_stream_connected():
            raise CallEndedException("The call has ended.")
        if len(transcript) > 0:
            self._say(transcript[-1])
            print("the say is completed")
        resp = self.session.sst_stream.get_transcription()
        # self._say(self.thinking_phrase)
        return resp


class CallEndedException(Exception):
    """Exception raised when the call has ended."""

    pass
