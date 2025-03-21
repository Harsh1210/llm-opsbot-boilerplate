import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from tools.dummy_tools import dummy_converse
from utils.state_management import update_context
from utils.callbacks import CustomCallbackHandler  # Import the custom callback handler

load_dotenv()
app = FastAPI(title="Dummy Agent")

# Load dummy system prompt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DUMMY_PROMPT_PATH = os.path.join(BASE_DIR, "..", "system_prompts", "dummy_prompt.txt")
with open(DUMMY_PROMPT_PATH, "r", encoding="utf-8") as file:
    dummy_prompt = file.read()

# Initialize the dummy OpenAI model and bind the dummy tool
model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY", "dummy_key"),
    max_tokens=100
)
tools = [dummy_converse]
model_with_tools = model.bind_tools(tools)
tool_node = ToolNode(tools=tools)

# Function to decide flow continuation
def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END

# Function to call the model with dummy system prompt
def call_model(state: MessagesState):
    messages = state["messages"]
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages.insert(0, SystemMessage(content=dummy_prompt))
    response = model_with_tools.invoke(messages)
    return {"messages": response if isinstance(response, list) else [response]}

# Define LangGraph flow for dummy agent
chatflow = StateGraph(MessagesState)
chatflow.add_node("agent", call_model)
chatflow.add_node("tools", tool_node)
chatflow.add_edge(START, "agent")
chatflow.add_conditional_edges("agent", should_continue, ["tools", END])
chatflow.add_edge("tools", "agent")
chat_agent = chatflow.compile()

# Dummy agent endpoint that updates context and processes messages
@app.post("/dummy_agent")
async def dummy_agent_endpoint(request: Request):
    body = await request.json()
    user_message = body.get("message", "")
    session_id = "dummy_session"  # Replace with session logic if needed
    update_context(session_id, user_message)
    result = chat_agent.invoke({"messages": [HumanMessage(content=user_message)]})
    final_messages = result["messages"]
    response_text = "\n".join([msg.content for msg in final_messages if isinstance(msg, AIMessage)])
    return {"response": response_text}

# Example usage:
# callback_handler = CustomCallbackHandler()
# You can use this handler within the dummy agent similar to the Ops Agent if needed.
