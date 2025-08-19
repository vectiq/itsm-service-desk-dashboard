# Bedrock with Python via Boto3 — Minimal How-To

This guide shows how to verify access, list available models, and generate text using two APIs:

* `InvokeModel` for native per-model payloads
* `Converse` for a unified chat interface

It is distilled from the AWS User Guide page “Run example Amazon Bedrock API requests through the AWS SDK for Python (Boto3).” ([AWS Documentation][1])

---

## Prerequisites

* An AWS account plus a user or role with Bedrock permissions. ([AWS Documentation][1])
* Model access requested for **Amazon Titan Text G1 - Express**. ([AWS Documentation][1])
* Python with **boto3** installed and authenticated credentials configured. See Boto3 quickstart and AWS credential setup referenced by the page. ([AWS Documentation][1])

> Tip: Set `AWS_REGION` to a Bedrock region where your chosen model is available.

---

## 1) List available foundation models

Purpose: sanity check that credentials, region, and access are correct. This calls `ListFoundationModels`. ([AWS Documentation][1])

```python
"""
Lists the available Amazon Bedrock models.
"""
import logging
import json
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_foundation_models(bedrock_client):
    """
    Gets a list of available Amazon Bedrock foundation models.
    :return: The list of available bedrock foundation models.
    """
    try:
        response = bedrock_client.list_foundation_models()
        models = response["modelSummaries"]
        logger.info("Got %s foundation models.", len(models))
        return models
    except ClientError:
        logger.error("Couldn't list foundation models.")
        raise

def main():
    """Creates a Bedrock client and lists models in the configured region."""
    bedrock_client = boto3.client(service_name="bedrock")
    fm_models = list_foundation_models(bedrock_client)
    for model in fm_models:
        print(f"Model: {model['modelName']}")
        print(json.dumps(model, indent=2))
        print("---------------------------\n")
    logger.info("Done.")

if __name__ == "__main__":
    main()
```

Source: AWS example. ([AWS Documentation][1])

---

## 2) Generate text with the native inference API (`InvokeModel`)

Use when you want model-specific request bodies. Example targets **Amazon Titan Text G1 - Express**. ([AWS Documentation][1])

```python
# Use the native inference API to send a text message to Amazon Titan Text G1 - Express.

import boto3
import json
from botocore.exceptions import ClientError

# Create an Amazon Bedrock Runtime client.
brt = boto3.client("bedrock-runtime")

# Set the model ID, for example Amazon Titan Text G1 - Express.
model_id = "amazon.titan-text-express-v1"

# Define the prompt for the model.
prompt = "Describe the purpose of a 'hello world' program in one line."

# Format the request payload using the model's native structure.
native_request = {
    "inputText": prompt,
    "textGenerationConfig": {
        "maxTokenCount": 512,
        "temperature": 0.5,
        "topP": 0.9
    },
}

# Convert the native request to JSON.
request = json.dumps(native_request)

try:
    # Invoke the model with the request.
    response = brt.invoke_model(modelId=model_id, body=request)
except (ClientError, Exception) as e:
    print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
    raise

# Decode the response body.
model_response = json.loads(response["body"].read())

# Extract and print the response text.
response_text = model_response["results"][0]["outputText"]
print(response_text)
```

Source: AWS example. ([AWS Documentation][1])

---

## 3) Generate text with the unified chat API (`Converse`)

Preferred when supported because it unifies request format and simplifies multi-turn conversations. ([AWS Documentation][1])

```python
# Use the Conversation API to send a text message to Amazon Titan Text G1 - Express.

import boto3
from botocore.exceptions import ClientError

# Create an Amazon Bedrock Runtime client.
brt = boto3.client("bedrock-runtime")

# Set the model ID, for example Amazon Titan Text G1 - Express.
model_id = "amazon.titan-text-express-v1"

# Start a conversation with the user message.
user_message = "Describe the purpose of a 'hello world' program in one line."
conversation = [
    {
        "role": "user",
        "content": [{"text": user_message}],
    }
]

try:
    # Send the message to the model, using a basic inference configuration.
    response = brt.converse(
        modelId=model_id,
        messages=conversation,
        inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
    )

    # Extract and print the response text.
    response_text = response["output"]["message"]["content"][0]["text"]
    print(response_text)
except (ClientError, Exception) as e:
    print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
    raise
```

Source: AWS example. ([AWS Documentation][1])

---

## Notes for implementers

* If `ListFoundationModels` returns zero or your target is missing, confirm Region and that model access is granted in the console. ([AWS Documentation][1])
* Use `Converse` when available, fall back to `InvokeModel` otherwise. ([AWS Documentation][1])
* The AWS doc page links to CLI and SageMaker notebook variants if you need them. ([AWS Documentation][1])

---

## References

* “Run example Amazon Bedrock API requests through the AWS SDK for Python (Boto3).” AWS Docs. ([AWS Documentation][1])

---

[1]: https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started-api-ex-python.html "Run example Amazon Bedrock API requests through the AWS SDK for Python (Boto3) - Amazon Bedrock"
