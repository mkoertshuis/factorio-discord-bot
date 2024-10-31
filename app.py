import json
import os
import asyncio
import boto3

from discord_interactions import verify_key


lambda_client = boto3.client("lambda")


async def verify_event(event):
    """Verify the event is valid.
    This function verifies the event is valid by checking the signature and timestamp.
    It returns True if the event is valid, and False if it is not.

    Parameters
    ----------
    event: dict, required
        The event to be verified

    Returns
    ------
    bool
        True if the event is valid, False if it is not
    """

    # Get the Discord public key from the environment variable
    discord_public_key = os.environ.get("DISCORD_CLIENT_KEY")

    raw_body = event["body"]
    headers = event["headers"]
    signature = headers["x-signature-ed25519"]
    timestamp = headers["x-signature-timestamp"]

    # Verify the request is valid
    is_verified = verify_key(
        raw_body.encode(), signature, timestamp, discord_public_key
    )
    print("Event Verification Status:", is_verified)
    return is_verified


async def trigger_lambda(event):
    """Trigger a Lambda function.
    This function triggers a Lambda function with the given event.

    Parameters
    ----------
    event: dict, required
        The event to be passed to the Lambda function
    """

    command_lambda_arn = os.environ.get("COMMAND_LAMBDA_ARN")

    # Trigger the Lambda function asynchronously
    response = lambda_client.invoke(
        FunctionName=command_lambda_arn,
        InvocationType="Event",
        Payload=json.dumps(event),
    )

    # Print the response
    print(response)

    # Return the response
    return response


async def run_trigger_lambda(event):
    """Run the trigger_lambda function and return the result.
    This function runs the trigger_lambda function and returns the result.
    It triggers a Lambda function with the given event.

    Parameters
    ----------
    event: dict, required
        The event to be passed to the Lambda function

    Returns
    ------
    dict
        The response from the Lambda function
    """

    # Run the trigger_lambda function and return the result
    return await trigger_lambda(event)


async def run_verify_event(event):
    """Run the verify_event function and return the result.
    This function runs the verify_event function and returns the result.
    If the event is valid, it returns True, otherwise it returns False.

    Parameters
    ----------
    event: dict, required
        The event to be verified

    Returns
    ------
    bool
        True if the event is valid, False if it is not
    """

    # Run the verify_event function and return the result
    return await verify_event(event)


def lambda_handler(event, context):
    """Lambda Function to authenticate the request and return the response.
    This function is called by the API Gateway Lambda Proxy Integration.
    It will return a 200 response if the request is valid, and a 401 response if it is not.
    The request is verified by checking the signature and timestamp.
    The request is then parsed and the appropriate response is returned.
    The response is a JSON object with the following fields:
    - type: the type of response (1 for Pong, 4 for Application Command Response)
    - data: the data to be returned (for Application Command Response, this is the content of the response)
    - nonce: the nonce to be returned (for Application Command Response, this is the nonce of the response)
    - tts: whether the response should be read aloud (for Application Command Response, this is the tts of the response)
    - embeds: the embeds to be returned (for Application Command Response, this is the embeds of the response)
    - allowed_mentions: the allowed mentions to be returned (for Application Command Response, this is the allowed mentions of the response)

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    print(event)
    request_str = event["body"]
    if event:
        verification_response = asyncio.run(run_verify_event(event))
        request_json = json.loads(request_str)
        command_type = request_json["type"]
        if command_type == 1 and verification_response:
            return {"statusCode": 200, "body": json.dumps({"type": 1})}
        elif command_type == 2 and (
            verification_response
            and asyncio.run(run_trigger_lambda(event)).get("StatusCode") == 202
        ):
            return {"statusCode": 200, "body": json.dumps({"type": 5})}
        else:
            return {
                "statusCode": 401,
                "body": json.dumps(
                    {
                        "message": "Unauthorized"
                        if not verification_response
                        else "Invalid Command Type"
                    }
                ),
            }
    else:
        print("No event received.")
        return {"statusCode": 401, "body": json.dumps({"message": "No event found."})}