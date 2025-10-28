

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


def create_challenge_from_ctfd(base_url: str, api_token: str, challenge_data: Dict):
    """Create a CTFChallenge from CTFd API response"""
    import tempfile
    import requests
    
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    })
    
    # Create temporary artifacts directory
    artifacts_folder = tempfile.mkdtemp(prefix='ctfd_challenge_')
    
    # Download files if they exist
    files = challenge_data.get('files', [])
    if files:
        print(f"Downloading {len(files)} file(s) for {challenge_data.get('name', 'Unknown')}")
        for file_path in files:
            # CTFd file paths are usually relative URLs like "/files/..."
            file_url = base_url + file_path if not file_path.startswith('http') else file_path
            try:
                print(f"Downloading from: {file_url}")
                # Need to use session to maintain auth
                response = session.get(file_url, timeout=30)
                if response.status_code == 200:
                    filename = os.path.basename(file_path)
                    # Remove query string from filename
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    # Handle edge cases where filename might be empty
                    if not filename:
                        filename = f"file_{len(files)}.dat"
                    file_path_local = os.path.join(artifacts_folder, filename)
                    with open(file_path_local, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {filename}")
                else:
                    print(f"Failed to download {file_url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"Error downloading file {file_path}: {e}")
    
    # Extract flag from flags list
    flags = challenge_data.get('flags', [])
    flag = flags[0] if flags else ""
    
    # Determine categories
    category = challenge_data.get('category', 'Misc')
    categories = [category]
    
    # Check if this is a network-based challenge
    connection_info = challenge_data.get('connection_info', '')
    services = []
    # If there's connection_info, treat it as a network challenge
    if connection_info:
        # Create a fake service entry for network challenges
        services = [{
            'name': 'network_challenge',
            'image': 'network',
            'connection_info': connection_info
        }]
    
    challenge = CTFChallenge(
        name=challenge_data.get('name', 'Unknown'),
        description=challenge_data.get('description', ''),
        categories=categories,
        artifacts_folder=artifacts_folder,
        flag=flag,
        flag_regex=r'flag\{.*?\}',
        services=services
    )
    
    return challenge


def get_challenges_from_ctfd(base_url: str, api_token: str, challenge_name: Optional[str] = None) -> List[CTFChallenge]:
    """
    Get challenges from CTFd API
    
    Args:
        base_url: Base URL of CTFd instance
        api_token: API token for authentication
        challenge_name: Optional specific challenge name to fetch
        
    Returns:
        List of CTFChallenge objects
    """
    import requests
    
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    })
    
    try:
        response = session.get(f"{base_url}/api/v1/challenges", timeout=10)
        response.raise_for_status()
        
        challenges_data = response.json().get('data', [])
        challenges = []
        
        for ch_data in challenges_data:
            # If a specific challenge name was provided, allow case-insensitive
            # and partial substring matching to be more user-friendly.
            if challenge_name:
                provided = challenge_name.strip().lower()
                actual = (ch_data.get('name') or '').strip().lower()
                if provided not in actual:
                    continue
            
            try:
                # Get detailed challenge info including files
                ch_id = ch_data.get('id')
                detail_response = session.get(f"{base_url}/api/v1/challenges/{ch_id}", timeout=10)
                if detail_response.status_code == 200:
                    ch_data = detail_response.json().get('data', ch_data)
                
                print(f"Processing challenge: {ch_data.get('name')}, Files: {ch_data.get('files', [])}")
                
                challenge = create_challenge_from_ctfd(base_url, api_token, ch_data)
                # Store CTFd-specific info for later use
                challenge.id = ch_data.get('id')
                challenge.solved = ch_data.get('solved', False)
                challenges.append(challenge)
            except Exception as e:
                print(f"Error creating challenge {ch_data.get('name')}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # If no challenges matched, provide a helpful log message.
        if challenge_name and not challenges:
            print(f"No CTFd challenges matched name '{challenge_name}'. Available: {[c.get('name') for c in challenges_data]}")
        return challenges
    except requests.exceptions.RequestException as e:
        print(f"Error fetching challenges from CTFd: {e}")
        import traceback
        traceback.print_exc()
        return []


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

