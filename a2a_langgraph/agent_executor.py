from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue

from a2a.server.events.event_queue import EventQueue

# Importing event and status types for responding to client
from a2a.types import (
    TaskArtifactUpdateEvent,  # Event for sending result artifacts back to the client
    TaskStatusUpdateEvent,   # Event for sending status updates (e.g., working, completed)
    TaskStatus,              # Object that holds the current status of the task
    TaskState,               # Enum that defines states: working, completed, input_required, etc.
)

# Utility functions to create standardized message and artifact formats
from a2a.utils import (
    new_agent_text_message,  # Creates a message object from agent to client
    new_task,                # Creates a new task object from the initial message
    new_text_artifact        # Creates a textual result artifact
)

from agent import AppAgent


class LangGraphAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = AppAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:

        query = context.get_user_input()  
        task = context.current_task      

        if not task:                     # If no existing task, this is a new interaction
            task = new_task(context.message) 
            await event_queue.enqueue_event(task)        # Enqueue the new task to notify the A2A server

        # Agent stream
        async for event in self.agent.stream(query, task.context_id):

            if event['is_task_complete']:  # If the task has been successfully completed
                # Send the result artifact to the A2A server
                await event_queue.enqueue_event(
                    TaskArtifactUpdateEvent(
                        taskId=task.id,                 
                        contextId=task.context_id,      
                        artifact=new_text_artifact(     
                            name='current_result',     
                            description='Result of request to agent.', 
                            text=event['content'],      # The actual result text
                        ),
                        append=False,                   
                        lastChunk=True,                 # This is the final chunk of the result
                    )
                )
                # Send final status update: task is completed
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,                 
                        contextId=task.context_id,       
                        status=TaskStatus(state=TaskState.completed),  # Mark task as completed
                        final=True,                     # This is the last status update
                    )
                )

            elif event['require_user_input']:  # If the agent needs more information from user
                # Enqueue an input_required status with a message
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,              
                        contextId=task.context_id,       
                        status=TaskStatus(
                            state=TaskState.input_required,  
                            message=new_agent_text_message(  
                                event['content'],             
                                task.context_id,               
                                task.id                       
                            ),
                        ),
                        final=True,                     # Input_required is a final state until user responds
                    )
                )

            else:
                # Enqueue a status update showing ongoing work
                await event_queue.enqueue_event(
                    TaskStatusUpdateEvent(
                        taskId=task.id,                 
                        contextId=task.context_id,       
                        status=TaskStatus(
                            state=TaskState.working,    
                            message=new_agent_text_message(
                                event['content'],      
                                task.context_id,        
                                task.id                 
                            ),
                        ),
                        final=False,                    # More updates may follow
                    )
                )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Optional method to cancel long-running tasks (not supported here)
        raise Exception('Cancel not supported')  # Raise error since this agent doesn’t support canceling