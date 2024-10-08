import threading
import logging
import os
import base64
import json
import time
from flask import request
from dotenv import load_dotenv
import os

# Ensure environment variables are loaded
load_dotenv()

from gevent.pywsgi import WSGIServer
from twilio.rest import Client
from flask import Flask, Response
from flask_sock import Sock
import simple_websocket
import os
from audio_input import DeepgramStream
from utils import format_phone_number
from twilio.twiml.voice_response import VoiceResponse

from elevenlabs.client import ElevenLabs

ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY")
print("elevenlabs api key: ", ELEVENLABS_KEY)
elevenLabs_client = ElevenLabs(api_key=ELEVENLABS_KEY)


class TwilioServer:
    def __init__(self, remote_host: str, port: int):
        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        self.remote_host = remote_host
        self.port = port
        self.server_thread = threading.Thread(target=self._start)
        self.on_session = None

        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        self.from_phone = os.environ["TWILIO_PHONE_NUMBER"]
        self.client = Client(account_sid, auth_token)

        @self.app.route("/incoming-voice", methods=["POST"])
        def incoming_voice():
            phone_number = request.form.get("From")
            phone_number = format_phone_number(phone_number)
            print(f"Incoming call from phone number: {phone_number}")
            twiml = VoiceResponse()
            stream_url = f"wss://{request.host}/audiostream_inbound/{phone_number}"
            print(f"Stream URL: {stream_url}")
            twiml.connect().stream(url=stream_url)
            return Response(str(twiml), mimetype="text/xml")

        @self.sock.route("/audiostream_inbound/<phone_number>", websocket=True)
        def on_media_stream_inbound(ws, phone_number):
            session = TwilioCallSession(
                ws,
                self.client,
                remote_host=self.remote_host,
                phone_number=phone_number,
            )
            if self.on_session is not None:
                thread = threading.Thread(
                    target=self.on_session, args=(session, phone_number)
                )
                thread.start()
            session.start_session()

        @self.app.route("/", methods=["GET"])
        def healthcheck():
            return {"status": "ok"}, 200

    def _start(self):
        logging.info("Starting Twilio Server")
        WSGIServer(("0.0.0.0", self.port), self.app).serve_forever()

    def start(self):
        self.server_thread.start()


class TwilioCallSession:
    def __init__(self, ws, client: Client, remote_host: str, phone_number=None):
        self.ws = ws
        self.client = client
        self.sst_stream = DeepgramStream()
        self.remote_host = remote_host
        self._call = None
        self.phone_number = phone_number
        self.stream_sid = None
        self.is_streaming = True

    def media_stream_connected(self):
        return self._call is not None

    def _read_ws(self):
        try:
            while True:
                try:
                    message = self.ws.receive()
                except simple_websocket.ws.ConnectionClosed:
                    logging.warn("Call media stream connection lost.")
                    break
                if message is None:
                    logging.warn("Call media stream closed.")
                    break

                data = json.loads(message)
                if data["event"] == "start":
                    logging.info("Call connected, " + str(data["start"]))
                    self._call = self.client.calls(data["start"]["callSid"])
                    self.stream_sid = data["start"][
                        "streamSid"
                    ]  # Fix: Assign streamSid correctly

                elif data["event"] == "media":
                    media = data["media"]
                    chunk = base64.b64decode(media["payload"])
                    if not self.is_streaming:
                        self.sst_stream.queue.put(chunk)
                elif data["event"] == "stop":
                    logging.info("Call media stream ended.")
                    break
        except simple_websocket.ws.ConnectionClosed:
            logging.warn("Call media stream connection lost.")
        finally:
            # Ensure the DeepgramStream is closed when the WebSocket connection is closed
            self.sst_stream.close()

    def stream_elevenlabs(self, text: str):
        # Step 1: get the streamSid, which is a unique identifier of the stream
        stream_sid = self.stream_sid
        duration = 0
        if not stream_sid:
            logging.error("No stream SID available. Cannot send audio.")
            return  # Exit if stream_sid is not set

        print(f"stream SID: {stream_sid}")

        # Step 2: send a request to elevenlabs client and gather the chunks
        audio_generator = elevenLabs_client.generate(
            text=text,
            voice="Rachel",
            model="eleven_turbo_v2",
            output_format="ulaw_8000",
        )

        # Consume the generator and send audio chunks immediately
        for chunk in audio_generator:
            if not chunk:
                logging.error("No audio generated from ElevenLabs.")
                return  # Exit if no audio is generated
            num_samples = len(chunk)
            chunk_duration = num_samples / 8000
            duration += chunk_duration

            audio_base64 = base64.b64encode(chunk).decode("utf-8")

            # Step 3: send a websocket message to twilio
            message = {
                "streamSid": stream_sid,
                "event": "media",
                "media": {"payload": audio_base64},
            }
            try:
                self.ws.send(json.dumps(message))
            except Exception as e:
                logging.error(f"Failed to send WebSocket message: {e}")

        self.is_streaming = True
        time.sleep(duration)
        print("Read yfor caller's message")
        self.is_streaming = False

    def start_session(self):  # Fix: Adjusted indentation
        self._read_ws()
