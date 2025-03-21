# LLM Ops Bot Boilerplate

## Overview
LLM Ops Bot Boilerplate is a modular framework that supports multiple agent implementations using FastAPI, LangChain, and AWS tools. It facilitates the creation of agents such as an Ops Agent for managing AWS EC2 instances and Dummy Agents for testing purposes. The repository also includes support for various chat integrations and databases.

## Project Structure
```
├── agents
│   ├── ops_agent.py             # Ops Agent FastAPI app (endpoint: /ops_agent)
│   └── dummy_agent.py           # Dummy Agent FastAPI app (endpoint: /dummy_agent)
├── chat_integrations
│   ├── teams.py                 # Dummy Teams integration
│   └── whatsapp.py              # WhatsApp integration
├── db
│   ├── db.py                    # Primary database connection and models
│   └── dummy_db.py              # Dummy database for testing
├── docker-compose.yml           # Docker Compose configuration
├── dockerfiles
│   ├── Dockerfile.ops_agent     # Dockerfile for building the Ops Agent container
│   └── Dockerfile.dummy_agent   # Dockerfile for building the Dummy Agent container
├── system_prompts
│   ├── ec2_prompt.txt           # System prompt for Ops Agent (consider renaming to ops_prompt.txt)
│   └── dummy_prompt.txt         # System prompt for Dummy Agent
├── tools
│   ├── ops_agent_tools.py       # Tools for the Ops Agent
│   └── dummy_tools.py           # Tools for the Dummy Agent
├── utils
│   ├── callbacks.py             # Custom callback handler for tracking model interactions
│   ├── state_management.py      # State management for chat context
│   └── utils.py                 # Utility functions (e.g., shell commands, tool call handling)
└── README.md                    # This file
```

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- Python dependencies defined in `requirements.txt`
- A `.env` file configured with the following variables:
  - `OPENAI_API_KEY`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_DB`
  - `WHATSAPP_ACCESS_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`
  - `META_VERIFY_TOKEN`

### Running the Application
Build and start all containers with Docker Compose:
```bash
docker-compose up --build
```
This command will:
- Build the Ops Agent container using `dockerfiles/Dockerfile.ops_agent` and expose it on port **8000**.
- Build the Dummy Agent container using `dockerfiles/Dockerfile.dummy_agent` and expose it on port **8001**.
- Start a Postgres container for database support.

Access the agents via:
- **Ops Agent:** [http://localhost:8000/ops_agent](http://localhost:8000/ops_agent)
- **Dummy Agent:** [http://localhost:8001/dummy_agent](http://localhost:8001/dummy_agent)

### Adding a New Agent

To add a new agent to the framework, follow these steps:

1. **Develop the Agent:**
   - In the `agents` directory, create a new Python file (e.g., `new_agent.py`).
   - Follow the structure of `ops_agent.py` or `dummy_agent.py`:
     - Load the appropriate system prompt from the `system_prompts` folder.
     - Initialize a ChatOpenAI model and bind any specific tools (created in a corresponding file in `tools`).
     - Define a LangGraph conversation flow.
     - Expose a unique API endpoint (e.g., `/new_agent`).

2. **Create a System Prompt:**
   - Add a system prompt file in the `system_prompts` directory (e.g., `new_agent_prompt.txt`).

3. **Implement Agent Tools:**
   - If required, create a new tools file in the `tools` directory (e.g., `new_agent_tools.py`) with functions specific to the new agent.

4. **Add Docker Support:**
   - In the `dockerfiles` folder, create a new Dockerfile (e.g., `Dockerfile.new_agent`) that builds the new agent container:
     ```dockerfile
     # filepath: /home/ubuntu/llm-opsbot-boilerplate/dockerfiles/Dockerfile.new_agent
     FROM python:3.9-slim
     WORKDIR /app
     COPY ../requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     COPY .. .
     CMD ["uvicorn", "agents.new_agent:app", "--host", "0.0.0.0", "--port", "8000"]
     ```
   - Update the `docker-compose.yml` file with a new service entry for the new agent:
     ```yaml
     new_agent:
       build:
         context: .
         dockerfile: dockerfiles/Dockerfile.new_agent
       container_name: new_agent_container
       ports:
         - "8002:8000"  # Update host port as needed
       environment:
         - OPENAI_API_KEY=your_openai_api_key
         # Include any additional environment variables specific to new_agent
       depends_on:
         - postgres
       networks:
         - ops_network
     ```

5. **Test the New Agent:**
   - Rebuild the containers using:
     ```bash
     docker-compose up --build
     ```
   - Verify the new agent by accessing its endpoint (e.g., [http://localhost:8002/new_agent](http://localhost:8002/new_agent)).

## Further Development

- **Chat Integrations:**  
  Add integrations for additional platforms (e.g., Microsoft Teams) in the `chat_integrations` directory.
- **Database:**  
  Extend or add new database models in the `db` directory using SQLAlchemy.
- **Utilities & Callbacks:**  
  Enhance shared functionality in the `utils` folder; consider expanding `callbacks.py` for advanced logging of model interactions.
- **Customization:**  
  Modify LangGraph flow logic, tool implementations, and system prompts to suit your specific use cases.

## Contributing
Contributions are welcome. To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Ensure your code complies with PEP8 guidelines and is well documented.
4. Update the README with any changes that affect setup or usage.
5. Submit a pull request describing your changes.

---


