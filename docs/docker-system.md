# Docker-based CTF Agent System

This enhanced version of the CTF LLM Agent now supports running agents in Docker containers and includes support for additional dockerized services that run on the same virtual network as the agent container.

## Key Features

### 1. Dockerized Agent Execution
- Agents run in isolated Docker containers
- Pre-installed with common CTF tools (curl, wget, netcat, nmap, sqlmap)
- Automatic cleanup after execution
- Network isolation for each challenge

### 2. Service Support
- Define additional services in `challenge.json`
- Services run on the same Docker network as the agent
- Automatic image building from `docker/` directory

### 3. Network Isolation
- Each challenge gets its own Docker network
- Services can communicate using container names as hostnames
- Agent can access services at predictable URLs

## Challenge Configuration

### Basic Challenge Structure
```
challenges/my_challenge/
├── challenge.json          # Challenge metadata and services
├── artifacts/             # Files accessible to the agent
│   └── README.md
└── docker/               # Service Docker files (optional)
    ├── Dockerfile
    ├── app.py
    └── templates/
```

### challenge.json with Services
```json
{
    "name": "My Web Challenge",
    "description": "A challenge with a web service",
    "categories": ["web"],
    "flag": "flag{example}",
    "flag_regex": "flag\\{\\S+\\}",
    "services": [
        {
            "name": "webapp",
            "image": "my-webapp:latest",
            "ports": {
                "80/tcp": 8080
            },
            "internal_port": 80,
            "environment": {
                "FLAG": "flag{example}"
            }
        }
    ]
}
```

### Service Configuration Options

#### Required Fields
- `name`: Container name (used as hostname in network)
- `image`: Docker image name
- `internal_port`: Port the service listens on inside the container

#### Optional Fields
- `ports`: Port mapping for external access (host:container)
- `environment`: Environment variables
- `volumes`: Volume mounts

## Agent Capabilities

### Web Challenge Support
The agent automatically detects web challenges and:
1. Performs reconnaissance with curl/wget
2. Identifies vulnerabilities using LLM analysis
3. Executes exploitation commands
4. Extracts flags from responses

### Available Tools in Agent Container
- `curl` - HTTP client
- `wget` - Download tool
- `netcat` (nc) - Network utility
- `nmap` - Network scanner
- `sqlmap` - SQL injection tool
- Python with common libraries

### Network Access
Services are accessible at: `http://service_name:internal_port`

Example: If you have a service named "webapp" on port 80:
```bash
curl http://webapp:80
```

## Running the System

### With Docker (Default)
```bash
python eval_agent.py --challenge easy_sql_injection
```

### Without Docker (Legacy Mode)
```bash
python eval_agent.py --no-docker --challenge baby_cat
```

### Single Challenge
```bash
python eval_agent.py --challenge challenge_name
```

### All Challenges
```bash
python eval_agent.py
```

## Example: SQL Injection Challenge

The included `easy_sql_injection` challenge demonstrates:
- A vulnerable Flask web application
- Custom Docker image building
- SQL injection exploitation
- Flag extraction from admin panel

### Challenge Flow
1. Agent detects web challenge with services
2. Performs web reconnaissance
3. Identifies SQL injection vulnerability
4. Crafts bypass payload: `' OR '1'='1' --`
5. Accesses admin panel and extracts flag

## Development

### Adding New Service Types
1. Create service configuration in `challenge.json`
2. Add Docker files in `docker/` directory
3. Test service startup

### Custom Agent Logic
Update `agent/agent.py` to handle new challenge types:
```python
def solve_challenge(self, challenge: CTFChallengeClient) -> str | None:
    if challenge.network_info and 'services' in challenge.network_info:
        return self._solve_web_challenge(challenge)
    else:
        return self._solve_file_challenge(challenge)
```

### Docker Image Building
Images are built automatically if:
- Service image name doesn't contain '/' or 'localhost'
- `docker/Dockerfile` exists in challenge directory

## Troubleshooting

### Docker Issues
- Ensure Docker is running
- Check Docker permissions
- Verify image build logs in agent output

### Network Issues
- Services start before agent execution
- Use container names as hostnames

### Service Issues
- Check service logs in Docker output
- Verify Dockerfile and application code

## Security Notes

- Containers run in isolated networks
- No persistent data between runs
- Automatic cleanup prevents resource leaks
- Services only accessible within challenge network