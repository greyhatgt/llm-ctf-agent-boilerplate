from helper.ctf_challenge import CTFChallengeClient
from helper.agent_boilerplate import AgentInterface
from helper.llm_helper import LiteLLMManager

import os
import logging
from pathlib import Path

# https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
def list_files(startpath) -> list[str]:
    output = []
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        output.append('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            output.append('{}{}'.format(subindent, f))
    return output


class SimpleAgent(AgentInterface):
    '''
    SimpleAgent strategy:
    
    
    '''
    
    def __init__(self, lite_llm_manager: LiteLLMManager):
        self.lite_llm_manager = lite_llm_manager

    def solve_challenge(self, challenge: CTFChallengeClient):
        # Implement your challenge-solving logic here
        files = list_files(challenge.working_folder)

        llm_client = self.lite_llm_manager.create_model_client("gpt-5-nano-2025-08-07")
        file_list_str = "\n".join(files)
        prompt1 = f"""\
        You are a cybersecurity expert participating in a Capture The Flag (CTF) competition.
        Your task is to solve this challenge:
        Challenge Name: {challenge.challenge.name}
        Challenge Description: {challenge.challenge.description}
        The challenge provides the following files and directories:
        {file_list_str}
        
        Choose a file to investigate further.
        Respond with the name of the file you want to investigate.
        Ex: "file.txt" without any other text or the quotes.
        """
        response = llm_client.call(prompt1)
        chosen_file = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        if not chosen_file or chosen_file not in file_list_str:
            self.log("LLM did not choose a valid file.")
            return

        self.log(f"Chosen file to investigate: {chosen_file}")
        
        file_content = Path(challenge.working_folder, chosen_file).read_bytes()
        
        self.log(f"Content of {chosen_file}:\n{str(file_content)}")
        
        instance = llm_client.instance
        # TODO: Add a way to log usage while directly using instance; mb a wrapper class?
        prompt2 = f"""\
            
        """
        # TODO: Finish this and dockerize agent
            
        

# define the `Agent` variable as the Agent class you would like to use
Agent = SimpleAgent
