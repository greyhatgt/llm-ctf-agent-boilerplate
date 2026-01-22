"""
CTFTime Integration - Helper methods to get challenges from active CTFTime endpoints
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
from helper.legacy_ctf_challenge import CTFdClient, CTFdChallenge


class CTFTimeEndpoint:
    """Represents a CTF event from CTFTime"""
    
    def __init__(self, event_data: Dict):
        self.event_data = event_data
        self.id = event_data.get('id')
        self.title = event_data.get('title', '')
        self.url = event_data.get('url', '')
        self.ctftime_url = f"https://ctftime.org/event/{self.id}"
        self.start = event_data.get('start', '')
        self.finish = event_data.get('finish', '')
        self.format = event_data.get('format', '')
        self.logo = event_data.get('logo', '')
        self.organizers = event_data.get('organizers', [])
        self.onsite = event_data.get('onsite', False)
        self.weight = event_data.get('weight', 0.0)
    
    def is_active(self) -> bool:
        """Check if event is currently active"""
        try:
            start = datetime.fromisoformat(self.start.replace('Z', '+00:00'))
            finish = datetime.fromisoformat(self.finish.replace('Z', '+00:00'))
            now = datetime.now(start.tzinfo if start.tzinfo else finish.tzinfo)
            return start <= now <= finish
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.event_data


class CTFTimeHelper:
    """Helper for CTFTime API operations"""
    
    BASE_URL = "https://ctftime.org/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CTF-Agent-Solver/1.0'
        })
    
    def get_active_events(self, limit: int = 10, days_ahead: int = 7) -> List[CTFTimeEndpoint]:
        """
        Get currently active CTF events
        
        Args:
            limit: Maximum number of events to return
            days_ahead: Number of days ahead to include
            
        Returns:
            List of active CTFTimeEndpoint objects
        """
        try:
            params = {'limit': limit * 3}
            response = self.session.get(
                f"{self.BASE_URL}/events/",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            events_data = response.json()
            if isinstance(events_data, dict):
                events_data = events_data.get('results', [])
            elif not isinstance(events_data, list):
                events_data = []
            
            active_events = []
            current_time = datetime.now()
            
            for event_data in events_data:
                try:
                    event = CTFTimeEndpoint(event_data)
                    if event.is_active():
                        active_events.append(event)
                        if len(active_events) >= limit:
                            break
                except Exception as e:
                    print(f"Error processing event: {e}")
                    continue
            
            return active_events
        except requests.exceptions.RequestException as e:
            print(f"Error fetching active events: {e}")
            return []
    
    def get_event_details(self, event_id: int) -> Optional[Dict]:
        """Get detailed info about an event"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/events/{event_id}/",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching event details: {e}")
            return None
    
    def get_challenges_for_ctfd_event(self, event_url: str, api_token: str) -> List[CTFdChallenge]:
        """
        Get challenges from a CTFd event listed on CTFTime
        
        Args:
            event_url: URL of the CTF event
            api_token: API token for the CTFd instance
            
        Returns:
            List of CTFdChallenge objects
        """
        # Try to extract base URL from event URL
        if not event_url:
            return []
        
        # Handle different URL formats
        base_url = event_url
        if '/login' in base_url:
            base_url = base_url.split('/login')[0]
        if '/challenges' in base_url:
            base_url = base_url.split('/challenges')[0]
        
        # Try to connect to CTFd API
        try:
            client = CTFdClient(base_url, api_token)
            return client.get_challenges()
        except Exception as e:
            print(f"Error fetching challenges from {base_url}: {e}")
            return []
    
    def discover_ctf_platform(self, event_url: str) -> Optional[str]:
        """Discover what CTF platform is running at an event URL"""
        if not event_url:
            return None
        
        try:
            # Try CTFd
            response = self.session.get(f"{event_url}/api/v1/scoreboard", timeout=5)
            if response.status_code == 200:
                return 'ctfd'
        except:
            pass
        
        try:
            # Try checking for common endpoints
            response = self.session.get(f"{event_url}/api/v1/challenges", timeout=5)
            if response.status_code == 200:
                return 'ctfd'
        except:
            pass
        
        # Could add more platform detection here
        
        return None
    
    def get_top_teams(self, event_id: int, limit: int = 10) -> List[Dict]:
        """Get top teams for an event"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/events/{event_id}/results/",
                params={'limit': limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching top teams: {e}")
            return []


def get_active_challenges_from_ctftime(base_url: Optional[str] = None, 
                                      api_token: Optional[str] = None,
                                      limit: int = 10) -> List[CTFdChallenge]:
    """
    Get active challenges from CTFTime events
    
    Args:
        base_url: Base URL of your CTFd instance (if syncing)
        api_token: API token for CTFd (if syncing)
        limit: Number of active events to check
        
    Returns:
        List of challenges from active CTFTime events
    """
    helper = CTFTimeHelper()
    
    if base_url and api_token:
        # Fetch challenges from specific CTFd instance
        try:
            client = CTFdClient(base_url, api_token)
            return client.get_challenges()
        except Exception as e:
            print(f"Error fetching challenges: {e}")
            return []
    else:
        # Just return event metadata
        events = helper.get_active_events(limit)
        challenges = []
        
        for event in events:
            # In a real implementation, you'd fetch challenges from each event
            # For now, return events as "challenges"
            challenge_data = {
                'name': f"Event: {event.title}",
                'category': 'CTFTime Event',
                'description': f"Active CTF event: {event.title}",
                'value': 0,
                'solves': 0,
                'solved': False,
                'id': event.id,
                'connection_info': f"URL: {event.url}"
            }
            challenges.append(CTFdChallenge(challenge_data))
        
        return challenges


# Convenience functions

def sync_ctftime_to_local(ctftime_url: str, local_ctfd_url: str, local_api_token: str):
    """
    Sync challenges from a CTFTime event to local CTFd instance
    This would require the actual implementation based on the CTF platform
    """
    helper = CTFTimeHelper()
    
    # Discover platform
    platform = helper.discover_ctf_platform(ctftime_url)
    if platform == 'ctfd':
        # Get challenges from the event
        challenges = helper.get_challenges_for_ctfd_event(ctftime_url, local_api_token)
        
        # Could add logic here to sync/import challenges to local CTFd
        print(f"Found {len(challenges)} challenges to sync")
        
    else:
        print(f"Unknown or unsupported platform: {platform}")


if __name__ == "__main__":
    # Example usage
    print("Fetching active CTFTime events...")
    helper = CTFTimeHelper()
    active_events = helper.get_active_events(limit=5)
    
    for event in active_events:
        print(f"\n{event.title}")
        print(f"  URL: {event.url}")
        print(f"  Starts: {event.start}")
        print(f"  Ends: {event.finish}")
        print(f"  Format: {event.format}")
        print(f"  Weight: {event.weight}")

