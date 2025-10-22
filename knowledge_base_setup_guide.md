# AWS Bedrock Knowledge Base Setup Guide

## Overview
This guide explains how to set up AWS Bedrock Knowledge Base to enhance your Course Catalog Agent with document and link ingestion capabilities.

## Prerequisites
- AWS Account with Bedrock access
- Proper IAM permissions for Bedrock Knowledge Base operations
- Documents/links you want to ingest (one-time setup)

## Step 1: Create Knowledge Base in AWS Console

### 1.1 Navigate to Bedrock Console
1. Go to AWS Console → Amazon Bedrock
2. Select your region (us-east-2 based on your config)
3. Click "Knowledge bases" in the left sidebar

### 1.2 Create Knowledge Base
1. Click "Create knowledge base"
2. Choose "Quick create" for simplicity
3. Configure:
   - **Knowledge base name**: `course-catalog-kb`
   - **Description**: `Knowledge base for course catalog and career guidance`

### 1.3 Configure Data Source
1. **Data source name**: `course-documents`
2. **S3 bucket**: Create new bucket or use existing
3. **Upload documents**: Upload your PDFs, text files, etc.
4. **Supported formats**: PDF, TXT, DOCX, CSV, HTML

### 1.4 Configure Embedding Model
- **Embedding model**: Amazon Titan Embeddings G1 - Text
- **Vector store**: Amazon OpenSearch Serverless (default)

### 1.5 Configure Access Permissions
- Use default settings or configure custom IAM role
- Ensure your agent has access to the Knowledge Base

## Step 2: Get Required ARNs and IDs

After creation, note down:
- **Knowledge Base ID**: Found in Knowledge Base details
- **Inference Profile ARN**: Create inference profile for Claude Sonnet

### 2.1 Create Inference Profile (if not exists)
1. Go to Bedrock → Inference profiles
2. Create new profile for Claude Sonnet 3.5
3. Note the ARN

## Step 3: Update Environment Configuration

Add these to your `aws_credentials.env`:

```env
# Knowledge Base Configuration
BEDROCK_KB_ID=your-knowledge-base-id-here
INFERENCE_PROFILE_ARN_SONNET=arn:aws:bedrock:us-east-2:account:inference-profile/your-profile-name

# Optional: Advanced KB settings
KB_MAX_RESULTS=5
KB_SIMILARITY_THRESHOLD=0.7
```

## Step 4: Document Ingestion Methods

### 4.1 Manual Document Upload
1. Upload PDFs, Word docs, text files to S3 bucket
2. Trigger sync in Knowledge Base console

### 4.2 Web Content Ingestion
1. Use AWS Console to add web URLs
2. Configure crawling settings
3. Set refresh frequency

### 4.3 Programmatic Ingestion
Use the provided utility functions in `kb_utils.py` for:
- Batch document uploads
- URL content ingestion
- Knowledge Base synchronization

## Step 5: Testing Knowledge Base Integration

1. Run the test script: `python test_knowledge_base.py`
2. Verify documents are ingested
3. Test retrieval functionality

## Troubleshooting

### Common Issues:
1. **Access Denied**: Check IAM permissions for Knowledge Base access
2. **Documents not found**: Verify S3 bucket permissions and document formats
3. **No citations**: Ensure documents are properly processed and indexed

### IAM Permissions Required:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:RetrieveAndGenerate",
                "bedrock:Retrieve",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## Next Steps
1. Upload your course catalog documents
2. Test the integration
3. Fine-tune retrieval parameters
4. Monitor performance and adjust as needed
