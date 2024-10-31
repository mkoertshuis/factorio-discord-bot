import requests
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

# Read from Secrets Manager if it's defined as Lambda Function
TOKEN = os.getenv('TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')

# If you want to register commands only in a specific guild/server
GUILD_ID = os.getenv('GUILD_ID')

# Guild URL
URL = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands"

# Read the new commands from a YAML file
with open("discord_commands.yaml", "r", encoding="utf-8") as file:
    yaml_content = file.read()

new_commands = yaml.safe_load(yaml_content)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Step 1: Get the current commands
response = requests.get(URL, headers=headers)
if response.status_code != 200:
    print(f"Failed to retrieve commands: {response.text}")
else:
    current_commands = response.json()

# Step 2: Delete old commands (you can customize the logic here)
for command in current_commands:
    command_name = command["name"]
    if command_name not in [cmd["name"] for cmd in new_commands]:
        delete_url = f"{URL}/{command['id']}"
        delete_response = requests.delete(delete_url, headers=headers)
        if delete_response.status_code != 204:
            print(f"Failed to delete command {command_name}: {delete_response.text}")
        else:
            print(f"Command {command_name} deleted.")

# Step 3: Register new commands
for command in new_commands:
    response = requests.post(URL, json=command, headers=headers)
    command_name = command["name"]
    if response.status_code != 200:
        print(response.text)
    else:
        print(f"Command {command_name} created: {response.status_code}")
