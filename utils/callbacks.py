from langchain.callbacks.base import BaseCallbackHandler

class CustomCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.intermediate_steps = []

    def on_chain_start(self, serialized, inputs, **kwargs):
        self.intermediate_steps.append({"event": "chain_start", "inputs": inputs})

    def on_chain_end(self, outputs, **kwargs):
        self.intermediate_steps.append({"event": "chain_end", "outputs": outputs})

    def on_tool_start(self, serialized, inputs, **kwargs):
        self.intermediate_steps.append({"event": "tool_start", "inputs": inputs})

    def on_tool_end(self, outputs, **kwargs):
        self.intermediate_steps.append({"event": "tool_end", "outputs": outputs})

    def on_text(self, text, **kwargs):
        self.intermediate_steps.append({"event": "text", "text": text})

    def get_intermediate_steps(self):
        return self.intermediate_steps
