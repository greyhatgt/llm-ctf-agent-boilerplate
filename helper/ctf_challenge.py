

from typing import Callable


class CTFChallenge:
    '''
    Data of challenge
    '''
    def __init__(self, name: str, description: str, artifacts_folder: str, flag: str):
        self.name = name
        self.description = description
        self.artifacts_folder = artifacts_folder
        self.flag = flag
        

class CTFChallengeClient:
    '''
    These are the fields that your agent can see
    '''
    def __init__(self, challenge: CTFChallenge, working_folder: str, submit_flag: Callable):
        self.challenge = challenge
        self.working_folder = working_folder
        self.submit_flag = submit_flag

    def submit_flag(self, flag: str):
        if self.submit_flag:
            self.submit_flag(flag)


class CTFChallengeGrader:
    '''
    These are the fields that the grader can see
    '''
    def __init__(self, challenge: CTFChallenge, flag: str):
        self.challenge = challenge
        self.flag = flag
        self.clients = []
        
    def create_client(self, working_folder: str) -> CTFChallengeClient:
        
        def submit_flag(flag: str):
            if flag == self.flag:
                print("Correct flag submitted!")
            else:
                print("Incorrect flag.")
        client = CTFChallengeClient(self.challenge, working_folder, submit_flag)
        self.clients.append(client)
        return client

# TODO: Not immediate priority, but eventually integrate with CTFd and similar platforms' APIs
# Need to fetch challenges, submit flags, ...

