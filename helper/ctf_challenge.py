

import os
import shutil
from typing import Callable


class CTFChallenge:
    '''
    Data of challenge
    '''
    def __init__(self, name: str, description: str, categories: list[str], artifacts_folder: str, flag: str, flag_regex: str):
        self.name = name
        self.description = description
        self.categories = categories
        self.artifacts_folder = artifacts_folder
        self.flag = flag
        self.flag_regex = flag_regex

    def __str__(self) -> str:
        return f"CTFChallenge(name={self.name}, description={self.description}, categories={self.categories}, artifacts_folder={self.artifacts_folder}, flag_regex={self.flag_regex})"
    def __repr__(self) -> str:
        return self.__str__()


class CTFChallengeClient:
    '''
    These are the fields that your agent can see
    '''
    def __init__(self, challenge: CTFChallenge, working_folder: str, submit_flag: Callable[[str], bool]):
        self.challenge = challenge
        self.working_folder = working_folder
        if os.path.exists(working_folder):
            shutil.rmtree(working_folder)
        shutil.copytree(challenge.artifacts_folder, working_folder)
        self._submit_flag_callback = submit_flag

    def __str__(self) -> str:
        return f"CTFChallengeClient(challenge={self.challenge}, working_folder={self.working_folder})"

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
        
    def create_client(self, working_folder: str) -> CTFChallengeClient:
        
        def submit_flag(flag: str) -> bool:
            if flag == self.challenge.flag:
                return True
            else:
                return False
        
        client = CTFChallengeClient(self.challenge, working_folder, submit_flag)
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
    
    challenge = CTFChallenge(
        name=data["name"],
        description=data["description"],
        categories=data["categories"],
        artifacts_folder=artifacts_folder,
        flag=data["flag"],
        flag_regex=data["flag_regex"]
    )
    
    return challenge

