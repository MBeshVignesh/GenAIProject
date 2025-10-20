# AWS Credentials Setup Guide

This guide will help you set up AWS credentials for the Career Path Recommender System.

## Prerequisites

1. An AWS account
2. AWS CLI installed (optional but recommended)
3. Access to AWS Bedrock service

## Method 1: Environment Variables (Recommended)

### Windows (PowerShell)
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:AWS_DEFAULT_REGION="us-east-1"
```

### Windows (Command Prompt)
```cmd
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_DEFAULT_REGION=us-east-1
```

### Linux/Mac (Bash)
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

## Method 2: AWS Credentials File

Create a file at `~/.aws/credentials` (Linux/Mac) or `%USERPROFILE%\.aws\credentials` (Windows):

```ini
[default]
aws_access_key_id = your-access-key-id
aws_secret_access_key = your-secret-access-key
region = us-east-1
```

## Method 3: AWS CLI Configuration

If you have AWS CLI installed:

```bash
aws configure
```

Follow the prompts to enter your credentials.

## Getting AWS Credentials

1. **Log in to AWS Console**: Go to https://aws.amazon.com/console/
2. **Navigate to IAM**: Search for "IAM" in the AWS services
3. **Create Access Key**:
   - Go to "Users" → Select your user → "Security credentials" tab
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Download the credentials file or copy the keys

## Required AWS Permissions

Your AWS user/role needs the following permissions for Bedrock:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
    ]
}
```

## Enabling Bedrock Access

1. **Go to AWS Bedrock Console**: https://console.aws.amazon.com/bedrock/
2. **Request Model Access**:
   - Click "Model access" in the left sidebar
   - Find "Claude 3.5 Sonnet" and click "Request model access"
   - Submit the request (usually approved quickly)

## Testing Your Setup

Run the following Python script to test your credentials:

```python
import boto3
from botocore.exceptions import ClientError

try:
    # Test basic AWS access
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"✅ AWS credentials working! User: {identity['Arn']}")
    
    # Test Bedrock access
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    print("✅ Bedrock client initialized successfully")
    
except ClientError as e:
    print(f"❌ AWS Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Troubleshooting

### Common Issues:

1. **Access Denied**: Make sure you have Bedrock permissions and model access
2. **Invalid Credentials**: Double-check your access key and secret key
3. **Region Issues**: Ensure you're using a region where Bedrock is available (us-east-1, us-west-2, etc.)
4. **Model Not Available**: Request access to Claude models in the Bedrock console

### Supported Regions:
- us-east-1 (N. Virginia)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- ap-southeast-1 (Singapore)

## Security Best Practices

1. **Never commit credentials to version control**
2. **Use IAM roles when possible** (for EC2 instances)
3. **Rotate access keys regularly**
4. **Use least privilege principle** - only grant necessary permissions
5. **Consider using AWS Secrets Manager** for production applications

## Next Steps

Once your credentials are set up, you can run the career recommender:

```bash
python main.py
```

The system will automatically detect your AWS credentials and use Bedrock for enhanced recommendations, or fall back to built-in recommendations if credentials are not available.
