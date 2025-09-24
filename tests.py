import unittest
import logging
from helper.ctf_challenge import CTFChallengeGrader, create_challenge_from_chaldir
from helper.llm_helper import LiteLLMManager
from agent.agent import Agent
import os

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class AgentTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up resources for all tests in this class."""
        cls.llm_manager = LiteLLMManager()

    def test_01_key_info(self):
        """Tests that the API key information can be retrieved."""
        key_info = LiteLLMManager.get_key_info()
        self.assertIsNotNone(key_info, "Failed to get key info.")

        balance = LiteLLMManager.get_remaining_balance()
        # Balance can be None if not supported by the provider
        if balance is not None:
            self.assertIsInstance(balance, (float, int), "Remaining balance should be a number.")

    def test_02_litellm_call(self):
        """
        Test that the LLM setup is working by making a simple call.
        If this fails, make sure your .env file is correct.
        """
        llm_model_client = self.llm_manager.create_client()
        
        # Using a commonly available model for testing
        test_model = "gpt-3.5-turbo" 
        try:
            response = llm_model_client.simple_call(test_model, "Hello, how are you?")
            self.assertIsNotNone(response.choices[0].message.content)
            
            message_cost = self.llm_manager.get_request_cost(response.id)
            self.assertIsInstance(message_cost, (float, int))

        except Exception as e:
            self.fail(f"LiteLLM simple_call failed with model '{test_model}': {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in this class have run."""
        # computing usage cost takes time
        usage_cost = cls.llm_manager.get_usage_cost()
        logging.info(f"Total LLM Requests: {len(cls.llm_manager.llm_requests)}")
        logging.info(f"Total Usage Cost: ${usage_cost:.6f}")


if __name__ == "__main__":
    unittest.main()
