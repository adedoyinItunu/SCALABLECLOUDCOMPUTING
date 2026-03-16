import json
import boto3
import os
import urllib.request
import urllib.error

dynamodb = boto3.resource('dynamodb')
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

def call_claude(prompt):
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            result = json.loads(response.read().decode('utf-8'))
            raw_text = result['content'][0]['text'].strip()

            # Strip markdown code fences if Claude added them
            if raw_text.startswith("```"):
                lines = raw_text.split('\n')
                # Remove first and last lines (the ``` fences)
                raw_text = '\n'.join(lines[1:-1]).strip()

            return raw_text

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Anthropic API error {e.code}: {error_body}")

def build_prompt(mode, user_input, num_questions, difficulty):
    source = f"the topic: {user_input}" if mode == "topic" else f"this text: {user_input}"
    return f"""Generate {num_questions} multiple choice quiz questions based on {source}.
Difficulty level: {difficulty}.

You MUST respond with ONLY a raw JSON array. No introduction. No explanation. No markdown. No code fences. Just the JSON array starting with [ and ending with ].

Example of the exact format required:
[
  {{
    "question": "What is AWS Lambda?",
    "options": ["A) A database service", "B) A serverless compute service", "C) A storage service", "D) A networking service"],
    "answer": "B",
    "explanation": "AWS Lambda is a serverless compute service that runs code in response to events."
  }}
]

Now generate {num_questions} questions about {source} at {difficulty} difficulty. Reply with the JSON array only."""

def lambda_handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])

    for record in event['Records']:
        body = json.loads(record['body'])
        job_id = body['jobId']

        try:
            prompt = build_prompt(
                body['mode'],
                body['input'],
                body.get('numQuestions', 5),
                body.get('difficulty', 'medium')
            )
            raw_response = call_claude(prompt)
            questions = json.loads(raw_response)

            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #s = :s, questions = :q',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'done', ':q': questions}
            )

        except Exception as e:
            table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #s = :s, errorMsg = :e',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'failed', ':e': str(e)}
            )
