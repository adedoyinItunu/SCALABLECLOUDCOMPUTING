================================================================
QUIZ GENERATOR — Scalable Cloud Programming CA
MSc Cloud Computing, NCI
================================================================

PROJECT OVERVIEW
----------------
A cloud-native quiz generation application that uses AWS serverless
architecture (Lambda, SQS, DynamoDB, API Gateway) and the OpenAI API
to generate multiple-choice questions from a topic or pasted text.

The front-end also integrates:
  - Classmate API 1: Translation service
  - Classmate API 2: Difficulty scoring service
  - Public API: Open Trivia DB (opentdb.com)

----------------------------------------------------------------
FOLDER STRUCTURE
----------------------------------------------------------------
quiz-generator/
├── template.yaml              AWS SAM infrastructure definition
├── readme.txt                 This file
├── .gitignore
├── functions/
│   ├── ingest/app.py          Lambda 1: receives POST /quiz
│   ├── processor/app.py       Lambda 2: calls OpenAI, saves result
│   └── get_quiz/app.py        Lambda 3: serves GET /quiz/{jobId}
└── frontend/
    └── index.html             Complete front-end (single file)

----------------------------------------------------------------
PREREQUISITES
----------------------------------------------------------------
1. AWS account (free tier)
2. AWS CLI installed and configured (aws configure)
3. AWS SAM CLI installed
4. Python 3.11+
5. OpenAI API key (platform.openai.com)

----------------------------------------------------------------
BACKEND DEPLOYMENT STEPS
----------------------------------------------------------------

Step 1 — Add your OpenAI API key to template.yaml
    Open template.yaml, find this line under Globals > Environment:
        OPENAI_API_KEY: "REPLACE_BEFORE_DEPLOY"
    Replace with your real key:
        OPENAI_API_KEY: "sk-your-key-here"

Step 2 — Build the project
    sam build

Step 3 — Deploy to AWS (first time only)
    sam deploy --guided

    When prompted:
        Stack Name:          quiz-generator
        AWS Region:          eu-west-1
        Confirm changes:     N
        Allow IAM creation:  Y
        Disable rollback:    N
        Auth warnings:       y (for both functions)
        Save to config file: Y

Step 4 — Copy your API URL
    After deploy completes, look for the Outputs section:
        ApiUrl = https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com/Prod
    Copy this URL.

Step 5 — Future deploys (after code changes)
    sam build && sam deploy

----------------------------------------------------------------
FRONTEND SETUP
----------------------------------------------------------------

Step 1 — Open frontend/index.html in a text editor
    Find these two lines near the top of the <script> section:

        const API_BASE  = "https://YOUR-API-ID.execute-api.eu-west-1.amazonaws.com/Prod";
        const MOCK_MODE = true;

    Replace API_BASE with your real URL from the deploy output.
    Change MOCK_MODE from true to false.

Step 2 — Connect classmate APIs (when you receive them)
    Find these lines and replace the placeholder URLs:

        const TRANSLATION_API = "https://CLASSMATE-1-API-URL/translate";
        const DIFFICULTY_API  = "https://CLASSMATE-2-API-URL/score";

Step 3 — Open in browser
    You can open index.html directly in a browser for testing.
    For production, upload to S3 static website hosting:

        aws s3 mb s3://quiz-generator-frontend-YOUR-NAME
        aws s3 sync frontend/ s3://quiz-generator-frontend-YOUR-NAME
        aws s3 website s3://quiz-generator-frontend-YOUR-NAME \
            --index-document index.html

----------------------------------------------------------------
MOCK MODE (testing without backend)
----------------------------------------------------------------
While MOCK_MODE = true in index.html:
  - No AWS backend is needed
  - Quiz generation returns sample questions after a 2s delay
  - The Open Trivia DB bonus round works for real (no key needed)
  - Classmate service buttons show placeholder alerts

----------------------------------------------------------------
VIEWING LOGS (debugging)
----------------------------------------------------------------
Stream live Lambda logs to your terminal:

    sam logs -n ProcessorFunction --stack-name quiz-generator --tail
    sam logs -n IngestFunction    --stack-name quiz-generator --tail
    sam logs -n GetQuizFunction   --stack-name quiz-generator --tail

----------------------------------------------------------------
TEARING DOWN (to avoid AWS charges after submission)
----------------------------------------------------------------
    aws cloudformation delete-stack --stack-name quiz-generator --region eu-west-1

================================================================
