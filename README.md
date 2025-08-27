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
uv add a2a-sdk starlette sse-starlette uvicorn pydantic langgraph

### Steps to run the hello_world a2a
mkdir a2a_helloworld
create:
    - main.py
    - agent_executor.py
    - client.py
uv run main.py
uv run client.py