import json
import boto3
import uuid
import os

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,GET,OPTIONS",
    "Content-Type": "application/json"
}

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get('body', '{}'))
        mode = body.get('mode')
        user_input = body.get('input')
        num_questions = body.get('numQuestions', 5)
        difficulty = body.get('difficulty', 'medium')

        if not mode or not user_input:
            return {
                "statusCode": 400,
                "headers": HEADERS,
                "body": json.dumps({"error": "mode and input are required"})
            }

        job_id = str(uuid.uuid4())

        table = dynamodb.Table(os.environ['TABLE_NAME'])
        table.put_item(Item={
            'jobId': job_id,
            'status': 'pending',
            'mode': mode,
            'input': user_input
        })

        sqs.send_message(
            QueueUrl=os.environ['QUEUE_URL'],
            MessageBody=json.dumps({
                'jobId': job_id,
                'mode': mode,
                'input': user_input,
                'numQuestions': num_questions,
                'difficulty': difficulty
            })
        )

        return {
            "statusCode": 202,
            "headers": HEADERS,
            "body": json.dumps({
                "jobId": job_id,
                "status": "pending",
                "message": "Quiz is being generated"
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": str(e)})
        }
