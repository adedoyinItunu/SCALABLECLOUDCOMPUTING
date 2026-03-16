import json
import boto3
import os
import urllib.request

dynamodb = boto3.resource('dynamodb')

# Read the OpenAI key directly from the environment variable set in template.yaml
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']


def call_openai(prompt):
    """
    Call the OpenAI Chat Completions API using only built-in Python libraries.
    No pip install needed - Lambda supports urllib out of the box.
    """
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a quiz generator. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=45) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['choices'][0]['message']['content']


def build_prompt(mode, user_input, num_questions, difficulty):
    """Build the prompt that tells OpenAI exactly what format to return."""
    source = f"the topic: {user_input}" if mode == "topic" else f"this text: {user_input}"

    return f"""Generate {num_questions} multiple choice quiz questions based on {source}.
Difficulty level: {difficulty}.

Respond ONLY with a JSON array in exactly this format, no other text:
[
  {{
    "question": "question text here",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "answer": "A",
    "explanation": "brief explanation of why A is correct"
  }}
]"""


def lambda_handler(event, context):
    """
    Triggered automatically by SQS when a message arrives.
    1. Reads the job details from the SQS message
    2. Calls OpenAI with a structured prompt
    3. Parses the response into structured question objects
    4. Updates DynamoDB with status 'done' and the questions
    """
    table = dynamodb.Table(os.environ['TABLE_NAME'])

    # SQS delivers messages in a 'Records' list (BatchSize=1 so always one item)
    for record in event['Records']:
        body   = json.loads(record['body'])
        job_id = body['jobId']

        try:
            prompt       = build_prompt(
                body['mode'],
                body['input'],
                body.get('numQuestions', 5),
                body.get('difficulty', 'medium')
            )
            raw_response = call_openai(prompt)
            questions    = json.loads(raw_response)

            # Write completed result to DynamoDB
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #s = :s, questions = :q',
                ExpressionAttributeNames={'#s': 'status'},  # 'status' is reserved in DynamoDB
                ExpressionAttributeValues={
                    ':s': 'done',
                    ':q': questions
                }
            )

        except Exception as e:
            # Mark job as failed so the front-end does not spin forever
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #s = :s, errorMsg = :e',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':s': 'failed',
                    ':e': str(e)
                }
            )
