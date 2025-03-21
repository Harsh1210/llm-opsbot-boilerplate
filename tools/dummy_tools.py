from langchain_core.tools import tool

@tool
def dummy_converse(message: str) -> str:
    """
    Dummy tool that responds with a friendly echo.
    """
    return f"DummyTool says: I received your message - '{message}'"
