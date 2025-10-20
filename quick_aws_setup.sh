#!/bin/bash
# 🚀 Quick AWS Setup Script for Career Path Recommender System

echo "🚀 AWS Setup for Career Path Recommender System"
echo "================================================"

# Function to check if AWS credentials are set
check_aws_credentials() {
    if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "❌ AWS credentials not set"
        echo ""
        echo "Please set your AWS credentials:"
        echo "export AWS_ACCESS_KEY_ID=your_access_key"
        echo "export AWS_SECRET_ACCESS_KEY=your_secret_key"
        echo "export AWS_REGION=us-east-2"
        echo ""
        echo "You can get these from:"
        echo "1. AWS Console → IAM → Users → Your Username → Security credentials"
        echo "2. Click 'Create access key' → Command Line Interface (CLI)"
        return 1
    else
        echo "✅ AWS credentials are set"
        return 0
    fi
}

# Function to test AWS connection
test_aws_connection() {
    echo "🔍 Testing AWS connection..."
    python3 -c "
import boto3
try:
    client = boto3.client('bedrock-runtime')
    print('✅ AWS Bedrock connection successful')
    return True
except Exception as e:
    print(f'❌ AWS connection failed: {e}')
    return False
" 2>/dev/null
}

# Function to test Bedrock models
test_bedrock_models() {
    echo "🔍 Testing Bedrock model access..."
    python3 -c "
import boto3
try:
    client = boto3.client('bedrock-runtime')
    models = client.list_foundation_models()
    claude_models = [m for m in models.get('modelSummaries', []) if 'claude' in m.get('modelId', '').lower()]
    print(f'✅ Found {len(claude_models)} Claude models available')
    for model in claude_models[:3]:  # Show first 3
        print(f'  - {model.get(\"modelId\")}')
    return True
except Exception as e:
    print(f'❌ Bedrock model access failed: {e}')
    print('💡 Make sure to enable Claude models in AWS Bedrock Console')
    return False
" 2>/dev/null
}

# Function to test the Career Path System
test_career_system() {
    echo "🔍 Testing Career Path Recommender System..."
    python3 -c "
from main import CareerPathOrchestrator
import asyncio

async def test():
    try:
        orchestrator = CareerPathOrchestrator()
        print('✅ Career Path System initializes successfully')
        return True
    except Exception as e:
        print(f'❌ Career Path System failed: {e}')
        return False

result = asyncio.run(test())
" 2>/dev/null
}

# Main setup process
main() {
    echo ""
    echo "📋 Step 1: Checking AWS Credentials"
    if ! check_aws_credentials; then
        exit 1
    fi
    
    echo ""
    echo "📋 Step 2: Testing AWS Connection"
    if ! test_aws_connection; then
        echo ""
        echo "💡 Troubleshooting:"
        echo "1. Verify your AWS credentials are correct"
        echo "2. Check if your AWS account has Bedrock access"
        echo "3. Ensure you're using the correct region (us-east-1 recommended)"
        exit 1
    fi
    
    echo ""
    echo "📋 Step 3: Testing Bedrock Models"
    if ! test_bedrock_models; then
        echo ""
        echo "💡 Troubleshooting:"
        echo "1. Go to AWS Bedrock Console"
        echo "2. Click 'Model access' in the left sidebar"
        echo "3. Click 'Request model access'"
        echo "4. Find 'Claude 3.5 Sonnet' and click 'Request'"
        echo "5. Wait for approval (usually instant)"
        exit 1
    fi
    
    echo ""
    echo "📋 Step 4: Testing Career Path System"
    if ! test_career_system; then
        echo ""
        echo "💡 Troubleshooting:"
        echo "1. Check if all dependencies are installed: pip install -r requirements.txt"
        echo "2. Verify the system files are in the correct location"
        exit 1
    fi
    
    echo ""
    echo "🎉 SUCCESS! Your Career Path Recommender System is ready!"
    echo ""
    echo "🚀 You can now run:"
    echo "  python main.py                    # Full orchestrated system"
    echo "  python run_job_market_agent.py    # Job Market Agent only"
    echo "  python run_course_catalog_agent.py # Course Catalog Agent only"
    echo "  python run_career_matching_agent.py # Career Matching Agent only"
    echo ""
    echo "📚 For more details, see: aws_setup_guide.md"
}

# Run the main function
main
