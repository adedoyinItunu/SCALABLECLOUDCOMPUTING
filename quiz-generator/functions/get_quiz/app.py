import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    """
    Called when the front-end polls GET /quiz/{jobId}.
    Simply reads the item from DynamoDB and returns it.
    Front-end keeps calling this every 2 seconds until status is 'done'.
    """
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json"
    }

    try:
        # API Gateway puts path parameters in event['pathParameters']
        job_id = event['pathParameters']['jobId']

        table    = dynamodb.Table(os.environ['TABLE_NAME'])
        response = table.get_item(Key={'jobId': job_id})

        item = response.get('Item')
        if not item:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Job not found"})
            }

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(item)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }
