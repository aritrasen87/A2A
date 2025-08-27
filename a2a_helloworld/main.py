import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import HelloWorldAgentExecutor


def main():
    skill = AgentSkill(
        id="hello_world",
        name="a2a_helloworld",
        description="Returns Hello World",
        tags=["hi", "hello", "world"],
        examples=["Hey", "Hello", "Hi"],
    )

    agent_card = AgentCard(
        name="Hello World A2A Agent",
        description="A simple agent that returns a greeting",
        url="http://localhost:7001/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        version="1.0.0",
        capabilities=AgentCapabilities(push_notifications=False, streaming=False),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=HelloWorldAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=7001)


if __name__ == "__main__":
    main()