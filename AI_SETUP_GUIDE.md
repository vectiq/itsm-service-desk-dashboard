# 🤖 AWS Bedrock AI Integration Setup Guide

This guide walks you through setting up AWS Bedrock AI capabilities in your ITSM Dashboard.

## 📋 Prerequisites

1. **AWS Account** with Bedrock access
2. **Bedrock API Key** (you already have this in .env)
3. **Python environment** with required packages

## 🚀 Quick Setup

### 1. Install Required Packages

```bash
pip install boto3 python-dotenv
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Verify .env Configuration

Your `.env` file should contain:
```
AWS_BEARER_TOKEN_BEDROCK=ABSKQmVkcm9ja0FQSUtleS14a2h0LWF0LTA1MjY5NDc2NTY3MDpxcUk4VUJHVm52azc4d1hWWjBKTUcxUFFRMGpwcDljSWdwVlJidlRWdytvWGVXeDJyZFgzTS9WOXFZRT0=
AWS_REGION=us-east-1  # Optional, defaults to us-east-1
```

**Note:** Only the `AWS_BEARER_TOKEN_BEDROCK` is required. The bearer token contains all necessary authentication information.

### 3. Test AI Connection

Run the Streamlit app and check:
- Home page shows "🤖 AWS Bedrock AI: Connected"
- New "🤖 AI Features" page is available in sidebar

## 🎯 AI Use Cases Implemented

### UC-02: Incident Triage & Priority Classification
- **Purpose**: Automatically classify incident priority (P1-P5) based on title and description
- **Model**: Claude (Anthropic) for natural language understanding
- **Input**: Incident title + description
- **Output**: Priority level + reasoning

**Example Usage:**
```python
result = bedrock_client.classify_incident_priority(
    "Email server down", 
    "All users unable to access email. Business operations severely impacted."
)
# Returns: {"priority": "P1", "reasoning": "Critical system outage affecting all users"}
```

### UC-21: Knowledge Base Article Generation
- **Purpose**: Generate KB articles from clusters of similar incidents
- **Model**: Claude (Anthropic) for content generation
- **Input**: List of similar incidents with resolutions
- **Output**: Structured KB article (title, problem, solution, tags)

**Example Usage:**
```python
article = bedrock_client.generate_kb_article(incident_cluster)
# Returns: {"title": "...", "problem": "...", "solution": "...", "tags": "..."}
```

### UC-31: Intelligent Agent Assignment
- **Purpose**: Match incidents to best available agents based on skills, capacity, performance
- **Model**: Claude (Anthropic) for decision reasoning
- **Input**: Incident details + available agents with skills/capacity
- **Output**: Recommended agent + reasoning + confidence level

**Example Usage:**
```python
recommendation = bedrock_client.recommend_agent_assignment(incident, available_agents)
# Returns: {"agent": "Alice Johnson", "reasoning": "...", "confidence": "High"}
```

## 🧪 Testing the AI Features

### 1. Navigate to AI Features Page
- Go to "🤖 AI Features" in the sidebar
- You should see 4 tabs: UC-02, UC-21, UC-31, and AI Playground

### 2. Test UC-02: Incident Triage
- Try the sample incidents or enter custom ones
- Click "🎯 Classify Priority"
- Verify you get priority classification with reasoning

### 3. Test UC-21: KB Generation
- Select an incident category
- Click "📝 Generate KB Article"
- Review the generated article structure

### 4. Test UC-31: Agent Assignment
- Select an incident from the queue
- Click "🎯 Find Best Agent"
- Review the assignment recommendation

### 5. Test AI Playground
- Try custom prompts with Claude or Titan models
- Adjust temperature and max tokens
- Verify responses are generated

## 🔧 Configuration Options

### Model Selection
You can modify the models used in `utils/bedrock_client.py`:

```python
# For Claude
modelId='anthropic.claude-v2'  # or 'anthropic.claude-instant-v1'

# For Titan
modelId='amazon.titan-text-express-v1'  # or other Titan variants
```

### AWS Region
Update the region in `BedrockClient.__init__()`:
```python
self.region = 'us-east-1'  # Change to your preferred region
```

### Model Parameters
Adjust default parameters for different use cases:
```python
# For more creative responses
temperature = 0.8

# For more deterministic responses
temperature = 0.2

# For longer responses
max_tokens = 2000
```

## 🚨 Troubleshooting

### "AWS Bedrock is not available"
1. Check .env file exists and has correct credentials
2. Verify BEDROCK_KEY and AWS_BEARER_TOKEN_BEDROCK are set
3. Ensure boto3 and python-dotenv are installed

### "Error invoking Claude/Titan"
1. Check AWS region is correct
2. Verify model IDs are available in your region
3. Check AWS account has Bedrock access
4. Verify credentials have proper permissions

### "Failed to initialize Bedrock client"
1. Check internet connectivity
2. Verify AWS credentials format
3. Try different AWS region
4. Check if Bedrock service is available in your region

## 📊 Performance Considerations

### API Costs
- Monitor Bedrock usage in AWS console
- Each AI call incurs costs based on tokens processed
- Consider caching results for repeated queries

### Response Times
- AI calls typically take 2-5 seconds
- Use loading spinners for better UX
- Consider async processing for batch operations

### Rate Limits
- Bedrock has rate limits per model
- Implement retry logic for production use
- Consider queuing for high-volume scenarios

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit .env file to version control
2. **Credential Rotation**: Regularly rotate AWS credentials
3. **Access Control**: Use IAM roles with minimal required permissions
4. **Input Validation**: Sanitize user inputs before sending to AI models
5. **Output Filtering**: Review AI outputs before displaying to users

## 🚀 Next Steps

1. **Production Integration**: Integrate AI features into existing ITSM workflows
2. **Model Fine-tuning**: Train custom models on your specific incident data
3. **Automation**: Set up automated triage and assignment workflows
4. **Monitoring**: Implement logging and monitoring for AI decisions
5. **Feedback Loop**: Collect user feedback to improve AI accuracy

## 📞 Support

For issues with:
- **AWS Bedrock**: Check AWS documentation and support
- **Application Code**: Review error logs and debug locally
- **Model Performance**: Experiment with different prompts and parameters
