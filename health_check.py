import os
import time
from datetime import datetime

log_file = "voting_data.json"

def check_health():
    print("Running health check at " + datetime.now().strftime('%H:%M:%S'))
    
    if not os.path.exists(log_file):
        print("ALERT: database missing")
        return
    
    last_mod = os.path.getmtime(log_file)
    now = time.time()
    diff = now - last_mod

    if diff > 60:
        print("WARNING: System inactive for " + str(round(diff, 2)) + " seconds")
    else:
        size = os.path.getsize(log_file) / 1024
        print("SYSTEM HEALTHY")
        print("DB Size: " + str(round(size, 2)) + " KB")
        print("Active " + str(round(diff, 2)) + " sec ago")

if __name__ == "__main__":
    check_health()