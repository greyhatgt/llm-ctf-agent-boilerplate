
from abc import abstractmethod
import logging
from helper.ctf_challenge import CTFChallengeClient

class AgentInterface:
    logger: logging.Logger | None = None

    def log(self, message: str, level: int = logging.INFO):
        '''
        Log a message if a logger is set.
        '''
        if self.logger:
            self.logger.log(level, message)

    @abstractmethod
    def solve_challenge(self, challenge: CTFChallengeClient) -> str | None:
        '''
        Solve the given CTF challenge.
        Return the flag if solved, otherwise return None.
        '''
        pass
