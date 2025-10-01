import argparse
import os
import json
import logging
import time
from datetime import datetime

from helper.ctf_challenge import create_challenge_from_chaldir
from helper.llm_helper import LiteLLMManager
from helper.docker_manager import DockerManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_challenge_dirs(challenge_target=None):
    """Gets a list of challenge directories."""
    challenge_base_dir = 'challenges'
    if challenge_target:
        chal_dir = os.path.join(challenge_base_dir, challenge_target)
        if os.path.isdir(chal_dir):
            return [chal_dir]
        else:
            logging.error(f"Specified challenge '{challenge_target}' not found.")
            return []
    else:
        return [os.path.join(challenge_base_dir, d) for d in os.listdir(challenge_base_dir) if os.path.isdir(os.path.join(challenge_base_dir, d))]

def evaluate_challenge(chal_dir, llm_manager, run_output_dir, run_timestamp):
    challenge_name = os.path.basename(chal_dir)
    logging.info(f"--- Running evaluation for challenge: {challenge_name} ---")

    challenge_output_dir = os.path.join(run_output_dir, challenge_name)
    os.makedirs(challenge_output_dir)

    docker_manager = None
    try:
        challenge = create_challenge_from_chaldir(chal_dir)
        
        # Setup Docker environment for all challenges
        docker_manager = DockerManager(logging.getLogger(f"docker_{challenge_name}"))
        network_name = f"ctf-network-{challenge_name.lower().replace('_', '-')}"
        network_id = docker_manager.create_network(network_name)
        
        # Start any additional services using simplified approach
        services_deployed = []
        for service in challenge.services:
            # Build custom service image if needed
            image_name = service['image']
            docker_path = os.path.join(chal_dir, 'docker')
            if os.path.exists(docker_path) and os.path.exists(os.path.join(docker_path, 'Dockerfile')):
                logging.info(f"Building custom image: {image_name}")
                docker_manager.client.images.build(
                    path=docker_path,
                    tag=image_name,
                    rm=True,
                    forcerm=True
                )
                logging.info(f"Successfully built custom image: {image_name}")
            
            # Start the service container
            docker_manager.start_container(
                image=image_name,
                name=service['name'],
                network=network_name,
                environment=service.get('environment', {}),
                ports=service.get('ports', {})
            )
            services_deployed.append(service['name'])
            
            # Simple wait for service to be ready (replace health checks)
            time.sleep(3)
            logging.info(f"Service {service['name']} is ready")
        
        # Only create network_info if services were deployed
        network_info = None
        if services_deployed:
            network_info = {
                'network_name': network_name,
                'network_id': network_id,
                'services_deployed': services_deployed
            }
        
        # Build and run agent in Docker
        image_tag = docker_manager.build_agent_image(challenge_name)
        
        # Prepare challenge data for Docker
        challenge_data = {
            'name': challenge.name,
            'description': challenge.description,
            'categories': challenge.categories,
            'artifacts_folder': challenge.artifacts_folder,
            'flag': challenge.flag,
            'flag_regex': challenge.flag_regex,
            'network_info': network_info
        }
        
        start_time = time.time()
        
        docker_result = docker_manager.run_agent(challenge_data, network_name, challenge_output_dir, image_tag)
        
        end_time = time.time()
        
        # Extract results and LLM usage data from container
        found_flag = docker_result['result'].get('found_flag')
        container_request_ids = docker_result['result'].get('llm_request_ids', [])
        container_cost = docker_result['result'].get('llm_cost', 0.0)
        
        # Save Docker logs
        with open(os.path.join(challenge_output_dir, "agent.log"), "w", encoding="utf-8") as f:
            f.write(docker_result['logs'])

        # Use container's LLM usage data instead of host-level tracking
        challenge_request_ids = container_request_ids
        challenge_cost = container_cost

        duration = end_time - start_time
        success = found_flag is not None and found_flag == challenge.flag

        logging.info(f"Challenge: {challenge_name}, Success: {success}, Time: {duration:.2f}s, Cost: ${challenge_cost:.6f}")

        result_data = {
            "challenge_name": challenge.name,
            "success": success,
            "submitted_flag": found_flag,
            "correct_flag": challenge.flag,
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

def run_evaluation(challenge_dirs, llm_manager):
    """Runs the evaluation against the specified challenges."""
    results = []
    
    output_dir_base = "eval_results"
    if not os.path.exists(output_dir_base):
        os.makedirs(output_dir_base)

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(output_dir_base, run_timestamp)
    os.makedirs(run_output_dir)

    # Run Docker evaluations sequentially to avoid resource conflicts
    for chal_dir in challenge_dirs:
        try:
            result = evaluate_challenge(chal_dir, llm_manager, run_output_dir, run_timestamp)
            results.append(result)
        except Exception as exc:
            logging.error(f'{chal_dir} generated an exception: {exc}')

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
    parser = argparse.ArgumentParser(description="Evaluate CTF agent.")
    parser.add_argument("--challenge", help="Specify a single challenge directory name to run.", type=str, default=None)
    args = parser.parse_args()

    llm_manager = LiteLLMManager()
    challenge_dirs = get_challenge_dirs(args.challenge)
    if challenge_dirs:
        run_evaluation(challenge_dirs, llm_manager)
    else:
        logging.warning("No challenges found to evaluate.")

if __name__ == "__main__":
    main()