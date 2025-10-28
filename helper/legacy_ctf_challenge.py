"""
CTF Agent Base Classes - Compatible with CTFTime and CTFd
Implements classes from llm-ctf-agent-boilerplate for CTFTime integration
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from datetime import datetime


@dataclass
class ChallengeFiles:
    """Represents downloadable files for a challenge"""
    name: str
    url: str
    size: Optional[int] = None
    type: Optional[str] = None


@dataclass
class ChallengeHint:
    """Represents a hint for a challenge"""
    content: str
    cost: Optional[int] = None
    purchased: bool = False


class CTFChallenge(ABC):
    """
    Base class for CTF challenges
    Compatible with both CTFd and CTFTime
    """
    
    def __init__(self, challenge_data: Dict[str, Any]):
        self.data = challenge_data
        self.name = challenge_data.get('name', 'Unknown')
        self.category = challenge_data.get('category', 'Misc')
        self.description = challenge_data.get('description', '')
        self.value = challenge_data.get('value', 0)
        self.solves = challenge_data.get('solves', 0)
        self.solved = challenge_data.get('solved', False)
        
    @abstractmethod
    def get_files(self) -> List[ChallengeFiles]:
        """Get downloadable files for this challenge"""
        pass
    
    @abstractmethod
    def get_hints(self) -> List[ChallengeHint]:
        """Get hints for this challenge"""
        pass
    
    @abstractmethod
    def get_connection_info(self) -> str:
        """Get connection information (host, port, etc.)"""
        pass
    
    @abstractmethod
    def submit_flag(self, flag: str) -> bool:
        """Submit a flag for this challenge"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert challenge to dictionary"""
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'value': self.value,
            'solves': self.solves,
            'solved': self.solved,
        }


class CTFdChallenge(CTFChallenge):
    """CTFd-specific challenge implementation"""
    
    def __init__(self, challenge_data: Dict[str, Any], api_client=None):
        super().__init__(challenge_data)
        self.id = challenge_data.get('id')
        self.api_client = api_client
        self.connection_info = challenge_data.get('connection_info', '')
        
        # Parse files
        self._files = []
        for file_path in challenge_data.get('files', []):
            self._files.append(ChallengeFiles(
                name=file_path.split('/')[-1],
                url=file_path if file_path.startswith('http') else f"{self.api_client.base_url if api_client else ''}{file_path}",
            ))
        
        # Parse hints
        self._hints = []
        for hint_data in challenge_data.get('hints', []):
            self._hints.append(ChallengeHint(
                content=hint_data.get('content', ''),
                cost=hint_data.get('cost', 0),
                purchased=hint_data.get('purchased', False)
            ))
    
    def get_files(self) -> List[ChallengeFiles]:
        """Get downloadable files"""
        return self._files
    
    def get_hints(self) -> List[ChallengeHint]:
        """Get hints"""
        if not self.api_client:
            return self._hints
        return self.api_client.get_challenge_hints(self.id)
    
    def get_connection_info(self) -> str:
        """Get connection info"""
        return self.connection_info
    
    def submit_flag(self, flag: str) -> bool:
        """Submit a flag"""
        if not self.api_client:
            return False
        return self.api_client.submit_flag(self.id, flag)


class CTFTimeChallenge(CTFChallenge):
    """CTFTime-specific challenge implementation"""
    
    def __init__(self, challenge_data: Dict[str, Any]):
        super().__init__(challenge_data)
        self.event_id = challenge_data.get('event_id')
        self.ctf_url = challenge_data.get('ctf_url', '')
        
    def get_files(self) -> List[ChallengeFiles]:
        """Files would be from the CTF event itself"""
        # In practice, need to scrape or access CTF platform API
        return []
    
    def get_hints(self) -> List[ChallengeHint]:
        """Hints from CTFTime event"""
        return []
    
    def get_connection_info(self) -> str:
        """Get CTF event connection info"""
        return f"Event: {self.ctf_url}"
    
    def submit_flag(self, flag: str) -> bool:
        """Flags go through the actual CTF platform, not CTFTime"""
        raise NotImplementedError("Submit through the actual CTF platform")


