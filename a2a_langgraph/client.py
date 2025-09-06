import asyncio                      
import json                         
import traceback                    
from uuid import uuid4             
from typing import Any
import uuid

import httpx                        
from rich import print as rprint   
from rich.syntax import Syntax      

# Import the official A2A SDK client and related types
from a2a.client import A2ACardResolver , A2AClient
from a2a.types import (
    AgentCard,                      
    SendStreamingMessageRequest,    
    MessageSendParams,             
    TaskState,                      
    Part,
    TextPart,
)


def build_message_payload(text: str, task_id: str | None = None, context_id: str | None = None) -> dict[str, Any]:
    # Constructs a dictionary payload that matches A2A message format
    return {
        "message": {
            "role": "user",  
            "parts": [Part(root=TextPart(text=text))],
            "messageId": uuid4().hex,  
            **({"taskId": task_id} if task_id else {}),  
            **({"contextId": context_id} if context_id else {}),
        }
    }


def print_json_response(response: Any, title: str) -> None:
    # Displays a formatted and color-highlighted view of the response
    print(f"\n=== {title} ===")  # Section title for clarity
    try:
        if hasattr(response, "root"):  # Check if response is wrapped by SDK
            data = response.root.model_dump(mode="json", exclude_none=True)
        else:
            data = response.model_dump(mode="json", exclude_none=True)

        json_str = json.dumps(data, indent=2, ensure_ascii=False)  # Convert dict to pretty JSON string
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)  # Apply syntax highlighting
        rprint(syntax)  # Print it with color
    except Exception as e:
        # Print fallback text if something fails
        rprint(f"[red bold]Error printing JSON:[/red bold] {e}")
        rprint(repr(response))

async def handle_streaming(client: A2AClient, text: str, task_id: str | None = None, context_id: str | None = None):
    # Construct streaming request payload
    request = SendStreamingMessageRequest(id=str(uuid.uuid4()),params=MessageSendParams(**build_message_payload(text, task_id, context_id)))

    # Track latest task/context ID to support multi-turn
    latest_task_id = None
    latest_context_id = None
    input_required = False

    # Process each streamed update
    async for update in client.send_message_streaming(request):
        print_json_response(update, "Streaming Update")  # Print each update as it comes

        # Extract context/task from current update
        if hasattr(update.root, "result"):
            result = update.root.result
            if hasattr(result, "contextId"):
                latest_context_id = result.contextId
            if hasattr(result, "status") and result.status.state == TaskState.input_required:
                latest_task_id = result.taskId
                input_required = True

    # If input was required, get response from user and continue conversation
    if input_required and latest_task_id and latest_context_id:
        follow_up = input("\U0001F7E1 Agent needs more input. Your reply: ")
        await handle_streaming(client, follow_up, latest_task_id, latest_context_id)

# User interaction loop
async def interactive_loop(client: A2AClient, supports_streaming: bool):
    print("\nEnter your query below. Type 'exit' to quit.")  
    while True:
        query = input("\n\U0001F7E2 Your query: ").strip()  # Get user input
        if query.lower() in {"exit", "quit"}:
            print("\U0001F44B Exiting...") 
            break
        # based on agent's capability
        if supports_streaming:
            await handle_streaming(client, query)
        else:
            pass


agent_url = "http://localhost:9999"
PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"

def main():
    asyncio.run(run_main(agent_url))  


async def run_main(agent_url: str):
    print(f"Connecting to agent at {agent_url}...")  # Let user know we're starting connection
    try:
        async with httpx.AsyncClient() as httpx_client:
            # Initialize A2ACardResolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=agent_url,
            )

            final_agent_card_to_use: AgentCard | None = None

            try:
                print(
                    f"Fetching public agent card from: {agent_url}{PUBLIC_AGENT_CARD_PATH}"
                )
                _public_card = await resolver.get_agent_card()
                print("Fetched public agent card")
                print(_public_card.model_dump_json(indent=2))

                final_agent_card_to_use = _public_card

            except Exception as e:
                print(f"Error fetching public agent card: {e}")
                raise RuntimeError("Failed to fetch public agent card")

            client = A2AClient(
                httpx_client=httpx_client, agent_card=final_agent_card_to_use
            )
            supports_streaming = final_agent_card_to_use.capabilities.streaming
            rprint(f"[green bold]✅ Connected. Streaming supported:[/green bold] {supports_streaming}")  # Confirm success
            await interactive_loop(client, supports_streaming)  # Start conversation loop

    except Exception:
        traceback.print_exc()  # Show full error trace
        print("❌ Failed to connect or run") # Notify user of failure


if __name__ == "__main__":
    main()