import json
import os

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import requests

PUBLIC_KEY = os.getenv('PUBLIC_KEY')
APP_ID = os.getenv('APP_ID')

print(f'Public Key: {PUBLIC_KEY}')
print(f'App ID: {APP_ID}')

def defer(id, token):
    url = f"https://discord.com/api/interactions/{id}/{token}/callback"

    callback_data = {
        "type": 5
    }
    response = requests.post(url, json=callback_data)
    print(f'Send Response: {response.status_code} - {response.text}')  # Debug line

def update(message, token):
    url = f"https://discord.com/api/webhooks/{APP_ID}/{token}/messages/@original"

    # JSON data to send with the request
    data = {
        "content": message
    }

    # Send the PATCH request
    response = requests.patch(url, json=data)
    print(f'Update Response: {response.status_code} - {response.text}')  # Debug line

def lambda_handler(event, context):
  try:
    body = json.loads(event['body'])
        
    signature = event['headers']['x-signature-ed25519']
    timestamp = event['headers']['x-signature-timestamp']

    # validate the interaction

    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

    message = timestamp + event['body']
    
    try:
      verify_key.verify(message.encode(), signature=bytes.fromhex(signature))
    except BadSignatureError:
      return {
        'statusCode': 401,
        'body': json.dumps('invalid request signature')
      }
    
    # handle the interaction

    t = body['type']

    if t == 1:
      return {
        'statusCode': 200,
        'body': json.dumps({
          'type': 1
        })
      }
    elif t == 2:
      return command_handler(body)
    else:
      return {
        'statusCode': 400,
        'body': json.dumps('unhandled request type')
      }
  except Exception as e:
    print(f'Error: {str(e)}')
    raise

def command_handler(body):
  defer(body['id'],body['token'])

  command = body['data']['name']
  match command:
    case 'fetch':
      content = "Hallo World!"
      update(content,body['token'])
    case _:
      update("Command not found!",body['token'])
      return {
        'statusCode': 400,
        'body': json.dumps('unhandled command')
      }
  return {
    'statusCode': 200,
    'headers' : {'Content-Type': 'application/json'},
    'body': content
  }
