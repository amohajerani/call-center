"""
This is a working example of streaming elvenlabs
"""

import os
from dotenv import load_dotenv
from flask import Flask, request, Response
from flask_sock import Sock
import json
from twilio.twiml.voice_response import VoiceResponse
import base64
from elevenlabs.client import ElevenLabs

load_dotenv()

app = Flask(__name__)
sock = Sock(app)
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


PORT = int(os.getenv('PORT', '8080'))

OUTPUT_FORMAT = 'ulaw_8000'
TEXT = 'This is a test. You can now hang up. Thank you.'


@app.route('/incoming-voice', methods=['POST'])
def incoming_call():
    print(f"Incoming call received. Host: {request.host}")
    twiml = VoiceResponse()
    stream_url = f"wss://{request.host}/call/connection"
    print(f"Stream URL: {stream_url}")
    twiml.connect().stream(url=stream_url)
    return Response(str(twiml), mimetype='text/xml')


@sock.route('/call/connection')
def call_connection(ws):
    while True:
        data = ws.receive()
        message = json.loads(data)

        if message['event'] == 'start' and 'start' in message:
            stream_sid = message['start']['streamSid']
            audio_generator = client.generate(
                text=TEXT,
                voice='Rachel',
                model="eleven_turbo_v2",
                output_format=OUTPUT_FORMAT
            )

            # Consume the generator and concatenate the audio chunks
            audio = b''.join(chunk for chunk in audio_generator)

            audio_base64 = base64.b64encode(audio).decode('utf-8')

            ws.send(json.dumps({
                'streamSid': stream_sid,
                'event': 'media',
                'media': {
                    'payload': audio_base64
                }
            }))


if __name__ == '__main__':
    print(f"Local: http://localhost:{PORT}")
    print(f"Remote: https://{os.getenv('SERVER_DOMAIN')}")
    app.run(port=PORT, debug=True)
