import openai
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat import ChatCompletionMessageParam
import dotenv
import os
import requests
from IPython import embed
from time import sleep

dotenv.load_dotenv()


class LiteLLMClient:
    def __init__(self, lite_llm_manager: 'LiteLLMManager'):
        self.lite_llm_manager = lite_llm_manager
        self.instance = openai.OpenAI(
            base_url=os.getenv('LITELLM_BASE_URL'),
            api_key=os.getenv('LITELLM_API_KEY')
        )
        self.history = []

    
    def call(self, model, messages: list[ChatCompletionMessageParam], **kwargs) -> ChatCompletion:
        params = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        response = self.instance.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        self.history.append({
            "request": params,
            "response": response
        })

        if hasattr(response, 'id') and response.id is not None:
            self.lite_llm_manager.llm_requests.append(response.id)
        if len(response.choices) == 0 or response.choices[0].message.content is None:
            raise ValueError("No valid response from LLM")
        return response
    
    # baby wrapper
    def simple_call(self, model, prompt: str, **kwargs) -> ChatCompletion:
        return self.call(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            **kwargs
        )
        

class LiteLLMManager:
    '''
    
    '''
    clients: list[LiteLLMClient]
    llm_requests: list[str]
    
    @staticmethod
    def list_models(base_url=None, api_key=None):
        base_url = base_url or os.getenv('LITELLM_BASE_URL')
        api_key = api_key or os.getenv('LITELLM_API_KEY')
        instance = openai.OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        return [model.id for model in instance.models.list().data]

    @staticmethod
    def get_remaining_balance(base_url=None, api_key=None):
        base_url = base_url or os.getenv('LITELLM_BASE_URL')
        api_key = api_key or os.getenv('LITELLM_API_KEY')
        
        k = LiteLLMManager.get_key_info(base_url, api_key)
        if 'max_budget' in k['info'] and 'spend' in k['info']:
            return k['info']['max_budget'] - k['info']['spend']
        embed()
        return None
        
    @staticmethod
    def get_key_info(base_url=None, api_key=None):
        base_url = base_url or os.getenv('LITELLM_BASE_URL')
        api_key = api_key or os.getenv('LITELLM_API_KEY')
        response = requests.get(
            f"{base_url}/key/info",
            headers={
                "accept": "application/json",
                "x-litellm-api-key": api_key
            }
        )
        return response.json()
    
    @staticmethod
    def get_request_cost(request_id: str):
        '''
        It takes a several seconds for the log to be available after the request is made.
        '''
        base_url = os.getenv('LITELLM_BASE_URL')
        api_key = os.getenv('LITELLM_API_KEY')

        for _ in range(10):
            response = requests.get(
                f"{base_url}/spend/logs?request_id={request_id}&summarize=true",
                headers={
                    "accept": "application/json",
                    "x-litellm-api-key": api_key
                }
            )
            data = response.json()
            if len(data) != 0 and data[0] is not None:
                break
            else:
                sleep(1)
        else:
            raise ValueError("Could not retrieve cost information for request_id:", request_id)

        if isinstance(data, list) and len(data) > 0 and 'spend' in data[0]:
            return data[0]['spend']
        return None

    def __init__(self, base_url=None, api_key=None):
        base_url = base_url or os.getenv('LITELLM_BASE_URL')
        api_key = api_key or os.getenv('LITELLM_API_KEY')
        self._cost = 0
        self.clients = []
        self.llm_requests = []
        
    def create_client(self) -> LiteLLMClient:
        client = LiteLLMClient(self)
        self.clients.append(client)
        return client
        
    def get_usage_cost(self) -> float:
        '''
        Get the total cost of all LLM calls made through this manager.
        '''
        total_cost = 0
        for request_id in self.llm_requests:
            cost = self.get_request_cost(request_id)
            if cost is not None:
                total_cost += cost
        return total_cost
