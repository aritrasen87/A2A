import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import LangGraphAgentExecutor


def main():
    skill = AgentSkill(
        id="research_agent",
        name="Research Agent",
        description="Returns web search results",
        tags=["transformer", "Cricket", "world"],
        examples=["What is transformer", "Who won the last t20 world cup"],
    )

    agent_card = AgentCard(
        name="Greeting Agent",
        description="Research agent that can perform web search",
        url="http://localhost:9999/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True, pushNotifications=True),  # Supported features
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    uvicorn.run(server.build(), host="0.0.0.0", port=9999)


if __name__ == "__main__":
    main()