
from abc import abstractmethod
import logging
from helper.ctf_challenge import CTFChallengeClient

class AgentInterface:
    logger: logging.Logger | None = None

    def log(self, message: str):
        if self.logger:
            self.logger.info(message)

    @abstractmethod
    def solve_challenge(self, challenge: CTFChallengeClient):
        # Implement your challenge-solving logic here
        pass
