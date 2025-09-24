from helper.ctf_challenge import CTFChallengeClient
from helper.agent_boilerplate import AgentInterface
from helper.llm_helper import LiteLLMManager

import os
import logging
from pathlib import Path
import re

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
    1. List files in the challenge directory
    2. Use LLM to choose a file to investigate
    3. Read the file content
    4. Use LLM to analyze the file content and extract the flag
    '''
    
    def __init__(self, lite_llm_manager: LiteLLMManager, logger: logging.Logger | None = None):
        self.lite_llm_manager = lite_llm_manager
        if logger:
            self.logger = logger

    def solve_challenge(self, challenge: CTFChallengeClient) -> str | None:
        
        # print(challenge)
        self.log(f"Solving challenge: {challenge.challenge.name}")
        
        # Implement your challenge-solving logic here
        files = list_files(challenge.working_folder)

        llm_client = self.lite_llm_manager.create_client()
        file_list_str = "\n".join(files)
        prompt1 = f"""\
        You are a cybersecurity expert participating in a Capture The Flag (CTF) competition.
        Your task is to solve this challenge:
        Challenge Name: {challenge.challenge.name}
        Challenge Description: {challenge.challenge.description}
        Challenge Categories: {challenge.challenge.categories}
        The challenge provides the following files and directories:
        {file_list_str}
        
        Choose a file to investigate further.
        Respond with the name of the file you want to investigate.
        Ex: "file.txt" without any other text or the quotes.
        """
        
        self.log(f"Prompt 1:\n{prompt1}\n")
        
        # example using the simple_call method
        response = llm_client.simple_call("gpt-5-nano", prompt1)

        self.log(f"LLM Response 1:\n{response.choices[0].message.content}\n")
        
        chosen_file = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        if not chosen_file or chosen_file not in file_list_str:
            self.log("LLM did not choose a valid file.")
            return

        self.log(f"Chosen file to investigate: {chosen_file}")
        
        file_content = Path(challenge.working_folder, chosen_file).read_bytes()
        
        self.log(f"Content of {chosen_file}:\n{str(file_content)}")
        
        # TODO: Add a way to log usage while directly using instance; mb a wrapper class?
        prompt2 = f"""\
            Here is the content of the file {chosen_file}:
            {str(file_content)}
            
            Output the flag in the format {challenge.challenge.flag_regex}
        """
        
        self.log(f"Prompt 2:\n{prompt2}\n")
        
        # example using normal call method
        response2 = llm_client.call(
            model="gemini-2.5-pro",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert participating in a Capture The Flag (CTF) competition. Your task is to find and extract the hidden flag in the provided file content."},
                {"role": "system", "content": f"The flag format is: {challenge.challenge.flag_regex}"},
                {"role": "user", "content": prompt1},
                {"role": "assistant", "content": chosen_file},
                {"role": "user", "content": prompt2}
            ],
            temperature=0.3
        )
        
        self.log(f"LLM Response 2:\n{response2.choices[0].message.content}\n")
        
        flag = response2.choices[0].message.content.strip() if response2.choices[0].message.content else ""
        
        if not flag:
            self.log("LLM did not provide a flag.")
            return
        self.log(f"LLM provided flag: {flag}")
        
        match = re.search(challenge.challenge.flag_regex, flag)
        llm_flag = match.group(0) if match else None

        self.log(f"Attempted to match flag against regex {challenge.challenge.flag_regex} gives {llm_flag}")
        if llm_flag:
            self.log("Found flag is in correct format.")
        else:
            self.log("Unable to find flag in correct format.")
            return
        
        if challenge.submit_flag(llm_flag):
            self.log("CORRECT FLAG SUBMITTED!")
            return llm_flag
        else:
            self.log("INCORRECT FLAG SUBMITTED.")
            return None
        

# define the `Agent` variable as the Agent class you would like to use
Agent = SimpleAgent
