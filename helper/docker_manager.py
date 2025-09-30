import docker
import tempfile
import os
import shutil
import json
import logging
import dotenv
from typing import Dict, Optional, Any
from docker.errors import NotFound

# Load environment variables from .env file
dotenv.load_dotenv()

# Verify required environment variables are set
required_env_vars = ['LITELLM_BASE_URL', 'LITELLM_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {missing_vars}. Please check your .env file.")

class DockerManager:
    """
    Simple Docker manager for CTF challenges.
    
    Provides containerized execution environment for CTF agents with:
    - Isolated networks per challenge
    - Multi-service deployment support
    - File-based Docker image building
    - Volume mounting for artifacts and output
    - Automatic cleanup of resources
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.client = docker.from_env()
        self.logger = logger or logging.getLogger(__name__)
        self.containers = []
        self.networks = []
        
    def create_network(self, name: str) -> str:
        """Create a Docker network."""
        try:
            # Remove existing network if it exists
            try:
                existing_network = self.client.networks.get(name)
                existing_network.remove()
                self.logger.info(f"Removed existing network: {name}")
            except NotFound:
                pass
            
            network = self.client.networks.create(name, driver="bridge")
            self.networks.append(network)
            self.logger.info(f"Created Docker network: {name}")
            return network.id or ""
        except Exception as e:
            self.logger.error(f"Failed to create network {name}: {e}")
            raise
    
    def build_agent_image(self, challenge_name: str) -> str:
        """Build the agent Docker image using existing Dockerfile."""
        try:
            # Use the existing Dockerfile and build context
            dockerfile_path = "docker/agent"  # Use forward slashes for Docker
            if not os.path.exists(dockerfile_path):
                raise FileNotFoundError(f"Agent Dockerfile not found at {dockerfile_path}")
            
            image_tag = f"ctf-agent:{challenge_name}"
            
            # Build the image using the project root as context
            image, build_logs = self.client.images.build(
                path=".",  # Use current directory as build context
                dockerfile=f"{dockerfile_path}/Dockerfile",  # Forward slash for Docker
                tag=image_tag,
                rm=True,
                forcerm=True
            )
            
            self.logger.info(f"Built agent image: {image_tag}")
            return image_tag
            
        except Exception as e:
            self.logger.error(f"Failed to build image: {e}")
            raise
    
    def start_container(self, image: str, name: str, network: str, 
                       environment: Optional[Dict[str, str]] = None,
                       volumes: Optional[Dict[str, Dict[str, str]]] = None,
                       ports: Optional[Dict[str, int]] = None) -> Any:
        """Start a Docker container with specified configuration."""
        try:
            # Stop and remove existing container if it exists
            try:
                existing_container = self.client.containers.get(name)
                existing_container.stop()
                existing_container.remove()
                self.logger.info(f"Removed existing container: {name}")
            except NotFound:
                pass
            
            container = self.client.containers.run(
                image=image,
                name=name,
                network=network,
                environment=environment or {},
                volumes=volumes or {},
                ports=ports or {},
                detach=True,
                remove=False
            )
            
            self.containers.append(container)
            self.logger.info(f"Started container: {name}")
            return container
            
        except Exception as e:
            self.logger.error(f"Failed to start container {name}: {e}")
            raise
    
    def run_agent(self, challenge_data: Dict, network_name: str, output_dir: str, image_tag: str) -> Dict:
        """Run the agent in a Docker container."""
        container_name = f"agent-{challenge_data['name'].lower().replace(' ', '-')}"
        
        # Create temporary directories for volume mounting
        temp_output = tempfile.mkdtemp(prefix="ctf_output_")
        temp_artifacts = tempfile.mkdtemp(prefix="ctf_artifacts_")
        
        try:
            # Copy artifacts to temp directory for easier mounting
            for item in os.listdir(challenge_data['artifacts_folder']):
                src = os.path.join(challenge_data['artifacts_folder'], item)
                dst = os.path.join(temp_artifacts, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            # Prepare volumes
            volumes = {
                temp_output: {'bind': '/app/output', 'mode': 'rw'},
                temp_artifacts: {'bind': '/app/artifacts', 'mode': 'ro'}
            }
            
            # Prepare environment
            environment = {
                'CHALLENGE_DATA': json.dumps(challenge_data),
                # Copy LiteLLM environment variables for API access
                'LITELLM_BASE_URL': os.environ.get('LITELLM_BASE_URL', ''),
                'LITELLM_API_KEY': os.environ.get('LITELLM_API_KEY', ''),
            }
            
            # Run the agent container
            container = self.start_container(
                image=image_tag,
                name=container_name,
                network=network_name,
                environment=environment,
                volumes=volumes
            )
            
            # Wait for container to complete
            result = container.wait()
            logs = container.logs().decode('utf-8')
            
            # Copy results back from temp directory
            for item in os.listdir(temp_output):
                src = os.path.join(temp_output, item)
                dst = os.path.join(output_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            # Read results
            try:
                with open(os.path.join(output_dir, 'final_result.txt'), 'r') as f:
                    final_result = json.loads(f.read())
            except Exception as e:
                self.logger.error(f"Failed to read final result: {e}")
                final_result = {'found_flag': None, 'success': False, 'error': 'Failed to read result'}
            
            return {
                'exit_code': result['StatusCode'],
                'logs': logs,
                'result': final_result
            }
            
        except Exception as e:
            self.logger.error(f"Failed to run agent: {e}")
            return {
                'exit_code': -1,
                'logs': str(e),
                'result': {'found_flag': None, 'success': False, 'error': str(e)}
            }
        finally:
            # Cleanup temp directories
            try:
                shutil.rmtree(temp_output)
                shutil.rmtree(temp_artifacts)
            except Exception as e:
                self.logger.error(f"Failed to cleanup temp directories: {e}")
    
    def cleanup(self):
        """Clean up all containers and networks."""
        # Stop and remove containers
        for container in self.containers:
            try:
                container.stop()
                container.remove()
                self.logger.info(f"Cleaned up container: {container.name}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup container {container.name}: {e}")
        
        # Remove networks
        for network in self.networks:
            try:
                network.remove()
                self.logger.info(f"Cleaned up network: {network.name}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup network {network.name}: {e}")
        
        self.containers.clear()
        self.networks.clear()