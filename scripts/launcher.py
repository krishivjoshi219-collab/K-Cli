import os
import subprocess
import sys

os.chdir('/content')
log_file = open('/content/train.log', 'w')
proc = subprocess.Popen(
    [sys.executable, '-u', '/content/train_remote.py'],
    stdout=log_file,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
print(f"TRAINING_PID={proc.pid}")
