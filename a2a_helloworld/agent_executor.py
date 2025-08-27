from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from pydantic import BaseModel


class HelloWorld(BaseModel):
    """Hello world agent that returns a greeting"""

    async def invoke(self) -> str:
        return "Hello World!"


class HelloWorldAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = HelloWorld()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        result = await self.agent.invoke()
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("Cancel not supported")