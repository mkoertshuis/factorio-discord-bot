import json
import os
import boto3

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import requests

PUBLIC_KEY = os.getenv('PUBLIC_KEY')
APP_ID = os.getenv('APP_ID')

print(f'Public Key: {PUBLIC_KEY}')
print(f'App ID: {APP_ID}')

def format_describe(stack_json):
  # Load the JSON string into a Python dictionary
  stack_details = json.loads(stack_json)

  # Extract relevant details
  stack_name = stack_details.get('StackName', 'N/A')
  stack_status = stack_details.get('StackStatus', 'N/A')
  creation_time = stack_details.get('CreationTime', 'N/A')
  
  # Format parameters
  parameters = stack_details.get('Parameters', [])
  formatted_parameters = "\n".join([f"{param_key}: {param_value}" 
                                      for param in parameters 
                                      for param_key, param_value in param.items()])

  # Create a formatted string for the output
  embed = {
    "title": stack_name,
    "color": 5814783,
    "fields": [
      {
        "name": "Stack Status",
        "value": stack_status,
        "inline": False
      },
      {
        "name": "Creation Time",
        "value": creation_time,
        "inline": False
      },
      {
        "name": "Parameters",
        "value": formatted_parameters or 'None',
        "inline": False
      }
    ]
  }

  return embed

def describe(event):
    cloudformation = boto3.client('cloudformation')
    stack_name = event.get('stack_name', 'factorio')
    response = cloudformation.describe_stacks(StackName=stack_name)
    stack_details = response['Stacks'][0]
    parameters = stack_details.get('Parameters', [])
    content = json.dumps({
        'StackName': stack_details['StackName'],
        'StackStatus': stack_details['StackStatus'],
        'CreationTime': stack_details['CreationTime'].isoformat(),
        'Parameters': [{param['ParameterKey']: param['ParameterValue']} for param in parameters]
    }, default=str)
    return content

def update_stack(event,options):
  cloudformation = boto3.client('cloudformation')
  for option in options:
    if option['name'] == "state":
      state = option['value']
      break
  print(f"New state: {state}")
  response = client.update_stack(
    StackName="factorio",
    UsePreviousTemplate=True,
    Parameters=[{
      'ParameterKey': 'ServerState',
      'ParameterValue': state
    }],
    Capabilities=['CAPABILITY_IAM']
  )
  return response, state

def defer(id, token):
    url = f"https://discord.com/api/interactions/{id}/{token}/callback"
    callback_data = {
        "type": 5
    }
    response = requests.post(url, json=callback_data)
    print(f'Defer Response: {response.status_code} - {response.text}')  # Debug line

    if response.status_code != 204:  # 204 No Content is expected
        print(f'Failed to defer interaction: {response.text}')

def update(data, token):
    url = f"https://discord.com/api/webhooks/{APP_ID}/{token}/messages/@original"
    response = requests.patch(url, json=data)
    print(f'Update Response: {response.status_code} - {response.text}')  # Debug line

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        signature = event['headers']['x-signature-ed25519']
        timestamp = event['headers']['x-signature-timestamp']

        # Validate the interaction
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        message = timestamp + event['body']
        
        try:
            verify_key.verify(message.encode(), signature=bytes.fromhex(signature))
        except BadSignatureError:
            return {
                'statusCode': 401,
                'body': json.dumps('invalid request signature')
            }
        
        # Handle the interaction
        t = body['type']
        if t == 1:
            return {
                'statusCode': 200,
                'body': json.dumps({'type': 1})
            }
        elif t == 2:
            return command_handler(body,event)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('unhandled request type')
            }
    except Exception as e:
        print(f'Error: {str(e)}')
        raise

def command_handler(body,event):
    defer(body['id'], body['token'])

    command = body['data']['name']
    options = body['data'].get('options',[])
    match command:
        case 'describe':
          content = describe(event)
          update({"embeds":[format_describe(content)]}, body['token'])
          return {
              'statusCode': 200,
              'headers': {'Content-Type': 'application/json'},
              'body': content
          }
        case 'update':
          content, state = update_stack(event,options)
          update({"content":f"Server state set to {state}!"})
          return {
              'statusCode': 200,
              'headers': {'Content-Type': 'application/json'},
              'body': content
          }
        case _:
            update({"content":"Command not found!"}, body['token'])
            return {
                'statusCode': 400,
                'body': json.dumps('unhandled command')
            }