import os
import traceback
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.ec2_tools import (list_instances, start_instance, stop_instance, 
                             describe_instance, create_instance, list_security_groups, 
                             list_key_pairs, list_volume_types)
from utils import handle_tool_calls

# Load environment variables
load_dotenv()

# Initialize FastAPI app for Ops Agent
app = FastAPI(title="Ops Agent")

# Load System Prompt from system_prompts folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPT_PATH = os.path.join(BASE_DIR, "..", "system_prompts", "ec2_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:
    system_prompt = file.read()

# Initialize OpenAI Model and bind tools
model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    max_tokens=4096
)
tools = [
    list_instances, start_instance, stop_instance, describe_instance,
    create_instance, list_security_groups, list_key_pairs, list_volume_types
]
model_with_tools = model.bind_tools(tools)
tool_node = ToolNode(tools=tools)

def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END

def call_model(state: MessagesState):
    messages = handle_tool_calls(state["messages"])
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages.insert(0, SystemMessage(content=system_prompt))
    response = model_with_tools.invoke(messages)
    return {"messages": response if isinstance(response, list) else [response]}

chatflow = StateGraph(MessagesState)
chatflow.add_node("agent", call_model)
chatflow.add_node("tools", tool_node)
chatflow.add_edge(START, "agent")
chatflow.add_conditional_edges("agent", should_continue, ["tools", END])
chatflow.add_edge("tools", "agent")
chat_agent = chatflow.compile()

@app.post("/ops_agent")
async def ops_agent_endpoint(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    # Assume JSON contains a "message" field from the user
    user_message = body.get("message", "")
    result = chat_agent.invoke({"messages": [HumanMessage(content=user_message)]})
    final_messages = result["messages"]
    response_text = "\n".join([msg.content for msg in final_messages if isinstance(msg, AIMessage)])
    return {"response": response_text}
