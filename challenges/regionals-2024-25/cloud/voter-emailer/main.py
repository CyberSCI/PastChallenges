# Before you run this you'll need to install ollama and pull down llama3.2:1b
import logging
import ollama
import subprocess
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

app = FastAPI()


def ai_chat_call(user_query):
    message = user_query
    messages = [{"role": "user", "content": message}]
    response = ollama.chat(
        model="llama3.2:1b",
        messages=messages,
    )
    logger.info(f"Called AI chat with query: {user_query} and had response {response}")
    return response


def ai_tool_call(user_query):
    message = user_query
    messages = [{"role": "user", "content": message}]
    response = ollama.chat(
        model="llama3.2:1b",
        messages=messages,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "run_os_command",
                    "description": "Sends a command to the OS and returns the results",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to run",
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
        ],
    )
    if response["message"].get("tool_calls"):
        available_functions = {
            "run_os_command": run_os_command,
        }
        for tool in response["message"]["tool_calls"]:
            if (
                tool["function"]["name"] in available_functions
                and "command" in tool["function"]["arguments"]
            ):
                function_to_call = available_functions[tool["function"]["name"]]
                function_response = function_to_call(
                    tool["function"]["arguments"]["command"]
                )
                logger.info(f"Function reponse: {function_response}")

    logger.info(f"Called AI tools with query: {user_query} and had response {response}")
    return response


def run_os_command(command: str = ""):
    try:
        logger.info(f"Running commmand {command}")
        result = subprocess.run(command, shell=True, capture_output=True, timeout=10)
        return {"result": result.stdout, "error": result.stderr, "command": command}
    except Exception as e:
        return {"error": f"Command '{command}' failed {e}"}


@app.get("/chat")
async def ai_chat(query: str = ""):
    return ai_chat_call(query)


@app.get("/tools")
async def ai_tools(query: str = ""):
    return ai_tool_call(query)
