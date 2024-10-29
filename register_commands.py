import requests
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

# Read from Secrets Manager if it's defined as Lambda Function
TOKEN = os.getenv('TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')


# If you want to register command only in a specific guild/server
GUILD_ID = os.getenv('GUILD_ID')

# Guild URL
URL = f"https://discord.com/api/v10/applications/{APPLICATION_ID}/guilds/{GUILD_ID}/commands"


with open("discord_commands.yaml", "r",
          encoding="utf-8") as file:
    yaml_content = file.read()

commands = yaml.safe_load(yaml_content)
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Send the POST request for each command
for command in commands:
    response = requests.post(URL, json=command, headers=headers)
    command_name = command["name"]
    if response.status_code != 200:
        print(response.text)
    else:
        print(f"Command {command_name} created: {response.status_code}")
