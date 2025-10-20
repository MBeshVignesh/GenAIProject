# AWS Credentials Setup - Simple Guide

## Quick Setup

1. **Edit the `aws_credentials.env` file** with your actual AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_actual_access_key_here
   AWS_SECRET_ACCESS_KEY=your_actual_secret_key_here
   AWS_DEFAULT_REGION=us-east-1
   ```

2. **Get your AWS credentials from AWS Console:**
   - Go to https://aws.amazon.com/console/
   - Sign in to your AWS account
   - Go to IAM → Users → Your Username → Security credentials
   - Click "Create access key" → Choose "Command Line Interface (CLI)"
   - Copy the Access Key ID and Secret Access Key

3. **Run the career agent:**
   ```bash
   python test_career_agent.py
   ```

## That's it! 

The system will automatically:
- ✅ Load credentials from `aws_credentials.env`
- ✅ Use AWS Bedrock for AI-powered recommendations (if credentials are valid)
- ✅ Fall back to built-in recommendations (if credentials are invalid/missing)

No complex setup needed - just edit the .env file with your real credentials!
