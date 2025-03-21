import os  # Standard library for file and environment variable operations
import traceback  # Used for debugging exceptions
from fastapi import FastAPI, Request, BackgroundTasks  # Import FastAPI and related classes
from dotenv import load_dotenv  # Load environment variables from .env file
from langchain_openai import ChatOpenAI  # Interface to access OpenAI models
from langgraph.graph import StateGraph, MessagesState, START, END  # LangGraph components for conversation flow
from langgraph.prebuilt import ToolNode  # Prebuilt node to execute tool functions
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage  # Message types for conversation
# Import our utility function from the new utils folder
from utils.utils import handle_tool_calls  
# Import Ops Agent tools (renamed from ec2_tools.py to ops_agent_tools.py)
from tools.ops_agent_tools import (list_instances, start_instance, stop_instance, 
    describe_instance, create_instance, list_security_groups, 
    list_key_pairs, list_volume_types)
from utils.callbacks import CustomCallbackHandler  # Import the custom callback handler

load_dotenv()  # Load all environment variables from .env

# Initialize the FastAPI app with a clear title indicating its purpose
app = FastAPI(title="Ops Agent")  # This is the primary operations agent

# Load the system prompt file (used to guide model responses)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current directory of this file
SYSTEM_PROMPT_PATH = os.path.join(BASE_DIR, "..", "system_prompts", "ec2_prompt.txt")  # Construct the path to the prompt file
with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:
    system_prompt = file.read()  # Read the system prompt content

# Initialize the OpenAI Chat model and bind our tools for extended functionality
model = ChatOpenAI(
    model="gpt-4",  # Specify which GPT model to use
    temperature=0,  # Use temperature 0 for deterministic outputs
    openai_api_key=os.getenv("OPENAI_API_KEY"),  # Get API key from environment
    max_tokens=4096  # Maximum tokens permitted in responses
)
tools = [
    list_instances, start_instance, stop_instance, describe_instance,
    create_instance, list_security_groups, list_key_pairs, list_volume_types
]  # List of tool functions available to the agent
model_with_tools = model.bind_tools(tools)  # Bind the tools to the model; this allows the model to invoke them
tool_node = ToolNode(tools=tools)  # Wrap tools into a ToolNode for the LangGraph flow

# Function to decide next step in conversation; if a tool call is pending, continue to that node
def should_continue(state: MessagesState) -> str:
    # Check if the last message has an associated tool call
    last_message = state["messages"][-1]
    return "tools" if last_message.tool_calls else END  # If tool call found, continue; otherwise, end the flow

# Function to wrap the model invocation ensuring system prompt is included
def call_model(state: MessagesState):
    # Process the conversation history, handling any special tool calls
    messages = handle_tool_calls(state["messages"])
    # Prepend the system prompt if it is not already present in the message history
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages.insert(0, SystemMessage(content=system_prompt))
    response = model_with_tools.invoke(messages)  # Invoke the model with the updated messages list
    return {"messages": response if isinstance(response, list) else [response]}  # Ensure we always return a list

# Define the conversation flow using LangGraph; this modular design makes it easier to extend
chatflow = StateGraph(MessagesState)
chatflow.add_node("agent", call_model)  # Add node for the agent's processing
chatflow.add_node("tools", tool_node)  # Add node for executing tool calls
chatflow.add_edge(START, "agent")  # Start flow at the agent node
chatflow.add_conditional_edges("agent", should_continue, ["tools", END])  # If tool calls needed, go to tools; else end
chatflow.add_edge("tools", "agent")  # After executing a tool, return to agent for further processing
chat_agent = chatflow.compile()  # Compile the flow into an executable agent

# Create an endpoint for receiving requests; this endpoint will be used by clients
@app.post("/ops_agent")
async def ops_agent_endpoint(request: Request, background_tasks: BackgroundTasks):
    # Parse incoming JSON payload to extract a message from the user
    body = await request.json()
    user_message = body.get("message", "")  # Retrieve user message; default to empty if not provided
    # Invoke the compiled conversation flow with the user message wrapped in a HumanMessage
    result = chat_agent.invoke({"messages": [HumanMessage(content=user_message)]})
    final_messages = result["messages"]  # Extract responses from the model
    # Concatenate all AI responses into a single text output
    response_text = "\n".join([msg.content for msg in final_messages if isinstance(msg, AIMessage)])
    return {"response": response_text}  # Return the result as JSON
