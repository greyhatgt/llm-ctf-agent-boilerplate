# CTF LLM Agent Boilerplate

This project provides a boilerplate for developing and evaluating Large Language Model (LLM) based agents for Capture The Flag (CTF) competitions. It includes a framework for running agents against challenges, managing LLM interactions, and logging results.

## Quickstart

### 1. Installation

This project uses `uv` for package management. If you don't have it installed, you can find instructions here: https://docs.astral.sh/uv/getting-started/installation/

First, install the dependencies:

```bash
uv sync
```

### 2. Configuration

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

### 3. Running the Evaluation

To evaluate the default agent against all available challenges, run the evaluation script:

```bash
uv run eval_agent.py
```

To run against a single challenge:

```bash
uv run eval_agent.py --challenge <challenge_name>
```
For example:
```bash
uv run eval_agent.py --challenge baby_cat
```

Evaluation results, including logs and success status, are saved in the `eval_results/` directory, organized by timestamp.

### 4. Testing the Agent

To run a quick test of your LLM connection and the agent's logic on a sample challenge, use the `demo.py` script:

```bash
uv run demo.py
```

## Project Structure

```
.
├── agent/
│   └── agent.py           # <-- Main agent logic goes here. Modify this file.
├── challenges/
│   ├── baby_cat/          # Example challenge
│   │   ├── artifacts/
│   │   │   └── myfile.txt
│   │   └── challenge.json
│   └── ...
├── docs/
│   └── architecture.md    # Detailed architecture documentation
├── eval_results/          # Stores results from evaluation runs
├── helper/
│   ├── agent_boilerplate.py # Agent interface definition
│   ├── ctf_challenge.py   # Helper classes for challenges (Grader, Client)
│   └── llm_helper.py      # LiteLLM integration and cost tracking
├── .env                   # Local environment configuration (API keys)
├── .env.example           # Example environment file
├── eval_agent.py          # Main script to run evaluations
├── demo.py                # Script for quick testing and debugging
└── README.md              # This file
```

## How to...

### Implement a Custom Agent

1.  Open `agent/agent.py`.
2.  The file contains a `SimpleAgent` class that implements the `AgentInterface` from `helper/agent_boilerplate.py`.
3.  Modify the `solve_challenge` method to implement your own strategy. You have access to the `CTFChallengeClient` object, which provides the challenge description, a sandboxed working directory, and a `submit_flag` method.

### Create a New Challenge

1.  Create a new directory in `challenges/`. The directory name will be the challenge's identifier.
2.  Inside, create a `challenge.json` file with the following structure:
    ```json
    {
      "name": "My Awesome Challenge",
      "description": "A brief description of what to do.",
      "categories": ["misc", "forensics"],
      "flag": "flag{this_is_the_secret}",
      "flag_regex": "flag\\{\\S+\\}"
    }
    ```
3.  Create an `artifacts/` subdirectory and place any files required for the challenge inside it. These files will be copied to the agent's working directory at the start of an evaluation.

## Architecture

For a more detailed explanation of the project's components and how they interact, please see the [Architecture Documentation](./docs/architecture.md).
