# AWS Bedrock Multi-Modal Application Setup Guide

This guide will help you set up and run the integrated AWS Bedrock multi-modal application with both backend and frontend components.

## 📁 Project Structure

```
bedrock-multimodal-app/
├── app.py                 # Backend server (integrated_backend_server)
├── index.html            # Frontend web interface
├── requirements.txt      # Python dependencies
├── README.md            # This setup guide
├── generated_images/    # Output directory for images
├── generated_speech/    # Output directory for audio files
└── logs/               # Application logs
```

## 🔧 Prerequisites

### 1. AWS Setup
- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Access to AWS Bedrock service
- Access to AWS Polly service

### 2. Required AWS Permissions
Your AWS user/role needs the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "polly:SynthesizeSpeech",
                "polly:DescribeVoices"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Enable Bedrock Models
In the AWS Console, go to Amazon Bedrock and enable access to:
- Amazon Nova Pro
- Amazon Nova Sonic  
- Amazon Nova Canvas
- Amazon Nova Micro
- Amazon Titan Image Generator

### 4. System Requirements
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)
- FFmpeg (optional, for MP4 audio conversion)

## 🚀 Installation & Setup

### Step 1: Install Python Dependencies

Create a `requirements.txt` file:
```txt
boto3>=1.34.0
botocore>=1.34.0
flask>=2.3.0
flask-cors>=4.0.0
requests>=2.31.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Configure AWS Credentials

Option A - AWS CLI:
```bash
aws configure
```

Option B - Environment Variables:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Option C - IAM Role (for EC2 instances)
- Attach appropriate IAM role to your EC2 instance

### Step 3: Optional - Install FFmpeg
For MP4 audio conversion support:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

## 🏃‍♂️ Running the Application

### Method 1: Integrated Server (Recommended)

1. Start the backend server:
```bash
python app.py server
```

2. Open your web browser and navigate to:
```
http://localhost:8080
```

3. The application will automatically detect if the backend is running

### Method 2: Development Mode

1. Start backend on custom port:
```bash
python app.py server 8081 0.0.0.0
```

2. If serving frontend separately, update the API_BASE_URL in index.html:
```javascript
const API_BASE_URL = 'http://localhost:8081'
```