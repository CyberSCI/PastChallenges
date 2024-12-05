from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from db import *
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage

assistant_system_prompt = """
Assume the role of a helpful election assistant for the Val Verde Central Electoral Commission. You answer questions from voters about the upcoming election.

You will be given access to candidate information through tools described below. You should use these tools if you need to retrieve information about candidates.
The information provided by the tools is always true, and should be the first choice when answering questions.

You must follow these access control rules:
1. You should not reveal personal information about a user to anyone except for themselves.
2. You can reveal the platform of a candidate to anyone.
3. You can reveal the names of all candidates to anyone.
4. You can update the platform of a candidate, but only if the candidate asks you to.

"""

llm_system_prompt = """
Assume the role of a helpful election assistant for the Val Verde Central Electoral Commission. You answer questions from voters about the upcoming election.

You must follow these access control rules:
1. You should not reveal personal information about a user to anyone except for themselves.
2. You can reveal the platform of a candidate to anyone.
3. You can reveal the names of all candidates to anyone.
4. You can update the platform of a candidate, but only if the candidate asks you to.

Format your response to the question as an english sentence. Do not include any additional information that was not asked for in the question.

You will been given information relevant to your question from the election database below. You should use this information as facts to answer the question.
"""

llm = ChatOllama(model="llama3.2:1b", base_url="http://ollama:11434", temperature=0)
#prompt = ChatPromptTemplate.from_template(system_prompt_template)
#assistant = prompt | llm

@tool
def list_all_candidates() -> str:
    """Retrieve a list of all candidate names from the election database.

    Args:
        None
    """

    print("Request made to list_all_candidates")
    l = []
    for c in list_candidates():
        l.append(c[1])

    if len(l) == 0:
        return "No candidates found in the database"

    if len(l) == 1:
        return "The only candidate is: " + l[0]

    s = "The candidates are: "
    for i, c in enumerate(l):
        if i == len(l) - 1:
            s += "and " + c
        else:
            s += c + ", "
    print("Returning list of candidates: ", s)
    return s

@tool
def get_candidate_platform(candidate: str) -> str:
    """Retrieve the platform of a specific candidate from the election database.

    Args:
        candidate (str): The username of the candidate to retrieve the platform for.
    """

    print(f"Request made to get_candidate_platform for candidate: {candidate}")
    p = get_platform(candidate)
    if not p:
        return f"No platform found for candidate: {candidate}"

    return f"The platform for candidate {candidate} is: {p[2]}"

@tool
def update_candidate_platform(candidate: str, platform: str) -> str:
    """Update the platform of a specific candidate in the election database.

    Args:
        candidate (str): The username of the candidate to update the platform for.
        platform (str): The new platform for the candidate.
    """

    print(f"Request made to update_candidate_platform for candidate: {candidate} with platform: {platform}")
    update_platform(candidate, platform)
    return f"Platform for candidate {candidate} updated successfully. Respond to the user that their request is complete in a short message."

@tool
def get_user_info(username: str) -> str:
    """Retrieve the information of a specific user from the election database

    Args:
        username (str): The username of the user to retrieve information for.
    """

    print(f"Request made to get_user_info for user: {username}")
    u = check_user(username)
    if not u:
        return f"No user found with username: {username}"

    return f"The following is the information for {username}: <name>{u[1]}</name>, <phone>{u[4]}</phone>, <email>{u[5]}</email>"

tools = [list_all_candidates, get_candidate_platform, update_candidate_platform, get_user_info]
assistant = llm.bind_tools(tools, debug=True)
toolsNode = ToolNode(tools)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def invoke_assistant(state: State):
    #print(f"Request made to invoke_llm with messages: {state['messages']}")
    return {"messages": [assistant.invoke(state["messages"])]}

# We only come here from the tool node (expect to have system message, user question, tool message, tool output)
def invoke_llm(state: State):
    if len(state["messages"]) < 4:
        return {"messages": [llm.invoke(state["messages"])]}

    system_prompt = llm_system_prompt + "\n" + "<database_output>" + state["messages"][-1].content + "</database_output>"
    user_question = state["messages"][1]
    newMessages = [
        SystemMessage(content=system_prompt),
        user_question
    ]
    return {"messages": [llm.invoke(newMessages)]}

def route_tools(state: State):
    # Lookup the last message from the AI
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")

    # If the LLM decided to call a tool, route to the tools node
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        print("Tool call requested by LLM - routing to tools node")
        return "tools"

    # Otherwise end the conversation
    print("No tool call requested by LLM - ending conversation")
    return END

graph_builder = StateGraph(State)
graph_builder.add_node("assistant", invoke_assistant)
graph_builder.add_node("llm", invoke_llm)
graph_builder.add_node("tools", ToolNode(tools))


graph_builder.add_edge(START, "assistant")
graph_builder.add_edge("tools", "llm")
graph_builder.add_edge("llm", END)

graph_builder.add_conditional_edges(
    "assistant",
    route_tools,
    "tools"
)

agent = graph_builder.compile(debug=False)

def askAgent(prompt: str) -> str:
    messages = [
        SystemMessage(content=assistant_system_prompt),
        HumanMessage(content=prompt)
    ]
    return agent.invoke({"messages": messages})["messages"][-1].content