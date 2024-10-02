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
        init_phrase: Optional[str] = None,
        phone_number='',
    ):
        self.init_phrase = init_phrase
        self.url = "http://localhost:5001/run_agent"  # "http://probable-instantly-crab.ngrok-free.app/run_agent"
        self.phone_number=phone_number

    def get_response(self, transcript: List[str]) -> str:
        if len(transcript) > 0:
            try:
                res = requests.post(
                    self.url,
                    json={
                        "transcript": transcript,
                        "phone_number":self.phone_number
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
    ):
        self.session = session

    def get_response(self, transcript: List[str]) -> str:
        if not self.session.media_stream_connected():
            raise CallEndedException("The call has ended.")
        if len(transcript) > 0:
            self.session.stream_elevenlabs(transcript[-1])
        resp = self.session.sst_stream.get_transcription()
        # the thinking phrase can be added here.
        return resp


class CallEndedException(Exception):
    """Exception raised when the call has ended."""

    pass
