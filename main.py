import json
import os
import subprocess
import time
import socket
import sys
import urllib
import urllib.request

UTILIZATION_THRESHOLD = 0.01
GPU_POLLING_ATTEMPTS = 3
GPU_IDLE_THRESHOLD = 30 # Minutes
STATUS_FILE = '/tmp/gpu_utilization_notifier'
SLACK_NOTIFICATION_URL = os.environ.get("SLACK_NOTIFICATION_URL", False)

if not SLACK_NOTIFICATION_URL:
  print("Unable to function without SLACK_NOTIFICATION_URL envvar.")


def track_for_notifications():
  utilization = get_gpu_utilization_polled(GPU_POLLING_ATTEMPTS)
  if utilization is False:
    print("No GPUs detected")
    sys.exit()

  if utilization > UTILIZATION_THRESHOLD:
    set_gpu_active()
    print("GPUs are active")
    sys.exit()

  last_active = get_gpu_last_active()
  if last_active >= GPU_IDLE_THRESHOLD:
    print("GPUs are Idle")
    send_idle_notification()
    set_gpu_active()
    sys.exit()

  print(f"GPUs have been idle for {last_active} minutes.")


def set_gpu_active():
  with open(STATUS_FILE, 'w') as statusfile:
    statusfile.write(str(time.time()))


def get_gpu_last_active():
  if not os.path.exists(STATUS_FILE):
    set_gpu_active()
    return 0
  st = os.stat(STATUS_FILE)
  return (time.time() - st.st_mtime)/60


def send_idle_notification():
  print("Sending message to slack.")
  ip_address = get_ip()
  hostname = socket.getfqdn()
  message = f'There has been no GPU activity on {hostname} ({ip_address}) for at least {GPU_IDLE_THRESHOLD} minutes.'
  payload = {
    "username": "GPU Watch",
    "icon_emoji": ":rulebreaker:",
    "text": message
  }

  # Using URLLIB directly to avoid external dependencies.
  params = json.dumps(payload).encode('utf8')
  req = urllib.request.Request(
    SLACK_NOTIFICATION_URL,
    data=params,
    headers={'content-type': 'application/json'}
  )
  response = urllib.request.urlopen(req)

#
# Code below from Nebula
# https://github.com/tedivm/nebula-cli/blob/master/nebulacli.py
# License MIT, Copyright Robert Hafner
#

def get_gpu_utilization_polled(attempts=3):
  gpu_stats = []
  for x in range(attempts):
    utilization = get_gpu_utilization()
    if utilization is False:
      return False
    gpu_stats.append(utilization)
    time.sleep(0.05)

  gpu_utilization = False
  if len(gpu_stats) > 0:
    total = sum(gpu_stats)
    if total == 0:
      gpu_utilization = 0
    else:
      gpu_utilization = sum(gpu_stats) / len(gpu_stats)

  return gpu_utilization


def get_gpu_utilization():
  # If nvidia-smi isn't here there are no GPUs
  which_result = subprocess.run(['which', 'nvidia-smi'], stdout=subprocess.PIPE)
  if which_result.returncode != 0:
    return False

  command = 'nvidia-smi --query-gpu=utilization.gpu --format=csv'
  result = subprocess.run(command.split(' '), stdout=subprocess.PIPE)
  util_strings = result.stdout.decode("utf-8").replace(' %', '').strip().split('\n')[1:]
  util_numbers = [int(n) for n in util_strings if n]

  # No GPUs detected
  if len(util_numbers) < 1:
    return False

  total = sum(util_numbers)
  if total <= 0:
    return 0

  return total/float(len(util_numbers))


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == '__main__':
    track_for_notifications()
