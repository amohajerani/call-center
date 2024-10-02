from gevent import monkey

monkey.patch_all()

import logging
import time
from agents import TwilioCaller, AIAgent
from twilio_io import TwilioServer
from conversation import run_conversation
from pyngrok import ngrok


port = 8080
remote_host = "adapted-commonly-jennet.ngrok-free.app"


logging.getLogger().setLevel(logging.INFO)
ngrok.connect(port, domain=remote_host)

logging.info(f"Starting server at {remote_host} from local:{port}")
logging.info(f"Set call webhook to https://{remote_host}/incoming-voice")

tws = TwilioServer(remote_host=remote_host, port=port)
tws.start()


def run_chat(sess, phone_number):
    ai_agent = None
    member_agent = None
    try:
        init_phrase = "Thank you for calling Signify. My name is Sarah. Can you verify your name please?"

        ai_agent = AIAgent( init_phrase=init_phrase, phone_number=phone_number)
        member_agent = TwilioCaller(
            sess,
        )

        while not member_agent.session.media_stream_connected():
            time.sleep(0.1)
        run_conversation(ai_agent, member_agent)

    finally:
        # Delete instances when the call ends
        if ai_agent:
            del ai_agent
        if member_agent:
            del member_agent
        logging.info("Call ended. Agent instances deleted.")
        # sys.exit(0)


tws.on_session = run_chat
