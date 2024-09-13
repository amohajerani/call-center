from llm_convo.mec_ai_io import OpenAIChatCompletion, LangChainAgent
import threading


def run_in_thread(completion_event):
    transcript = ["hello, how can i help you?", "I am calling to get more information."]
    ag = LangChainAgent(system_prompt="you are a call center representative.")
    res = ag.get_response(transcript)
    transcript.append(res)
    transcript.append("my name is Oliver")

    transcript.append("please check my identity using my name")
    res = ag.get_response(transcript)
    print("res: ", res)

    # Signal that the agent has completed its work
    completion_event.set()


# Create an event to signal completion
completion_event = threading.Event()


# Create a thread and run the function in that thread
thread = threading.Thread(
    target=run_in_thread, name="AI_Agent_Thread", args=(completion_event,)
)
thread.start()

# Wait for the completion event to be set
# completion_event.wait()
