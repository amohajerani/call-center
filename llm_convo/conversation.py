from llm_convo.agents import ChatAgent, CallEndedException


def run_conversation(ai_agent: ChatAgent, member_agent: ChatAgent, member_information):
    transcript = []
    while True:
        # add the member_information to the top of the conversation for better visibility
        if len(transcript) == 2:  # after the first exchange
            transcript[0] = (
                transcript[0]
                + "I have accessed your infomration. "
                + member_information
            )

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
