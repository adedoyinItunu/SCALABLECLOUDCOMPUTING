import json
import boto3
import os

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
        job_id = event['pathParameters']['jobId']
        table = dynamodb.Table(os.environ['TABLE_NAME'])
        response = table.get_item(Key={'jobId': job_id})
        item = response.get('Item')

        if not item:
            return {
                "statusCode": 404,
                "headers": HEADERS,
                "body": json.dumps({"error": "Job not found"})
            }

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps(item)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": str(e)})
        }
