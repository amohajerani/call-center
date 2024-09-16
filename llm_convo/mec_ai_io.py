from typing import List, Optional
import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.messages import AIMessage, HumanMessage

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


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
        last_msg = transcript[-1]
        chat_history = []
        for idx, val in enumerate(transcript[:-1]):
            if idx % 2 == 0:
                chat_history.append(AIMessage(content=val))
            else:
                chat_history.append(HumanMessage(content=val))
        print("chat_history: ", chat_history)

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
