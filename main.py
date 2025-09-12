from helper.llm_helper import LiteLLMManager
from agent.agent import Agent
from IPython import embed
from pprint import pprint

# Put your agent test code here


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
    llm_model_client = llm_manager.create_model_client("gpt-5-nano-2025-08-07")
    response = llm_model_client.call("Hello, how are you?")
    print("LLM Response:", response.choices[0].message.content)
    message_cost = llm_manager.get_request_cost(response.id)
    print("Message Cost:", message_cost)
    print("===")
    
def test_agent():
    ...


def main():
    print("GreyHat LLM CTF Agent Boilerplate")
    test_key()
    test_litellm()



if __name__ == "__main__":
    main()
