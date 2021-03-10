# GPU Idle Alert

This script is meant to be run as a cronjob. If it doesn't see GPU Activity over a specific period of time (defaulted to 30 minutes) it will send a message to Slack.

## Installation Requirements

* Python 3
* nvidia-smi


## Running

Define the `SLACK_NOTIFICATION_URL` environmental variable or overwrite the script to hard code a value. Run as a cronjob every minute or so.
