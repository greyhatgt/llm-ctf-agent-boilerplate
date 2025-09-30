from helper.ctf_challenge import CTFChallengeClient
from helper.agent_boilerplate import AgentInterface
from helper.llm_helper import LiteLLMManager

import os
import logging
import subprocess
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
    """
    Docker-aware CTF agent with dual-mode challenge solving capabilities.
    
    Strategy:
    1. Auto-detect challenge type (network-based vs file-based)
    2. Network challenges: Perform service discovery and targeted exploitation
    3. File challenges: Analyze artifacts and extract flags through content inspection
    4. LLM-guided analysis and exploitation planning
    5. Pattern-based flag extraction with validation
    
    Supports containerized execution with network isolation and service orchestration.
    """
    
    def __init__(self, lite_llm_manager: LiteLLMManager, logger: logging.Logger | None = None):
        self.lite_llm_manager = lite_llm_manager
        if logger:
            self.logger = logger

    def solve_challenge(self, challenge: CTFChallengeClient) -> str | None:
        
        self.log(f"Solving challenge: {challenge.challenge.name}")
        self.log(f"Challenge description: {challenge.challenge.description}")
        self.log(f"Challenge categories: {challenge.challenge.categories}")
        
        # Check if this is a network-based challenge (has network_info)
        if (challenge.network_info and 
            challenge.network_info.get('network_name')):
            self.log("Detected network-based challenge")
            return self._solve_network_challenge(challenge)
        else:
            self.log("Detected file-based challenge")
            return self._solve_file_challenge(challenge)
    
    def _solve_network_challenge(self, challenge: CTFChallengeClient) -> str | None:
        """Handle network-based challenges with service discovery."""
        
        network_name = challenge.network_info.get('network_name', 'unknown')
        self.log(f"Operating in Docker network: {network_name}")
        
        llm_client = self.lite_llm_manager.create_client()
        
        # First, perform network discovery
        discovery_prompt = f"""
        You are a cybersecurity expert participating in a CTF competition. You need to analyze and exploit a network-based challenge.
        
        Challenge: {challenge.challenge.name}
        Description: {challenge.challenge.description}
        Categories: {challenge.challenge.categories}
        Flag format: {challenge.challenge.flag_regex}
        
        You are running in a Docker container with access to tools like:
        - nmap (network scanning)
        - curl (HTTP client)
        - wget (download tool)
        - netcat (nc - network utility)
        - sqlmap (SQL injection tool)
        
        Based on the challenge description, identify any URLs, hostnames, or services mentioned that you should target.
        If specific URLs are provided in the description, use those directly.
        
        For network discovery, use standard techniques to find services, but pay close attention to any 
        URLs or hostnames explicitly mentioned in the challenge description first.
        
        You can also try common service discovery if no specific targets are mentioned:
        - nmap for port scanning
        - curl to test connectivity to discovered services
        
        Respond with specific shell commands to run, one per line. Keep scans targeted and fast.
        """
        
        self.log(f"Network discovery prompt:\n{discovery_prompt}\n")
        
        response = llm_client.simple_call("gpt-5-nano", discovery_prompt)
        self.log(f"LLM Discovery Response:\n{response.choices[0].message.content}\n")
        
        discovery_commands = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
        
        # Execute discovery commands
        discovery_results = []
        
        for line in discovery_commands.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and any(line.startswith(cmd) for cmd in ['nmap -p', 'curl', 'wget', 'nc -', 'ping']):
                cmd = None
                try:
                    cmd = line
                    self.log(f"Executing discovery: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nReturn code: {result.returncode}"
                    discovery_results.append(f"Command: {cmd}\n{output}")
                    self.log(f"Discovery output:\n{output}")
                    
                    # Check for immediate flag in output
                    match = re.search(challenge.challenge.flag_regex, result.stdout)
                    if match:
                        flag = match.group(0)
                        self.log(f"Found flag during discovery: {flag}")
                        if challenge.submit_flag(flag):
                            self.log("CORRECT FLAG SUBMITTED!")
                            return flag
                        
                except Exception as e:
                    error_msg = f"Error executing discovery {cmd or line}: {e}"
                    discovery_results.append(error_msg)
                    self.log(error_msg)
        
        # Now analyze results and attempt exploitation
        exploitation_prompt = f"""
        You are a cybersecurity expert participating in an authorized CTF (Capture The Flag) competition. 
        This is a legitimate security exercise with explicit permission to test vulnerabilities.
        
        Challenge: {challenge.challenge.name}
        Description: {challenge.challenge.description}
        Categories: {challenge.challenge.categories}
        Flag format: {challenge.challenge.flag_regex}
        
        Discovery Results:
        {chr(10).join(discovery_results)}
        
        Based on these results, you need to find and exploit the vulnerability to capture the flag.
        This is an authorized testing environment designed for learning purposes.
        
        For this CTF challenge:
        1. Identify any running web services and their locations
        2. Based on the categories {challenge.challenge.categories}, craft appropriate exploit commands
        3. For SQL injection challenges, try payloads like: admin'-- or ' OR '1'='1'--
        4. Use curl to test login forms with SQL injection payloads
        5. The flag should match the format: {challenge.challenge.flag_regex}
        
        Provide specific curl commands to exploit the vulnerability and retrieve the flag.
        Example: curl -X POST "http://webapp:80/login" -d "username=admin'--&password=anything"
        """
        
        self.log(f"Exploitation prompt:\n{exploitation_prompt}\n")
        
        exploit_response = llm_client.simple_call("gpt-5-nano", exploitation_prompt)
        self.log(f"LLM Exploitation Response:\n{exploit_response.choices[0].message.content}\n")
        
        exploit_commands = exploit_response.choices[0].message.content.strip() if exploit_response.choices[0].message.content else ""
        
        # Execute exploitation commands
        for line in exploit_commands.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and any(line.startswith(cmd) for cmd in ['curl', 'wget', 'nc', 'sqlmap', 'python']):
                cmd = None
                try:
                    cmd = line
                    self.log(f"Executing exploit: {cmd}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    output = result.stdout
                    self.log(f"Exploit output:\n{output}")
                    
                    # Check if flag is in the output
                    match = re.search(challenge.challenge.flag_regex, output)
                    if match:
                        flag = match.group(0)
                        self.log(f"Found flag: {flag}")
                        
                        if challenge.submit_flag(flag):
                            self.log("CORRECT FLAG SUBMITTED!")
                            return flag
                        else:
                            self.log("INCORRECT FLAG SUBMITTED.")
                            
                except Exception as e:
                    error_msg = f"Error executing exploit {cmd or line}: {e}"
                    self.log(error_msg)
        
        self.log("No flag found in network exploitation")
        return None
    
    def _solve_file_challenge(self, challenge: CTFChallengeClient) -> str | None:
        """Handle file-based challenges (original logic)."""
        
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
