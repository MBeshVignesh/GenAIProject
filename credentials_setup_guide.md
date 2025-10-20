# 🔐 AWS Credentials Setup Guide

## 🎯 **WHERE TO PUT YOUR AWS CREDENTIALS**

The Career Path Recommender System reads AWS credentials from **environment variables**. Here are your options:

### **Option 1: Terminal Environment Variables (Recommended)**

**No file needed** - just run these commands in your terminal:

```bash
# Set your AWS credentials (replace with your actual keys)
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1

# Test if it works
python -c "from main import CareerPathOrchestrator; print('✅ Credentials set successfully')"
```

**Pros:** ✅ Simple, secure, temporary
**Cons:** ❌ Lost when you close terminal

### **Option 2: .env File (Best for Development)**

**File:** `my_aws_credentials.env` (I created this for you)

```bash
# Edit the file with your actual credentials
nano my_aws_credentials.env

# Load the credentials
source my_aws_credentials.env

# Test if it works
python -c "from main import CareerPathOrchestrator; print('✅ Credentials loaded')"
```

**Pros:** ✅ Persistent, easy to manage, secure
**Cons:** ❌ Need to remember to load it

### **Option 3: Shell Profile (Permanent)**

**File:** `~/.zshrc` or `~/.bash_profile`

```bash
# Add to your shell profile
echo 'export AWS_ACCESS_KEY_ID=your_access_key_here' >> ~/.zshrc
echo 'export AWS_SECRET_ACCESS_KEY=your_secret_key_here' >> ~/.zshrc
echo 'export AWS_REGION=us-east-1' >> ~/.zshrc

# Reload your shell
source ~/.zshrc
```

**Pros:** ✅ Permanent, automatic
**Cons:** ❌ Global to your system

### **Option 4: Direct in Code (NOT RECOMMENDED)**

**File:** `utils/config.py` (modify line 16-17)

```python
# DON'T DO THIS - it's insecure!
self.aws_access_key_id = "your_access_key_here"  # ❌ Bad practice
self.aws_secret_access_key = "your_secret_key_here"  # ❌ Bad practice
```

**Pros:** ✅ Always works
**Cons:** ❌ Insecure, credentials in code

## 🚀 **RECOMMENDED APPROACH**

### **For Testing/Development:**
```bash
# Use Option 1 - Terminal environment variables
export AWS_ACCESS_KEY_ID=your_actual_access_key
export AWS_SECRET_ACCESS_KEY=your_actual_secret_key
export AWS_REGION=us-east-1

# Run the system
python main.py
```

### **For Production:**
```bash
# Use Option 2 - .env file
# Edit my_aws_credentials.env with your credentials
source my_aws_credentials.env
python main.py
```

## 🔧 **HOW TO GET YOUR AWS CREDENTIALS**

1. **Go to AWS Console**: https://console.aws.amazon.com/
2. **Sign in** to your AWS account
3. **Go to IAM**: IAM → Users → Your Username
4. **Click "Security credentials"** tab
5. **Click "Create access key"**
6. **Choose "Command Line Interface (CLI)"**
7. **Copy the Access Key ID and Secret Access Key**

## 🧪 **TEST YOUR SETUP**

```bash
# Test if credentials are set
python -c "
import os
print('AWS_ACCESS_KEY_ID:', 'SET' if os.environ.get('AWS_ACCESS_KEY_ID') else 'NOT SET')
print('AWS_SECRET_ACCESS_KEY:', 'SET' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'NOT SET')
print('AWS_REGION:', os.environ.get('AWS_REGION', 'NOT SET'))
"

# Test the system
python -c "from main import CareerPathOrchestrator; print('✅ System ready!')"
```

## 🎯 **QUICK START**

```bash
# 1. Set your credentials
export AWS_ACCESS_KEY_ID=your_actual_access_key
export AWS_SECRET_ACCESS_KEY=your_actual_secret_key
export AWS_REGION=us-east-1

# 2. Test the system
python -c "from main import CareerPathOrchestrator; print('✅ Ready!')"

# 3. Run the system
python main.py
```

## 🔒 **SECURITY NOTES**

- ✅ **DO:** Use environment variables
- ✅ **DO:** Use .env files (add to .gitignore)
- ❌ **DON'T:** Put credentials in code files
- ❌ **DON'T:** Commit credentials to git
- ❌ **DON'T:** Share credentials in chat/email

The system is designed to be secure and flexible! 🚀
