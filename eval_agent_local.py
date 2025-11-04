import argparse
import os
import json
import logging
import time
import requests
import dotenv
import tempfile
import shutil
from datetime import datetime

from helper.ctf_challenge import CTFChallenge
from helper.llm_helper import LiteLLMManager
from helper.docker_manager import DockerManager

# Load environment variables
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_ctfd_challenge_id(challenge_name, api_token, base_url="http://localhost:8000"):
    """Get CTFd challenge ID by name"""
    if not api_token:
        return None
    
    try:
        headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f"{base_url}/api/v1/challenges",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                for ch in data['data']:
                    if ch.get('name') == challenge_name:
                        return ch.get('id')
        return None
    except Exception as e:
        logging.warning(f"Could not fetch challenge ID from CTFd: {e}")
        return None

def fetch_ctfd_challenge(challenge_id, api_token, base_url="http://localhost:8000"):
    """Fetch challenge details from CTFd API"""
    if not api_token:
        return None
    
    try:
        headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f"{base_url}/api/v1/challenges/{challenge_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                return data['data']
        return None
    except Exception as e:
        logging.warning(f"Could not fetch challenge from CTFd: {e}")
        return None

def download_ctfd_challenge_files(challenge_data, api_token, base_url="http://localhost:8000", output_dir=None):
    """Download challenge files from CTFd to a directory"""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ctfd_files_")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # If no files, return empty directory
    if not challenge_data or 'files' not in challenge_data or not challenge_data.get('files'):
        logging.info("No files attached to this challenge")
        return output_dir
    
    headers = {
        'Authorization': f'Token {api_token}',
    }
    
    files_downloaded = 0
    # Download each file
    for file_path in challenge_data.get('files', []):
        try:
            # Extract filename from path (remove query parameters like ?token=...)
            file_path_clean = file_path.split('?')[0]  # Remove query string
            filename = os.path.basename(file_path_clean) or "file"
            
            # Try direct file download endpoint first (most reliable)
            # CTFd file paths include tokens, so use the full path
            direct_url = f"{base_url}{file_path}"
            file_response = requests.get(direct_url, headers=headers, timeout=30, stream=True)
            
            if file_response.status_code == 200:
                file_output_path = os.path.join(output_dir, filename)
                with open(file_output_path, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logging.info(f"Downloaded file: {filename}")
                files_downloaded += 1
            else:
                # Try parsing numeric file_id as fallback (for API endpoint)
                file_id = None
                if '/files/' in file_path_clean:
                    parts = file_path_clean.split('/files/')
                    if len(parts) > 1:
                        file_id_part = parts[1].split('/')[0]
                        try:
                            file_id = int(file_id_part)
                        except ValueError:
                            pass  # Not a numeric ID, which is fine
                
                if file_id:
                    # Try API endpoint as fallback
                    file_url = f"{base_url}/api/v1/files/{file_id}"
                    file_response = requests.get(file_url, headers=headers, timeout=30, stream=True)
                    
                    if file_response.status_code == 200:
                        file_output_path = os.path.join(output_dir, filename)
                        with open(file_output_path, 'wb') as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        logging.info(f"Downloaded file via API: {filename}")
                        files_downloaded += 1
                    else:
                        logging.warning(f"Failed to download file {file_path}: HTTP {file_response.status_code}")
                else:
                    logging.warning(f"Failed to download file {file_path}: HTTP {file_response.status_code}")
        except Exception as e:
            logging.warning(f"Failed to download file {file_path}: {e}")
    
    logging.info(f"Downloaded {files_downloaded} file(s) from CTFd")
    return output_dir

def create_challenge_from_ctfd(challenge_data, artifacts_folder):
    """Create CTFChallenge object from CTFd API data"""
    # Map CTFd challenge data to our challenge format
    # CTFd uses: name, description, category (single string), value, state, etc.
    categories = [challenge_data.get('category', '')] if challenge_data.get('category') else []
    
    # Flag regex - default pattern
    flag_regex = challenge_data.get('flag_regex', r'flag\{.*\}')
    
    # Services - check if challenge has network/deployment info
    services = challenge_data.get('services', []) or []
    
    challenge = CTFChallenge(
        name=challenge_data.get('name', 'Unknown'),
        description=challenge_data.get('description', ''),
        categories=categories,
        artifacts_folder=artifacts_folder,
        flag='',  # Flag is not in challenge data (it's hidden)
        flag_regex=flag_regex,
        services=services
    )
    
    return challenge

def evaluate_challenge(challenge_name, llm_manager, run_output_dir, run_timestamp):
    """Evaluate a challenge from CTFd"""
    logging.info(f"--- Running evaluation for challenge: {challenge_name} ---")

    challenge_output_dir = os.path.join(run_output_dir, challenge_name)
    os.makedirs(challenge_output_dir)

    docker_manager = None
    temp_artifacts_dir = None
    try:
        api_token = os.environ.get('CTFD_API_TOKEN')
        base_url = os.environ.get('CTFD_URL', 'http://localhost:8000')
        
        # Fetch challenge from CTFd
        if not api_token:
            logging.error("CTFD_API_TOKEN not found in environment. Please ensure you have run start_ctfd.py first.")
            raise ValueError("CTFD_API_TOKEN required")
        
        ctfd_challenge_id = get_ctfd_challenge_id(challenge_name, api_token, base_url)
        if not ctfd_challenge_id:
            logging.error(f"Could not find challenge '{challenge_name}' in CTFd")
            raise ValueError(f"Challenge '{challenge_name}' not found in CTFd")
        
        logging.info(f"Found CTFd challenge ID: {ctfd_challenge_id}")
        
        # Fetch challenge data from CTFd
        challenge_data_ctfd = fetch_ctfd_challenge(ctfd_challenge_id, api_token, base_url)
        if not challenge_data_ctfd:
            raise ValueError(f"Failed to fetch challenge data from CTFd for ID {ctfd_challenge_id}")
        
        logging.info(f"Fetched challenge '{challenge_data_ctfd.get('name')}' from CTFd")
        logging.info(f"Challenge description: {challenge_data_ctfd.get('description', '')[:100]}...")
        logging.info(f"Challenge files: {challenge_data_ctfd.get('files', [])}")
        
        # Download challenge files to temp directory for Docker mount
        temp_artifacts_dir = download_ctfd_challenge_files(challenge_data_ctfd, api_token, base_url)
        logging.info(f"Challenge files downloaded to: {temp_artifacts_dir}")
        
        # Also save downloaded files to eval_results folder for review
        artifacts_save_dir = os.path.join(challenge_output_dir, "artifacts_from_ctfd")
        os.makedirs(artifacts_save_dir, exist_ok=True)
        if os.path.isdir(temp_artifacts_dir) and os.path.exists(temp_artifacts_dir):
            for item in os.listdir(temp_artifacts_dir):
                src = os.path.join(temp_artifacts_dir, item)
                dst = os.path.join(artifacts_save_dir, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    logging.info(f"Saved downloaded file to eval_results: {item}")
        
        # Create challenge object from CTFd data
        challenge = create_challenge_from_ctfd(challenge_data_ctfd, temp_artifacts_dir)
        
        # Try to merge service information from local challenge.json if it exists
        # This allows services to be defined locally even when fetching from CTFd
        # Try multiple naming conventions to find the local challenge directory
        challenge_name_normalized = challenge_name.lower().strip()
        possible_dirs = [
            os.path.join("challenges", challenge_name_normalized.replace(" ", "-")),
            os.path.join("challenges", challenge_name_normalized.replace(" ", "_")),
            os.path.join("challenges", challenge_name_normalized),
            os.path.join("challenges", challenge_name),
        ]
        
        # Also try exact case match
        for alt_dir in [
            os.path.join("challenges", challenge_name),
        ]:
            if alt_dir not in possible_dirs:
                possible_dirs.append(alt_dir)
        
        local_challenge_dir = None
        for alt_dir in possible_dirs:
            if os.path.exists(alt_dir):
                local_challenge_dir = alt_dir
                break
        
        if local_challenge_dir:
            local_challenge_json = os.path.join(local_challenge_dir, "challenge.json")
        else:
            local_challenge_json = None
        
        if local_challenge_json and os.path.exists(local_challenge_json):
            try:
                with open(local_challenge_json, 'r') as f:
                    local_data = json.load(f)
                local_services = local_data.get("services", [])
                if local_services:
                    logging.info(f"Found local challenge.json with {len(local_services)} service(s), merging service definitions")
                    challenge.services = local_services
            except Exception as e:
                logging.warning(f"Could not load local challenge.json: {e}")
        
        # Store local_challenge_dir for later use in building service images
        challenge._local_challenge_dir = local_challenge_dir
        
        # Setup Docker environment for all challenges
        docker_manager = DockerManager(logging.getLogger(f"docker_{challenge_name}"))
        # Sanitize challenge name for network name (replace spaces and underscores with hyphens)
        sanitized_network_name = challenge_name.lower().replace(' ', '-').replace('_', '-')
        network_name = f"ctf-network-{sanitized_network_name}"
        network_id = docker_manager.create_network(network_name)
        
        # Start any additional services using simplified approach
        services_deployed = []
        services_info = []  # Store service details (name, port, etc.)
        for service in challenge.services:
            # Build custom service image if needed
            image_name = service['image']
            docker_path = None
            
            # In CTFd mode, try to find local docker directory for building
            # We stored it earlier when merging service definitions
            local_challenge_dir = getattr(challenge, '_local_challenge_dir', None)
            if local_challenge_dir:
                docker_path = os.path.join(local_challenge_dir, 'docker')
            
            # Build the image if docker directory exists
            if docker_path and os.path.exists(docker_path) and os.path.exists(os.path.join(docker_path, 'Dockerfile')):
                logging.info(f"Building custom image: {image_name} from {docker_path}")
                docker_manager.client.images.build(
                    path=docker_path,
                    tag=image_name,
                    rm=True,
                    forcerm=True
                )
                logging.info(f"Successfully built custom image: {image_name}")
            else:
                # In CTFd mode, if we can't build locally, try to use existing image or fail
                logging.warning(f"Could not find local docker directory for {image_name}, trying to use existing image")
            
            # Start the service container
            docker_manager.start_container(
                image=image_name,
                name=service['name'],
                network=network_name,
                environment=service.get('environment', {}),
                ports=service.get('ports', {})
            )
            services_deployed.append(service['name'])
            
            # Store service info including port
            service_info = {
                'name': service['name'],
                'port': service.get('internal_port', None)
            }
            services_info.append(service_info)
            
            # Simple wait for service to be ready (replace health checks)
            time.sleep(3)
            logging.info(f"Service {service['name']} is ready")
        
        # Only create network_info if services were deployed
        network_info = None
        if services_deployed:
            network_info = {
                'network_name': network_name,
                'network_id': network_id,
                'services_deployed': services_deployed,
                'services': services_info  # Include detailed service information
            }
        
        # Build and run agent in Docker
        image_tag = docker_manager.build_agent_image(challenge_name)
        
        # Prepare challenge data for Docker
        challenge_data = {
            'name': challenge.name,
            'description': challenge.description,
            'categories': challenge.categories,
            'artifacts_folder': challenge.artifacts_folder,
            'flag': '',  # Don't pass flag in CTFd mode
            'flag_regex': challenge.flag_regex,
            'network_info': network_info
        }
        
        # Prepare CTFd environment variables
        # Replace localhost with host.docker.internal so the container can reach the host
        # This allows the agent container to access CTFd running on the host
        docker_ctfd_url = base_url.replace('localhost', 'host.docker.internal').replace('127.0.0.1', 'host.docker.internal')
        ctfd_environment = {
            'CTFD_API_TOKEN': api_token,
            'CTFD_URL': docker_ctfd_url,
            'CTFD_CHALLENGE_ID': str(ctfd_challenge_id)
        }
        logging.info(f"Using CTFd URL for Docker container: {docker_ctfd_url}")
        
        start_time = time.time()
        
        docker_result = docker_manager.run_agent(challenge_data, network_name, challenge_output_dir, image_tag, environment=ctfd_environment)
        
        end_time = time.time()
        
        # Extract results and LLM usage data from container
        found_flag = docker_result['result'].get('found_flag')
        container_success = docker_result['result'].get('success', False)
        container_request_ids = docker_result['result'].get('llm_request_ids', [])
        container_cost = docker_result['result'].get('llm_cost', 0.0)
        
        # Save Docker logs
        with open(os.path.join(challenge_output_dir, "agent.log"), "w", encoding="utf-8") as f:
            f.write(docker_result['logs'])

        # Use container's LLM usage data instead of host-level tracking
        challenge_request_ids = container_request_ids
        challenge_cost = container_cost

        duration = end_time - start_time
        
        # Use success from container (which handles CTFd API response vs local comparison)
        success = container_success

        logging.info(f"Challenge: {challenge_name}, Success: {success}, Time: {duration:.2f}s, Cost: ${challenge_cost:.6f}")

        result_data = {
            "challenge_name": challenge.name,
            "success": success,
            "submitted_flag": found_flag,
            "correct_flag": "hidden",
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration": duration,
            "cost": challenge_cost,
            "llm_request_ids": challenge_request_ids,
            "network_info": network_info,
        }

        with open(os.path.join(challenge_output_dir, "result.json"), "w") as f:
            json.dump(result_data, f, indent=4)
        
        return result_data

    except Exception as e:
        logging.error(f"Failed to run evaluation for {challenge_name}: {e}", exc_info=True)
        error_data = {
            "challenge_name": challenge_name,
            "success": False,
            "error": str(e),
        }
        with open(os.path.join(challenge_output_dir, "result.json"), "w") as f:
            json.dump(error_data, f, indent=4)
        return error_data
    finally:
        # Cleanup Docker resources
        if docker_manager:
            docker_manager.cleanup()
        # Cleanup temporary artifacts directory if created from CTFd
        if temp_artifacts_dir and os.path.exists(temp_artifacts_dir):
            try:
                shutil.rmtree(temp_artifacts_dir)
                logging.info(f"Cleaned up temporary artifacts directory: {temp_artifacts_dir}")
            except Exception as e:
                logging.warning(f"Failed to cleanup temp artifacts directory: {e}")

def run_evaluation(challenge_names, llm_manager):
    """Runs the evaluation against the specified challenges from CTFd."""
    results = []
    
    output_dir_base = "eval_results"
    if not os.path.exists(output_dir_base):
        os.makedirs(output_dir_base)

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(output_dir_base, run_timestamp)
    os.makedirs(run_output_dir)

    # Run Docker evaluations sequentially to avoid resource conflicts
    for challenge_name in challenge_names:
        try:
            result = evaluate_challenge(challenge_name, llm_manager, run_output_dir, run_timestamp)
            results.append(result)
        except Exception as exc:
            logging.error(f'{challenge_name} generated an exception: {exc}')

    # Sort results alphabetically by challenge name
    results.sort(key=lambda r: r.get('challenge_name', ''))

    logging.info("--- Evaluation Summary ---")
    successful_challenges = [r for r in results if r.get("success")]
    total_cost = sum(r.get('cost', 0) for r in results)
    logging.info(f"Total challenges run: {len(results)}")
    logging.info(f"Successful solves: {len(successful_challenges)}")
    logging.info(f"Total cost: ${total_cost:.6f}")
    for res in successful_challenges:
        logging.info(f"  - {res['challenge_name']}")

    summary_data = {
        "run_timestamp": run_timestamp,
        "total_challenges": len(results),
        "successful_challenges_count": len(successful_challenges),
        "failed_challenges_count": len(results) - len(successful_challenges),
        "total_cost": total_cost,
        "average_duration": sum(r.get('duration', 0) for r in results) / len(results) if results else 0,
        "successful_challenges": [r['challenge_name'] for r in results if r.get('success')],
        "failed_challenges": [r['challenge_name'] for r in results if not r.get('success')],
        "detailed_results": results,
    }

    with open(os.path.join(run_output_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f, indent=4)
    
    logging.info(f"Summary report saved to {os.path.join(run_output_dir, 'summary.json')}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate CTF agent against local CTFd instance.")
    parser.add_argument("--challenge", help="Specify a single challenge name to run from CTFd.", type=str, default=None)
    args = parser.parse_args()

    llm_manager = LiteLLMManager()
    
    # Fetch challenges from CTFd
    api_token = os.environ.get('CTFD_API_TOKEN')
    if not api_token:
        logging.error("CTFD_API_TOKEN not found in .env file")
        logging.error("Please ensure you have run start_ctfd.py first to generate an API token")
        return
    
    base_url = os.environ.get('CTFD_URL', 'http://localhost:8000')
    logging.info("Running in local CTFd mode: challenges will be fetched from CTFd and flags submitted back")
    
    # Get challenge list from CTFd
    headers = {
        'Authorization': f'Token {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}/api/v1/challenges", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                all_challenges = [ch.get('name') for ch in data['data']]
                
                if args.challenge:
                    # Filter to specific challenge
                    if args.challenge in all_challenges:
                        challenge_names = [args.challenge]
                    else:
                        logging.error(f"Challenge '{args.challenge}' not found in CTFd")
                        logging.info(f"Available challenges: {', '.join(all_challenges)}")
                        return
                else:
                    # Use all challenges
                    challenge_names = all_challenges
                    logging.info(f"Found {len(challenge_names)} challenges in CTFd")
            else:
                logging.error("No challenges found in CTFd response")
                return
        else:
            logging.error(f"Failed to fetch challenges from CTFd: {response.status_code}")
            return
    except Exception as e:
        logging.error(f"Failed to connect to CTFd: {e}")
        return
    
    run_evaluation(challenge_names, llm_manager)

if __name__ == "__main__":
    main()

