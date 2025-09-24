import argparse
import os
import json
import logging
import time
from datetime import datetime
import io
import shutil
import concurrent.futures

from agent.agent import Agent # The agent to evaluate
from helper.ctf_challenge import create_challenge_from_chaldir, CTFChallengeGrader
from helper.llm_helper import LiteLLMManager

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
    
    workdir = os.path.join(challenge_output_dir, "workdir")

    try:
        challenge = create_challenge_from_chaldir(chal_dir)
        grader = CTFChallengeGrader(challenge)
        client = grader.create_client(workdir)

        # Setup individual logger for the agent
        agent_log_stream = io.StringIO()
        agent_logger = logging.getLogger(f"agent_{challenge_name}")
        agent_logger.propagate = False
        agent_logger.handlers = []
        handler = logging.StreamHandler(agent_log_stream)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        agent_logger.addHandler(handler)
        agent_logger.setLevel(logging.INFO)

        agent = Agent(llm_manager, logger=agent_logger)

        request_ids_before = list(llm_manager.llm_requests)
        start_time = time.time()
        found_flag = agent.solve_challenge(client)
        end_time = time.time()
        request_ids_after = list(llm_manager.llm_requests)

        challenge_request_ids = [rid for rid in request_ids_after if rid not in request_ids_before]
        challenge_cost = llm_manager.get_cost_for_requests(challenge_request_ids)

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
        }

        with open(os.path.join(challenge_output_dir, "result.json"), "w") as f:
            json.dump(result_data, f, indent=4)

        with open(os.path.join(challenge_output_dir, "agent.log"), "w") as f:
            f.write(agent_log_stream.getvalue())
        
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

def run_evaluation(challenge_dirs, llm_manager):
    """Runs the evaluation against the specified challenges in parallel."""
    results = []
    
    output_dir_base = "eval_results"
    if not os.path.exists(output_dir_base):
        os.makedirs(output_dir_base)

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(output_dir_base, run_timestamp)
    os.makedirs(run_output_dir)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_chal = {executor.submit(evaluate_challenge, chal_dir, llm_manager, run_output_dir, run_timestamp): chal_dir for chal_dir in challenge_dirs}
        for future in concurrent.futures.as_completed(future_to_chal):
            chal_dir = future_to_chal[future]
            try:
                result = future.result()
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