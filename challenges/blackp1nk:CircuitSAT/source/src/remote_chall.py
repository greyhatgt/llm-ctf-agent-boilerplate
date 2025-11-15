import threading
import time
import base64
import random
import string
import sys
import os
from main import generate_challenge


with open('/flag') as f:
    FLAG = f.read().strip()

if not FLAG:
    print("Flag not found.")
    sys.exit(1)


# Timer to end the challenge after 4 seconds
def background_timer():
    time.sleep(4)
    print("Challenge fail!")
    sys.stdout.flush()
    os._exit(1)

# Generates a random base64-encoded string and T/F list 
#TODO: Change this as to return actual b64 string + T/F list
#TODO: Ask about the flag being printed - can we just explicitly print the flag since we're not giving out the Python program?
def encode_and_generate_tf(string_length=100, tf_length=28):
    b64_str, bool_answerkey = generate_challenge()

    tf_answerkey = ['T' if x else 'F' for x in bool_answerkey]

    return (b64_str, tf_answerkey)



    random_string = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=string_length))
    input_bytes = random_string.encode('utf-8')
    encoded_string = base64.b64encode(input_bytes).decode('utf-8')

    tf_list = ['T'] * 28 #CHANGE THIS - just for exploit testing purposes
    return (encoded_string, tf_list)

def start_chall():
    encoded_str, tf = encode_and_generate_tf()
    print("Here's a b64 encoded string. To win, achieve a score of 10. Good luck!")
    print(encoded_str)
    sys.stdout.flush()

    # Start 4-second timer in the background
    timer_thread = threading.Thread(target=background_timer)
    timer_thread.start()

    score = 0
    try:
        for i in range(10):
            for j in range(28):
                print(f"What should the value of variable {j + 1} be? Enter T or F.")
                sys.stdout.flush()
                response = sys.stdin.readline().strip()

                if response == tf[j]:
                    print("Correct!")
                else:
                    print("Challenge fail!")
                    sys.stdout.flush()
                    os._exit(1)

            score += 1

            if score == 10:
                print(FLAG)
                sys.stdout.flush()
                os._exit(0)

            print(f'Score: {score}')
            encoded_str, tf = encode_and_generate_tf()
            print(f'Next problem:\n{encoded_str}')
            sys.stdout.flush()
    except Exception as e:
        print(f"Connection ended: {e}")
    finally:
        sys.exit()

if __name__ == '__main__':
    start_chall()