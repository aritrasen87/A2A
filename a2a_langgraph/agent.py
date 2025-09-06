import os
from dotenv import load_dotenv
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage , AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables.config import RunnableConfig 
from langchain_core.tools import tool              # To define a callable tool for the agent
from typing import Any, Literal, AsyncIterable
from pydantic import BaseModel

memory = MemorySaver()

# ResponseFormat schema: validates what the agent returns
class ResponseFormat(BaseModel):
    status: Literal["completed", "input_required", "error"]  # Structured status of the agent reply
    message: str                                              # The message that will be shown to the user


### Research Agent for Web Search
tavily_tool = TavilySearchResults(max_results=5)
@tool
def web_search(query: str) -> str:
    """Search the web for information."""
    print('Invoking Tavily search for query:', query)
    docs = tavily_tool.invoke({"query": query})
    web_results = "\n".join([d["content"] for d in docs])
    #web_results = 'This is dummy result'
    return web_results



class AppAgent:

    # Response formatting guidelines expected by the agent
    RESPONSE_FORMAT_INSTRUCTION = (
        "Use 'completed' if the task is done, 'input_required' if clarification is needed, "
        "and 'error' if something fails. Always include a user-facing message."
    )
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        self.graph = self.app()

    def app(self):
        """Create a research agent with web search"""
        app = create_react_agent(
            model=self.llm,
            tools=[web_search],
            name="research_expert",
            prompt="Call the tool.",
            response_format=(self.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
            checkpointer=memory
            )

        return app
    
    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        """
        This function is used when a user sends a message to the agent.
        Instead of waiting for a single response, it gives us updates as they happen.

        - 'query' is the user’s question or command (e.g., "What time is it?")
        - 'session_id' is a unique ID for this user's interaction (to maintain context)        
        """

        # --------------------------------------------------------------
        # Set up a configuration that ties this request to a session.
        # LangGraph needs a session/thread ID to track the conversation.
        # --------------------------------------------------------------
        config: RunnableConfig = {
            "configurable": {
                "thread_id": session_id  # Unique ID to separate one user conversation from another
            }
        }

        inputs = {"messages": [("user", query)]}

        for item in self.graph.stream(inputs, config, stream_mode="values"):

            message = item["messages"][-1]

            # If the message is from the AI and includes tool usage,
            if isinstance(message, AIMessage) and message.tool_calls:
                yield { 
                    "is_task_complete": False,         
                    "require_user_input": False,       
                    "content": "Tool Call Required: Going for Tavily web search", 
                }

            # If the message is from the tool 
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,         
                    "require_user_input": False,       
                    "content": "Tool calling: Doing the Tavily Web search", 
                }

        yield self._final_response(config)

    def _final_response(self, config: RunnableConfig) -> dict[str, Any]:
        """
        After all streaming messages are done, this function checks what the agent finally decided.
        It uses the config to find the saved response (called 'structured_response').
        """

        state = self.graph.get_state(config)
        structured = state.values.get("structured_response")

        # check if the structured response is valid
        if isinstance(structured, ResponseFormat):
            if structured.status == "completed":
                return {
                    "is_task_complete": True,              # Mark this as done
                    "require_user_input": False,           # No further input needed
                    "content": structured.message,         # Show the user the final result
                }
            if structured.status in ("input_required", "error"):
                return {
                    "is_task_complete": False,             # Not done yet
                    "require_user_input": True,            # Ask the user to clarify
                    "content": structured.message,         # The question or error to show
                }
            
        print("[DEBUG] structured response:", structured)  # Print for debugging in the console

        return {
            "is_task_complete": False,                     # Don't mark this task as complete
            "require_user_input": True,                    # Ask the user to rephrase
            "content": "Unable to process your request at the moment. Please try again.",  # Default fallback message
        }