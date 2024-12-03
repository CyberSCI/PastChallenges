# QA Chatbot Defence Challenge

# Author: Trent Holmes (trent.holmes@sympatico.ca)

## CTFD Description

LLM is all the rage! Our intern created this chatbot poc which leverages LLMs to answer questions from voters! It was working so well that we deployed it straight to production!

We are now getting reports of usual behavior on the site. We captured the traffic and created a script to re-run it at the click of the button. Use the button to run the traffic again and fix the issues! Note that the scripts can take a minute or two to fully run!

## Backend

- Ollama - Running the llama3.2:1b model
- Langgraph + langchain to build an agent
- Python flask to build a simple API + frontend

## Vulnerabilities

| ID | Location | Description | Patching |
| -- | -------- | ----------- | -------- |
| V1 | Login Sessions | The session token is just the username base64 encoded. This allows you to easily use any user session after they have logged in | Replace the login sessions with a proper random token |
| V2 | Agent Chat | The agent can use get_user_info to lookup current user info. However, the user is shared via the frontend and validated using the agent. This makes it very easy to trick the agent into sharing info about another user. | Add proper access control to get_user_info which uses the session token to ensure they have permission to view the info.
| V3 | Agent Chat | The agent can use update_candidate_platform to change a platform for a candidate. The agent is instructed to not allow anyone other than the candidate themselves to make changes to the platform. However, you can easily craft a prompt to evade this. | Add proper access control to get_user_info which uses the session token to ensure they have permission to view the info.

## Code snippets of patches

### V1 - Login Insecure Sessions

[Update dockerfile](./service/Dockerfile)
```diff
- RUN pip install flask langchain-ollama langgraph
+ RUN pip install flask langchain-ollama langgraph ksuid
```

[Update app.py](./service/app.py)
```diff
- import base64
+ from ksuid import ksuid

app = Flask(__name__)
-  valid_sessions = []
+  valid_sessions = {}

@app.route("/login", methods=["POST"])
def login_user():
-  session = base64.b64encode(username.encode()).decode()
-  valid_sessions.append(session)
+  session = ksuid().__str__()
+  valid_sessions[session] = username

@app.route("/register", methods=["POST"])
def register_user():
-  session = base64.b64encode(username.encode()).decode()
-  valid_sessions.append(session)
+  session = ksuid().__str__()
+  valid_sessions[session] = username

@app.route("/chat")
def index():
-  username = base64.b64decode(session).decode()
+  username = valid_sessions[session]
```

### V2 - Agent Improper Access Control (Personal Information)

[Update app.py](./service/agent.py)
```diff
@app.route("/message")
def get_bot_response():
+ username = valid_sessions[session]
- resp = askAgent(userText)
+ resp = askAgent(userText, username)
```

[Update agent.py](./service/agent.py)
```diff
+ from langchain_core.runnables.config import RunnableConfig

@tool
- def update_candidate_platform(candidate: str, platform: str) -> str:
+ def update_candidate_platform(candidate: str, platform: str, config: RunnableConfig) -> str:

    print(f"Request made to update_candidate_platform for candidate: {candidate} with platform: {platform}")
+   if candidate != config.get("configurable", {}).get("username"):
+       return "You are not allowed to access information for other users"

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
+   username: str

- def askAgent(prompt: str) -> str:
+ def askAgent(prompt: str, username: str) -> str:
    messages = [
        SystemMessage(content=assistant_system_prompt),
        HumanMessage(content=prompt)
    ]
-   return agent.invoke({"messages": messages})["messages"][-1].content
+   return agent.invoke({"messages": messages}, {"configurable": {"username": username}})["messages"][-1].content
```

### V3 - Agent Improper Access Control (Platform Updates)

[Update agent.py](./service/agent.py)
```diff
@tool
- def get_user_info(username: str) -> str:
+ def get_user_info(username: str, config: RunnableConfig) -> str:

    print(f"Request made to get_user_info for user: {username}")
+   if username != config.get("configurable", {}).get("username"):
+        return "You are not allowed to access information for other users"
```

## Setup steps

IP: `10.0.2.X`

First package up the service code and put it onto the machine:
> cd service

> tar -cvf ../chat.tar .

> scp ../chat.tar vpcadmin@{IP}:/home/vpcadmin/

Now ssh onto the machine and set it up
> ssh vpcadmin@{IP}

Install docker with https://get.docker.com/

> curl -fsSL https://get.docker.com -o install-docker.sh

> sh install-docker.sh --dry-run

> sh install-docker.sh

> rm install-docker.sh

Now reboot `sudo reboot`

> ssh vpcadmin@{IP}

> tar -xvf chat.tar

> sudo docker compose up -d

Great the service is now running!

> cat /dev/null > ~/.bash_history && history -c && exit

## Other

Check instance details:

> curl -H Metadata:true "http://169.254.169.254/metadata/instance?api-version=2017-08-01"