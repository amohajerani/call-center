from llm_convo.agents import ChatAgent, CallEndedException


def run_conversation(agent_a: ChatAgent, agent_b: ChatAgent):
    transcript = []
    while True:
        try:
            text_a = agent_a.get_response(transcript)
            transcript.append(text_a)
            print("->", text_a)

            text_b = agent_b.get_response(transcript)
            transcript.append(text_b)
            print("->", text_b)
        except CallEndedException:
            print("Call ended.")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            break

    print("Conversation ended after", len(transcript) // 2, "turns.")
