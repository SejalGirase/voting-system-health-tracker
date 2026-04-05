import json
import time
import random
import os
from datetime import datetime

log_file = "voting_data.json"
candidates = ["Alice", "Bob", "Charlie", "Diana"]

def generate_vote():
    return {
        "voter_id": "V-" + str(random.randint(1000, 9999)),
        "candidate": random.choice(candidates),
        "timestamp": datetime.now().isoformat()
    }

def run_sim():
    print("Starting voting simulator...")
    votes = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try:
                votes = json.load(f)
            except:
                pass

    for i in range(25):
        v = generate_vote()
        votes.append(v)
        print("Vote recorded: " + v['candidate'])
        
        with open(log_file, 'w') as f:
            json.dump(votes, f, indent=4)
        
        time.sleep(random.uniform(0.5, 1.5))
    
    print("Total votes: " + str(len(votes)))

if __name__ == "__main__":
    run_sim()