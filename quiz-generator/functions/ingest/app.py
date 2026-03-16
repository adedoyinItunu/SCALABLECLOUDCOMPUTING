import json
import boto3
import uuid
import os

# boto3 is the AWS Python SDK - it lets you talk to SQS, DynamoDB etc.
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    """
    Called when the front-end POSTs to /quiz.
    1. Validates the request body
    2. Creates a unique jobId
    3. Saves initial status to DynamoDB
    4. Sends the job to SQS for async processing
    5. Returns the jobId immediately (does not wait for OpenAI)
    """

    # CORS headers - required so your HTML page can call this API
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

    try:
        body = json.loads(event.get('body', '{}'))

        # Validate required fields
        mode        = body.get('mode')           # "topic" or "text"
        user_input  = body.get('input')          # the topic string or pasted text
        num_questions = body.get('numQuestions', 5)
        difficulty  = body.get('difficulty', 'medium')

        if not mode or not user_input:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "mode and input are required"})
            }

        # Generate a unique ID for this quiz job
        job_id = str(uuid.uuid4())

        # Save initial record to DynamoDB so the front-end can poll immediately
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        table.put_item(Item={
            'jobId':  job_id,
            'status': 'pending',
            'mode':   mode,
            'input':  user_input
        })

        # Send the job details to SQS - this triggers the processor Lambda
        sqs.send_message(
            QueueUrl=os.environ['QUEUE_URL'],
            MessageBody=json.dumps({
                'jobId':        job_id,
                'mode':         mode,
                'input':        user_input,
                'numQuestions': num_questions,
                'difficulty':   difficulty
            })
        )

        # Return 202 Accepted - job received but not yet complete
        return {
            "statusCode": 202,
            "headers": headers,
            "body": json.dumps({
                "jobId":   job_id,
                "status":  "pending",
                "message": "Quiz is being generated"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }
