from gevent import monkey

monkey.patch_all()

import logging
import argparse
import tempfile
import os
import time
import sys
from llm_convo.agents import OpenAIChat, TwilioCaller, LangchainChat
from llm_convo.audio_input import get_whisper_model
from llm_convo.twilio_io import TwilioServer
from llm_convo.conversation import run_conversation
from pyngrok import ngrok


def main(port, remote_host, start_ngrok):
    if start_ngrok:
        ngrok_http = ngrok.connect(port)
        remote_host = ngrok_http.public_url.split("//")[1]
        print("remote host: ", remote_host)

    static_dir = os.path.join(tempfile.gettempdir(), "twilio_static")
    os.makedirs(static_dir, exist_ok=True)

    logging.info(
        f"Starting server at {remote_host} from local:{port}, serving static content from {static_dir}"
    )
    logging.info(f"Set call webhook to https://{remote_host}/incoming-voice")

    input(" >>> Press enter to start the call after ensuring the webhook is set. <<< ")

    tws = TwilioServer(remote_host=remote_host, port=port, static_dir=static_dir)
    tws.start()

    def run_chat(sess, outbound_call):
        if outbound_call:
            system_prompt = """
                You are a call center agent. Your task is to call members and help them schedule appointments. \
                    Be polite, professional, and efficient. Ensure you gather all necessary information such as the preferred date, time, and type of appointment. \
                    Confirm the details with the member before ending the call.
            """
            init_phrase = "Hi,This is Sarah from Signify Health. You are on a recorded call. I am calling to schedule your annual wellness visit."
        else:
            system_prompt = """
                You are a call center agent at Signify Health. You have received a call from a call from a member. \
                The members usually call regarding their appointments. Your task is to answer their questions, manage their appointments, and provide them with the necessary information. \
                    
            """
            init_phrase = "Thank you for calling Signify. My name is Sarah. I am an AI assistant. Can you verify your name please?"

        mec_agent = LangchainChat(system_prompt=system_prompt, init_phrase=init_phrase)
        member_agent = TwilioCaller(
            sess,
            # thinking_phrase="One moment"
        )
        while not member_agent.session.media_stream_connected():
            time.sleep(0.1)
        run_conversation(mec_agent, member_agent)
        sys.exit(0)

    tws.on_session = run_chat


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--preload_whisper", action="store_true")
    parser.add_argument("--start_ngrok", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--remote_host", type=str, default="localhost")
    args = parser.parse_args()
    if args.preload_whisper:
        get_whisper_model()
    main(args.port, args.remote_host, args.start_ngrok)
