# Career Path Recommender System

A compact multi-agent project that uses AWS Bedrock (Claude Sonnet 4.5) to help students and learners get career guidance and course recommendations by combining model inference with an optional Knowledge Base.

## 🎯 Overview

This repository contains two agents and a small Streamlit chat UI that let you query career guidance and course recommendations.

### 🧩 Agents

1. Career Agent (`agents/simple_career_agent.py`) – Generates personalized career recommendations. Loads environment from `aws_credentials.env` and will attempt to call Bedrock directly; Bedrock credentials improve results but an inference profile is not strictly required for the class itself.
2. Course Catalog Agent (`agents/course_catalog_agent.py`) – Analyzes course catalog documents and optionally uses an AWS Bedrock Knowledge Base for grounded retrieval-and-generate responses. This agent requires `INFERENCE_PROFILE_ARN_SONNET` to be set and will raise if missing.

### 🚀 Features

- **Interactive Streamlit Interface** - User-friendly chat interface for career guidance (implemented in `main.py`)
- **Knowledge Base Integration** - Enhanced document retrieval with AWS Bedrock Knowledge Base
- **Course-Skill Mapping** - Maps UTD courses to career requirements with document analysis
- **Personalized Recommendations** - Generates tailored career paths and project suggestions
- **AWS Bedrock Integration** - Uses Claude Sonnet 4.5 for intelligent analysis
- **Modular Architecture** - Clean, extensible agent-based design

## 🛠️ Installation

1. Clone the repository
```bash
git clone <repository-url>
cd GenAIProject
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. Set up AWS credentials

This project loads environment variables from `aws_credentials.env` via python-dotenv. You can create that file manually or follow the helper guide in `aws_credentials_setup.md`.

Required environment variables:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION (e.g., us-east-2)

Optional (for Bedrock / Knowledge Base):
- INFERENCE_PROFILE_ARN_SONNET (required by `CourseCatalogAgent`)
- BEDROCK_KB_ID (if you want KB-backed retrieval)
- KB_MAX_RESULTS, KB_SIMILARITY_THRESHOLD, LLM_TEMPERATURE, LLM_MAX_TOKENS

4. **Configure Knowledge Base (optional)**
```bash
# Follow the knowledge_base_setup_guide.md for detailed setup
# This enables enhanced document retrieval for the Course Catalog Agent
```

## 🚀 Usage

### Streamlit Web Interface (Recommended)

```bash
# Launch the interactive web interface
streamlit run main.py
```

The UI loads either the Career Agent or Course Catalog Agent (selectable). Chat messages are persisted in the Streamlit session while the app runs.

### Independent Agent Usage

- Course Catalog Agent: `agents/course_catalog_agent.py` contains a small CLI entrypoint and can be run directly:

```bash
python agents/course_catalog_agent.py
```

- Career Agent: `agents/simple_career_agent.py` is intended to be used programmatically (import the `CareerAgent` class). Example programmatic usage is shown below.

### Programmatic Usage

```python
import asyncio
from agents.simple_career_agent import CareerAgent
from agents.course_catalog_agent import CourseCatalogAgent

async def run():
  career_agent = CareerAgent()
  career_result = await career_agent.analyze("I want to become a Data Scientist")

  # CourseCatalogAgent requires INFERENCE_PROFILE_ARN_SONNET in env
  course_agent = CourseCatalogAgent()
  course_result = await course_agent.analyze("What courses should I take for data science?")

  print('Career Guidance:\n', career_result)
  print('Course Recommendations:\n', course_result)

asyncio.run(run())
```

## 📊 Example Output

### Career Agent Response
```
Data Scientist Career Path:

• Core Skills: Python/R, SQL, Statistics, Machine Learning, Data Visualization
• Learning Path: 
  - Python fundamentals and data manipulation (pandas, numpy)
  - Statistics and probability
  - Machine learning algorithms and frameworks (scikit-learn, TensorFlow)
  - Data visualization (matplotlib, seaborn, Tableau)
