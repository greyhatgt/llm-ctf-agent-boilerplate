# CTF LLM Agent Boilerplate

This project provides a Docker-based framework for developing and evaluating Large Language Model (LLM) agents for Capture The Flag (CTF) competitions. It supports both file-based challenges and complex network-based challenges with multiple containerized services.

## Features

- **Docker-based execution**: Complete isolation and reproducible environments
- **Multi-service challenges**: Deploy web applications, databases, and other services
- **Network-aware agents**: Automatic detection of network vs file-based challenges
- **LLM cost tracking**: Full observability of API usage and costs
- **Automated evaluation**: Batch testing across multiple challenges

## Quickstart

### 1. Prerequisites

- **Docker**: Required for containerized challenge execution
- **uv**: Package manager for Python dependencies

Install uv if you don't have it: https://docs.astral.sh/uv/getting-started/installation/

### 2. Installation

Install dependencies:

```bash
uv sync
```

### 3. Configuration

The agent requires access to an LLM through a LiteLLM-compatible API.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  Edit the `.env` file with your LiteLLM endpoint and API key:
    ```
    LITELLM_BASE_URL="https://your-litellm-proxy-url.com"
    LITELLM_API_KEY="your-litellm-api-key"
    ```

### 4. Running the Evaluation

All challenges now run in Docker containers with automatic resource management.

To evaluate against all challenges:

```bash
uv run eval_agent.py
```

To run a single challenge:

```bash
uv run eval_agent.py --challenge <challenge_name>
```

Examples:
```bash
uv run eval_agent.py --challenge baby_cat              # File-based challenge
uv run eval_agent.py --challenge easy_sql_injection    # Network-based challenge  
```

Results are saved in `eval_results/` with detailed logs, costs, and LLM request tracking.

## Project Structure

```
.
├── agent/
│   └── agent.py           # Main agent with network/file challenge detection
├── challenges/
│   ├── baby_cat/          # File-based challenge example
│   │   ├── artifacts/
│   │   │   └── myfile.txt
│   │   └── challenge.json
│   ├── easy_sql_injection/ # Network-based challenge example
│   │   ├── docker/         # Service container definitions
│   │   │   ├── Dockerfile
│   │   │   └── ...
│   │   ├── artifacts/
│   │   └── challenge.json
│   └── ...
├── docker/
│   └── agent/             # Agent container configuration
│       ├── Dockerfile     # Agent execution environment
│       └── run_agent.py   # Container entry point
├── eval_results/          # Timestamped evaluation results
├── helper/
│   ├── agent_boilerplate.py # Agent interface definition
│   ├── ctf_challenge.py   # Challenge models with service support
│   ├── docker_manager.py  # Docker orchestration and networking
│   └── llm_helper.py      # LLM integration with cost tracking
├── .env                   # Environment configuration (API keys)
├── eval_agent.py          # Main evaluation orchestrator
└── README.md              # This file
```

## How to...

### Implement a Custom Agent

1.  Open `agent/agent.py`.
2.  The file contains a `SimpleAgent` class that implements the `AgentInterface`.
3.  Modify the `solve_challenge` method to implement your own strategy. The agent automatically detects:
    - **File-based challenges**: Access via `challenge.working_folder` with artifacts
    - **Network-based challenges**: Access via `challenge.network_info` with service discovery
4.  Use the `CTFChallengeClient` object for challenge interaction and flag submission.

### Create a File-Based Challenge

1.  Create a new directory in `challenges/` (e.g., `my_challenge/`).
2.  Create `challenge.json`:
    ```json
    {
      "name": "My File Challenge",
      "description": "Find the hidden flag in the provided files.",
      "categories": ["misc", "forensics"],
      "flag": "flag{this_is_the_secret}",
      "flag_regex": "flag\\{\\S+\\}"
    }
    ```
3.  Create `artifacts/` subdirectory with challenge files.

### Create a Network-Based Challenge

1.  Create challenge directory and `challenge.json`:
    ```json
    {
      "name": "My Web Challenge",
      "description": "Exploit the vulnerable web application.",
      "categories": ["web", "sql"],
      "flag": "flag{sql_injection_success}",
      "flag_regex": "flag\\{\\S+\\}",
      "services": [
        {
          "name": "webapp",
          "image": "my-webapp:latest", 
          "ports": {"80/tcp": 8080},
          "environment": {"FLAG": "flag{sql_injection_success}"}
        }
      ]
    }
    ```
2.  Create `docker/` subdirectory with service Dockerfile and application code.
3.  The agent will automatically discover services via Docker networking.

### Monitor LLM Usage and Costs

Each evaluation provides detailed observability:

- **Per-challenge costs**: Individual LLM usage tracking
- **Request IDs**: Full audit trail of API calls  
- **Usage analytics**: Saved in `eval_results/*/llm_usage.json`
- **Batch summaries**: Total costs across multiple challenges


## Architecture

The system uses Docker containers for challenge execution with the following flow:

1. **Challenge Detection**: Automatic identification of file vs network challenges
2. **Service Deployment**: Docker containers for challenge services (if any)  
3. **Network Creation**: Isolated Docker network per challenge
4. **Agent Execution**: Containerized agent with access to services
5. **Result Collection**: LLM usage data and results extracted from containers
6. **Resource Cleanup**: Automatic cleanup of containers and networks

For detailed architecture documentation, see [docs/architecture.md](./docs/architecture.md).