class CTFdClient:
    """Client for CTFd instances"""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        })
    
    def get_challenges(self) -> List[CTFdChallenge]:
        """Get all challenges from CTFd"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/challenges", timeout=10)
            response.raise_for_status()
            challenges = []
            
            for ch_data in response.json().get('data', []):
                ch_data['api_client'] = self
                challenges.append(CTFdChallenge(ch_data, self))
            
            return challenges
        except requests.exceptions.RequestException as e:
            print(f"Error fetching challenges: {e}")
            return []
    
    def get_challenge(self, challenge_id: int) -> Optional[CTFdChallenge]:
        """Get specific challenge by ID"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/challenges/{challenge_id}",
                timeout=10
            )
            response.raise_for_status()
            
            ch_data = response.json().get('data', {})
            ch_data['api_client'] = self
            return CTFdChallenge(ch_data, self)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching challenge: {e}")
            return None
    
    def submit_flag(self, challenge_id: int, flag: str) -> bool:
        """Submit a flag for a challenge"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/challenges/attempt",
                json={
                    'challenge_id': challenge_id,
                    'submission': flag
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json().get('data', {})
            return data.get('status') == 'correct'
        except requests.exceptions.RequestException as e:
            print(f"Error submitting flag: {e}")
            return False
    
    def get_challenge_hints(self, challenge_id: int) -> List[ChallengeHint]:
        """Get hints for a challenge"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/challenges/{challenge_id}",
                timeout=10
            )
            response.raise_for_status()
            
            ch_data = response.json().get('data', {})
            hints = []
            for hint_data in ch_data.get('hints', []):
                hints.append(ChallengeHint(
                    content=hint_data.get('content', ''),
                    cost=hint_data.get('cost', 0),
                    purchased=hint_data.get('purchased', False)
                ))
            return hints
        except requests.exceptions.RequestException as e:
            print(f"Error fetching hints: {e}")
            return []


class CTFTimeHelper:
    """Helper for CTFTime API integration"""
    
    BASE_URL = "https://ctftime.org/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CTF-Agent-Solver/1.0'
        })
    
    def get_active_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get currently active CTF events"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/events/",
                params={'limit': limit},
                timeout=10
            )
            response.raise_for_status()
            
            events = response.json()
            active_events = []
            current_time = datetime.now()
            
            for event in events:
                try:
                    start = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00'))
                    finish = datetime.fromisoformat(event.get('finish', '').replace('Z', '+00:00'))
                    
                    if start <= current_time <= finish:
                        active_events.append(event)
                except Exception:
                    continue
            
            return active_events[:limit]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching active events: {e}")
            return []
    
    def get_challenges_for_event(self, event_id: int) -> List[Dict[str, Any]]:
        """
        Get challenges for a CTF event
        Note: CTFTime doesn't provide challenge details directly
        You would need to integrate with each CTF platform's API
        """
        # This would need to be implemented per CTF platform
        # Examples: CTFd, rCTF, CyberChef CTFs, etc.
        pass
    
    def discover_platform(self, event_url: str) -> Optional[str]:
        """Discover the CTF platform for an event"""
        # Try to detect CTFd, rCTF, etc.
        try:
            response = requests.get(event_url, timeout=5, allow_redirects=True)
            if 'CTFd' in response.text or '/api/v1/' in event_url:
                return 'ctfd'
            if 'rCTF' in response.text:
                return 'rctf'
        except:
            pass
        return None


def get_challenges_from_ctfd(base_url: str, api_token: str) -> List[CTFdChallenge]:
    """Convenience function to get challenges from CTFd"""
    client = CTFdClient(base_url, api_token)
    return client.get_challenges()


def get_active_ctftime_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function to get active CTFTime events"""
    helper = CTFTimeHelper()
    return helper.get_active_events(limit)
