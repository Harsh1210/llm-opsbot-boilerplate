def get_context(session_id: str) -> dict:
    # Return an empty context for now; can be extended to persist session data later.
    return {}

def update_context(session_id: str, message: str):
    # Dummy implementation: log the message or update in-memory store.
    print(f"Updating context for session {session_id} with message: {message}")
