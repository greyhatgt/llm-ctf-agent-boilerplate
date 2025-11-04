import os
import json
import sys
import logging

# Add the app directory to the Python path
sys.path.insert(0, '/app')

from agent.agent import Agent
from helper.ctf_challenge import CTFChallenge, CTFChallengeClient
from helper.llm_helper import LiteLLMManager

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("dockerized_agent")
    
    # Load challenge data from environment
    challenge_data = json.loads(os.environ.get('CHALLENGE_DATA', '{}'))
    if not challenge_data:
        logger.error("No challenge data provided")
        return
    
    # Create challenge object
    challenge = CTFChallenge(
        name=challenge_data['name'],
        description=challenge_data['description'],
        categories=challenge_data['categories'],
        artifacts_folder='/app/artifacts',
        flag=challenge_data['flag'],
        flag_regex=challenge_data['flag_regex']
    )
    
    # Create LLM manager
    llm_manager = LiteLLMManager()
    
    # Create agent
    agent = Agent(llm_manager, logger=logger)
    
    # Create challenge client
    # Check if CTFd API is configured (for --local mode)
    ctfd_api_token = os.environ.get('CTFD_API_TOKEN')
    ctfd_url = os.environ.get('CTFD_URL', 'http://localhost:8000')
    challenge_id = os.environ.get('CTFD_CHALLENGE_ID')  # Will be set by eval_agent
    
    # Track submission results for CTFd mode
    submission_results = {'last_flag': None, 'last_result': False}
    
    def submit_flag(flag: str) -> bool:
        logger.info(f"Flag submitted: {flag}")
        
        # If CTFd API is configured, submit via API
        if ctfd_api_token and challenge_id:
            try:
                import requests
                headers = {
                    'Authorization': f'Token {ctfd_api_token}',
                    'Content-Type': 'application/json'
                }
                # Submit flag to CTFd API
                # CTFd API endpoint format: POST /api/v1/challenges/attempt
                # Body: {"challenge_id": id, "submission": "flag"}
                response = requests.post(
                    f"{ctfd_url}/api/v1/challenges/attempt",
                    headers=headers,
                    json={'challenge_id': int(challenge_id), 'submission': flag},
                    timeout=10
                )
                
                if response and response.status_code in [200, 201]:
                    result_data = response.json()
                    logger.info(f"CTFd API response: {result_data}")
                    
                    # Check response format - CTFd API returns different formats
                    # Format 1: {'data': {'status': 'correct'}}
                    # Format 2: {'success': True, 'data': {'status': 'correct'}}
                    # Format 3: {'status': 'correct'}
                    # Also handle 'already_solved' status which means the flag was correct
                    result = False
                    if 'data' in result_data:
                        data = result_data.get('data', {})
                        if isinstance(data, dict):
                            status = data.get('status', '').lower()
                            # 'correct' and 'already_solved' both mean the flag was correct
                            result = status in ['correct', 'already_solved']
                        elif isinstance(data, str):
                            result = data.lower() in ['correct', 'already_solved']
                    elif 'status' in result_data:
                        status = result_data.get('status', '').lower()
                        result = status in ['correct', 'already_solved']
                    elif result_data.get('success', False):
                        # If success is True and no explicit status, check if there's an error
                        if 'error' not in result_data and 'message' not in result_data:
                            result = True
                    
                    logger.info(f"CTFd API submission result: {result} (status: {result_data.get('data', {}).get('status', 'unknown') if 'data' in result_data else 'unknown'})")
                    # Track submission result
                    submission_results['last_flag'] = flag
                    submission_results['last_result'] = result
                else:
                    logger.warning(f"CTFd API submission failed: {response.status_code} - {response.text}")
                    # Fallback to local check
                    result = flag == challenge.flag if challenge.flag else False
                    submission_results['last_flag'] = flag
                    submission_results['last_result'] = result
            except Exception as e:
                logger.warning(f"Error submitting to CTFd API: {e}, falling back to local check")
                result = flag == challenge.flag if challenge.flag else False
                submission_results['last_flag'] = flag
                submission_results['last_result'] = result
        else:
            # Local mode: just check if flag matches
            result = flag == challenge.flag
            submission_results['last_flag'] = flag
            submission_results['last_result'] = result
        
        # Write result to file that can be read from host
        with open('/app/output/flag_result.txt', 'w') as f:
            f.write(f"{flag}\n{result}")
        return result
    
    # Pass network info to client
    network_info = challenge_data.get('network_info', {})
    client = CTFChallengeClient(challenge, '/app/workdir', submit_flag, network_info)
    
    # Solve challenge
    try:
        found_flag = agent.solve_challenge(client)
        logger.info(f"Agent completed. Found flag: {found_flag}")
        
        # If found_flag is None, check flag_result.txt for submitted flag
        # (agent might return None even if flag was submitted if submission returned False)
        if not found_flag:
            try:
                flag_result_path = '/app/output/flag_result.txt'
                if os.path.exists(flag_result_path):
                    with open(flag_result_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 1:
                            submitted_flag = lines[0].strip()
                            if submitted_flag and (submitted_flag.startswith('flag{') or 'flag' in submitted_flag.lower()):
                                found_flag = submitted_flag
                                logger.info(f"Found submitted flag from flag_result.txt: {found_flag}")
            except Exception as e:
                logger.warning(f"Could not read flag_result.txt: {e}")
        
        # Calculate total cost for all LLM requests
        try:
            total_cost = llm_manager.get_usage_cost()
            logger.info(f"Total LLM cost: ${total_cost:.6f}")
        except Exception as cost_error:
            logger.warning(f"Could not calculate LLM cost: {cost_error}")
            total_cost = 0.0
        
        # Determine success: in CTFd mode, use submission result; in local mode, compare flags
        if ctfd_api_token and challenge_id:
            # CTFd mode: use the last submission result if we have it
            # If we have a submitted flag but no result tracked, check flag_result.txt
            if found_flag and not submission_results.get('last_flag'):
                submission_results['last_flag'] = found_flag
                # Try to read result from flag_result.txt
                try:
                    flag_result_path = '/app/output/flag_result.txt'
                    if os.path.exists(flag_result_path):
                        with open(flag_result_path, 'r') as f:
                            lines = f.readlines()
                            if len(lines) >= 2:
                                result_str = lines[1].strip().lower()
                                # Check for True/False/1/0/correct/incorrect
                                submission_results['last_result'] = result_str in ['true', '1', 'correct']
                except:
                    pass
            # Use tracked submission result if we have a flag submitted
            # Check if we tracked a submission result
            if 'last_result' in submission_results:
                success = submission_results['last_result']
            elif found_flag:
                # We have a flag but no tracked result - try to read from flag_result.txt
                try:
                    flag_result_path = '/app/output/flag_result.txt'
                    if os.path.exists(flag_result_path):
                        with open(flag_result_path, 'r') as f:
                            lines = f.readlines()
                            if len(lines) >= 2:
                                result_str = lines[1].strip().lower()
                                success = result_str in ['true', '1', 'correct']
                            else:
                                success = False
                    else:
                        success = False
                except:
                    success = False
            else:
                success = False
        else:
            # Local mode: compare found flag with challenge flag
            success = found_flag == challenge.flag if found_flag and challenge.flag else False
        
        # Write final result with LLM usage data
        with open('/app/output/final_result.txt', 'w') as f:
            f.write(json.dumps({
                'found_flag': found_flag,
                'success': success,
                'llm_request_ids': llm_manager.llm_requests,
                'llm_cost': total_cost
            }))
            
        # Write detailed LLM usage data
        with open('/app/output/llm_usage.json', 'w') as f:
            f.write(json.dumps({
                'request_ids': llm_manager.llm_requests,
                'total_cost': total_cost,
                'num_requests': len(llm_manager.llm_requests),
                'clients_created': len(llm_manager.clients)
            }, indent=2))
            
    except Exception as e:
        logger.error(f"Agent failed: {e}", exc_info=True)
        with open('/app/output/final_result.txt', 'w') as f:
            f.write(json.dumps({
                'found_flag': None,
                'success': False,
                'error': str(e),
                'llm_request_ids': getattr(llm_manager, 'llm_requests', []),
                'llm_cost': 0.0
            }))

if __name__ == "__main__":
    main()