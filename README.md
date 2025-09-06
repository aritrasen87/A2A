## Create the project folder
mkdir a2a

cd a2a

## create environemnt
uv venv --python 3.13 

## active environment
source .venv/bin/activate

## initialize the project
uv init

## Install dependencies
uv add a2a-sdk starlette sse-starlette uvicorn pydantic langgraph dotenv langgraph-supervisor langchain langchain_openai langchain_community

### Steps to run the hello_world a2a 

- create:
    - main.py
    - agent_executor.py
    - client.py
- uv run main.py
- uv run client.py


### Steps to run the langgraph a2a agent 
cd a2a_langgraph

- create:
    - agent.py
    - agent_executor.py
    - main.py
    - client.py
- uv run main.py
- uv run client.py