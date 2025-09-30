import logging
from helper.ctf_challenge import CTFChallengeGrader, create_challenge_from_chaldir
from helper.llm_helper import LiteLLMManager
from agent.agent import Agent
from pprint import pprint

# NOTE: This demo runs the agent in local mode (not Docker) for quick testing.
# For full Docker-based evaluation with network services, use eval_agent.py instead.


def test_key():
    key_info = LiteLLMManager.get_key_info()
    print("Key Information:")
    pprint(key_info)
    print("Remaining Balance:", LiteLLMManager.get_remaining_balance())
    print("===")
    

def test_litellm():
    '''
    Test that your LLM setup is working.
    If this fails, make sure your .env file is correct.
    '''
    print("Available Models:", LiteLLMManager.list_models())
    llm_manager = LiteLLMManager()
    llm_model_client = llm_manager.create_client()
    response = llm_model_client.simple_call("gpt-5-nano-2025-08-07", "Hello, how are you?")
    print("LLM Response:", response.choices[0].message.content)
    message_cost = llm_manager.get_request_cost(response.id)
    print("Message Cost:", message_cost)
    print("===")
    
def test_agent():
    logging.basicConfig(
        level=logging.INFO,  # Minimum level to capture
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    llm_manager = LiteLLMManager()
    agent = Agent(llm_manager, logging.getLogger())

    challenge = create_challenge_from_chaldir("./challenges/baby_cat")
    print(challenge)
    challenge_grader = CTFChallengeGrader(challenge)
    challenge_client = challenge_grader.create_client("./workdir")

    flag = agent.solve_challenge(challenge_client)
    if flag and challenge_client.submit_flag(flag):
        print("Challenge solved! Flag:", flag)
    else:
        print("Failed to solve the challenge.")

    print("===")
    print("Stats:")
    # computing usage cost takes time
    usage_cost = llm_manager.get_usage_cost()
    print("Total LLM Requests:", len(llm_manager.llm_requests))
    print(f"Total Usage Cost: ${usage_cost}")

def main():
    print("GreyHat LLM CTF Agent Boilerplate")
    test_key()
    test_litellm()
    test_agent()



if __name__ == "__main__":
    main()