• Projects: Kaggle competitions, personal data analysis projects
• Certifications: Google Data Analytics, AWS Machine Learning Specialty
• Timeline: 6-12 months for entry-level positions
```

### Course Catalog Agent Response
```
CS 6375 - Machine Learning
This course covers supervised and unsupervised learning algorithms, model evaluation, and practical applications using Python and scikit-learn.

CS 6360 - Database Design  
Focuses on relational database design, SQL optimization, and data modeling for large-scale applications.

CS 6350 - Big Data Management and Analytics
Covers distributed computing frameworks, data processing pipelines, and analytics on large datasets.
```

## 🏗️ Project layout

```
main.py                        # Streamlit web UI (chat)
agents/                        # Agent implementations
  ├─ simple_career_agent.py    # Career guidance (programmatic use)
  └─ course_catalog_agent.py   # Course catalog agent (KB-backed, has CLI entrypoint)
aws_credentials.env             # Environment file (loaded by python-dotenv)
aws_credentials_setup.md        # Instructions for creating credentials file
knowledge_base_setup_guide.md   # Knowledge Base setup guide
requirements.txt                # Python dependencies
docker-compose.yml, Dockerfile  # Optional containerization / deploy helpers
```


### Configuration

Environment variables are loaded from `aws_credentials.env` (via python-dotenv). The key settings are:

- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION (required)
- INFERENCE_PROFILE_ARN_SONNET (required by `CourseCatalogAgent`)
- BEDROCK_KB_ID (optional; set to enable KB-backed retrieval)
- KB_MAX_RESULTS, KB_SIMILARITY_THRESHOLD, LLM_TEMPERATURE, LLM_MAX_TOKENS

### AWS Bedrock Setup

1. Enable Claude Sonnet 4.5 in your AWS Bedrock console
2. Ensure your AWS credentials have Bedrock access
3. For Knowledge Base integration, follow `knowledge_base_setup_guide.md`

## 📚 Knowledge Base Integration

`CourseCatalogAgent` supports retrieving documents from an AWS Bedrock Knowledge Base (Retrieve & Generate). When `BEDROCK_KB_ID` is set the agent will return grounded responses and append detected sources. See `knowledge_base_setup_guide.md` for step-by-step setup.

## 🤖 Agent Details

### Career Agent
- Generates personalized career recommendations using Claude Sonnet 4.5
- Intended for programmatic usage (import the class and call `analyze()`)

### Course Catalog Agent
- Analyzes course descriptions and can perform KB-backed retrieval-and-generate (grounded answers + citations)
- Requires `INFERENCE_PROFILE_ARN_SONNET` to be set for direct Sonnet invocations

## 📈 Workflow

1. **User Query** → Input career goal or course question via Streamlit interface
2. **Agent Selection** → Choose between Career Agent or Course Catalog Agent
3. **Analysis** → Agent processes query using Claude Sonnet 4.5
4. **Knowledge Retrieval** → Course Catalog Agent optionally uses Knowledge Base for document retrieval
5. **Response** → Generate personalized recommendations and guidance

## 🔍 Example Queries

**Career Agent:**
- "I want to become a Data Scientist - what should I do?"
- "What projects should I build for machine learning roles?"
- "How do I transition from software engineering to AI/ML?"
- "What skills are most important for cloud engineering?"

**Course Catalog Agent:**
- "What courses should I take for data science?"
- "Tell me about CS 6375 Machine Learning"
- "What are the prerequisites for CS 6360 Database Design?"
- "Show me all the AI/ML related courses available"

## 🛡️ Security & Best Practices

- AWS credentials stored in environment variables
- Secure Knowledge Base integration with proper IAM permissions
- Error handling and comprehensive logging
- Modular, testable architecture
- Clean separation of concerns
- Streamlit session management for web interface

## 🚧 Development

### Running Tests
If there are tests present, run:

```bash
pytest
```

### Code Formatting

```bash
black .
flake8 .
```

### Adding New Agents
1. Create new agent class with `analyze()` method
2. Implement AWS Bedrock integration
3. Add to Streamlit interface in `main.py`
4. Update documentation

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please open an issue on GitHub or contact the development team.