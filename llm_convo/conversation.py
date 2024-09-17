from llm_convo.agents import ChatAgent, CallEndedException


def run_conversation(ai_agent: ChatAgent, member_agent: ChatAgent):
    transcript = []
    while True:
        try:
            text_a = ai_agent.get_response(transcript)
            transcript.append(text_a)
            print("->", text_a)

            text_b = member_agent.get_response(transcript)
            transcript.append(text_b)
            print("->", text_b)
        except CallEndedException:
            print("Call ended.")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            break

    print("Conversation ended after", len(transcript) // 2, "turns.")
