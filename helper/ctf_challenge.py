

import os
import shutil
from typing import Callable, List, Dict, Optional, Any


class CTFChallenge:
    """
    Challenge data container with Docker service support.
    
    Represents a CTF challenge with metadata and optional containerized services.
    Supports both file-based challenges (with artifacts) and network-based 
    challenges (with deployed services).
    """
    def __init__(self, name: str, description: str, categories: list[str], artifacts_folder: str, flag: str, flag_regex: str, services: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self.description = description
        self.categories = categories
        self.artifacts_folder = artifacts_folder
        self.flag = flag
        self.flag_regex = flag_regex
        self.services = services or []

    def __str__(self) -> str:
        return f"CTFChallenge(name={self.name}, description={self.description}, categories={self.categories}, artifacts_folder={self.artifacts_folder}, flag_regex={self.flag_regex}, services={len(self.services)} services)"
    def __repr__(self) -> str:
        return self.__str__()


class CTFChallengeClient:
    """
    Agent interface to challenge with Docker network awareness.
    
    Provides agents with:
    - Challenge metadata and artifacts access
    - Flag submission interface
    - Network information for service-based challenges
    - Working directory for temporary files
    """
    def __init__(self, challenge: CTFChallenge, working_folder: str, submit_flag: Callable[[str], bool], network_info: Optional[Dict[str, Any]] = None):
        self.challenge = challenge
        self.working_folder = working_folder
        self.network_info = network_info or {}
        if os.path.exists(working_folder):
            shutil.rmtree(working_folder)
        shutil.copytree(challenge.artifacts_folder, working_folder)
        self._submit_flag_callback = submit_flag

    def __str__(self) -> str:
        return f"CTFChallengeClient(challenge={self.challenge}, working_folder={self.working_folder}, network_info={self.network_info})"

    def __repr__(self) -> str:
        return self.__str__()

    def submit_flag(self, flag: str):
        return self._submit_flag_callback(flag)


class CTFChallengeGrader:
    '''
    These are the fields that the grader can see
    '''
    def __init__(self, challenge: CTFChallenge):
        self.challenge = challenge
        self.clients = []
        
    def __str__(self) -> str:
        return f"CTFChallengeGrader(challenge={self.challenge}, clients={self.clients})"
    def __repr__(self) -> str:
        return self.__str__()
        
    def create_client(self, working_folder: str, network_info: Optional[Dict[str, Any]] = None) -> CTFChallengeClient:
        
        def submit_flag(flag: str) -> bool:
            if flag == self.challenge.flag:
                return True
            else:
                return False
        
        client = CTFChallengeClient(self.challenge, working_folder, submit_flag, network_info)
        self.clients.append(client)
        return client
    
    

# TODO: Integrate with CTFd and similar platforms' APIs


def create_challenge_from_chaldir(chaldir: str):
    import json
    challenge_json_path = os.path.join(chaldir, "challenge.json")
    if not os.path.exists(challenge_json_path):
        raise FileNotFoundError(f"challenge.json not found in {chaldir}")
    
    with open(challenge_json_path, 'r') as f:
        data = json.load(f)
    
    required_fields = ["name", "description", "categories", "flag", "flag_regex"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in challenge.json")
    
    artifacts_folder = os.path.join(chaldir, "artifacts")
    if not os.path.isdir(artifacts_folder):
        raise FileNotFoundError(f"Artifacts folder 'artifacts' not found in {chaldir}")
    
    # Load services if present
    services = data.get("services", [])
    
    challenge = CTFChallenge(
        name=data["name"],
        description=data["description"],
        categories=data["categories"],
        artifacts_folder=artifacts_folder,
        flag=data["flag"],
        flag_regex=data["flag_regex"],
        services=services
    )
    
    return challenge

