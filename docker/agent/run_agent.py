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
    def submit_flag(flag: str) -> bool:
        logger.info(f"Flag submitted: {flag}")
        result = flag == challenge.flag
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
        
        # Calculate total cost for all LLM requests
        try:
            total_cost = llm_manager.get_usage_cost()
            logger.info(f"Total LLM cost: ${total_cost:.6f}")
        except Exception as cost_error:
            logger.warning(f"Could not calculate LLM cost: {cost_error}")
            total_cost = 0.0
        
        # Write final result with LLM usage data
        with open('/app/output/final_result.txt', 'w') as f:
            f.write(json.dumps({
                'found_flag': found_flag,
                'success': found_flag == challenge.flag if found_flag else False,
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