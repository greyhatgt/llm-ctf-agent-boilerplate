

import os
import shutil
import json
import yaml
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
    
    # Try to load challenge.json first, then challenge.yml
    challenge_json_path = os.path.join(chaldir, "challenge.json")
    challenge_yml_path = os.path.join(chaldir, "challenge.yml")
    
    data = None
    if os.path.exists(challenge_json_path):
        with open(challenge_json_path, 'r') as f:
            data = json.load(f)
    elif os.path.exists(challenge_yml_path):
        with open(challenge_yml_path, 'r') as f:
            yml_data = yaml.safe_load(f)
            # Convert YAML format to JSON format
            data = {}
            data["name"] = yml_data.get("name", "")
            data["description"] = yml_data.get("description", "")
            # Convert category (singular) to categories (list)
            category = yml_data.get("category", "Misc")
            data["categories"] = [category] if isinstance(category, str) else category
            # Convert flags (list) to flag (string) - take first flag
            flags = yml_data.get("flags", [])
            if flags:
                data["flag"] = flags[0] if isinstance(flags, list) else flags
            else:
                data["flag"] = ""
            # Generate flag_regex from flag if not provided
            if data["flag"]:
                # Extract flag content between {} if present
                flag_content = data["flag"]
                if "{" in flag_content and "}" in flag_content:
                    data["flag_regex"] = "flag\\{\\S+\\}"
                else:
                    data["flag_regex"] = "flag\\{\\S+\\}"
            else:
                data["flag_regex"] = "flag\\{\\S+\\}"
            # Load services if present (YAML might have connection_info or services)
            if "services" in yml_data:
                data["services"] = yml_data["services"]
            elif "connection_info" in yml_data:
                # Convert connection_info to a service if needed
                conn_info = yml_data["connection_info"]
                # Parse connection_info like "nc HOST PORT" or just store it
                data["services"] = []  # Could parse connection_info here if needed
            else:
                data["services"] = []
    else:
        raise FileNotFoundError(f"Neither challenge.json nor challenge.yml found in {chaldir}")
    
    required_fields = ["name", "description", "categories", "flag", "flag_regex"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in challenge file")
    
    # Check for artifacts folder, create if it doesn't exist
    artifacts_folder = os.path.join(chaldir, "artifacts")
    if not os.path.isdir(artifacts_folder):
        # Try to create it, but don't fail if we can't
        try:
            os.makedirs(artifacts_folder, exist_ok=True)
        except:
            pass
        # If still doesn't exist, that's okay - some challenges might not have artifacts
    
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

