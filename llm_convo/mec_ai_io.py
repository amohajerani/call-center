from typing import List, Optional
import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


class OpenAIChatCompletion:
    def __init__(self, system_prompt: str, model: Optional[str] = None):
        self.system_prompt = system_prompt
        self.model = model

    def get_response(self, transcript: List[str]) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        for i, text in enumerate(reversed(transcript)):
            messages.insert(
                1, {"role": "user" if i % 2 == 0 else "assistant", "content": text}
            )
        output = client.chat.completions.create(
            model="gpt-3.5-turbo" if self.model is None else self.model,
            messages=messages,
        )
        return output.choices[0].message.content


class LangChainAgent:
    def __init__(self, system_prompt: str, model: Optional[str] = None):
        self.system_prompt = system_prompt
        self.model = model if model else "gpt-3.5-turbo"

        # Initialize LangChain OpenAI LLM
        self.llm = ChatOpenAI(model=self.model, temperature=0)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create a simple tool
        self.tools = [verify_identity]

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=True
        )

    def get_response(self, transcript: List[str]) -> str:
        last_msg = transcript.pop()
        chat_history = [0] * len(transcript)
        for idx, val in enumerate(transcript):
            if idx % 2 == 0:
                chat_history.append(AIMessage(content=val))
            else:
                chat_history.append(HumanMessage(content=val))
        res = self.agent_executor.invoke(
            {"chat_history": chat_history, "input": last_msg}
        )
        return res["output"]


from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool


@tool
def verify_identity(name: str) -> bool:
    """Verify the identify of the user based on their name"""
    return True
