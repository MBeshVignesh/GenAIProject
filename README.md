# Career Path Recommender System

A production-grade multi-agent system using **AWS Bedrock Claude Sonnet 4.5** to help UTD students make informed career decisions by connecting course catalog data and personalized career recommendations.

## 🎯 Overview

This system consists of two specialized AI agents that work together to provide comprehensive career guidance:

### 🧩 Agents

1. **Career Agent** - Generates personalized career recommendations and project suggestions using Claude Sonnet 4.5
2. **Course Catalog Agent** - Analyzes UTD course catalog with Knowledge Base integration for enhanced document retrieval

### 🚀 Features

- **Interactive Streamlit Interface** - User-friendly chat interface for career guidance
- **Knowledge Base Integration** - Enhanced document retrieval with AWS Bedrock Knowledge Base
- **Course-Skill Mapping** - Maps UTD courses to career requirements with document analysis
- **Personalized Recommendations** - Generates tailored career paths and project suggestions
- **AWS Bedrock Integration** - Uses Claude Sonnet 4.5 for intelligent analysis
- **Modular Architecture** - Clean, extensible agent-based design

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd career-path-recommender
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up AWS credentials**
```bash
# Copy the credentials template
cp aws_credentials.env.example aws_credentials.env

# Edit aws_credentials.env with your credentials
# Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
# Optional: INFERENCE_PROFILE_ARN_SONNET, BEDROCK_KB_ID for Knowledge Base
```

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

This opens a web interface where you can:
- Choose between Career Agent and Course Catalog Agent
- Chat with the selected agent
- Get personalized career guidance and course recommendations

### Independent Agent Usage

Each agent can run independently:

```bash
# Run Career Agent independently
python agents/simple_career_agent.py

# Run Course Catalog Agent independently  
python agents/course_catalog_agent.py
```

### Programmatic Usage

```python
from agents.simple_career_agent import CareerAgent
from agents.course_catalog_agent import CourseCatalogAgent
import asyncio

async def run_agents():
    # Career Agent
    career_agent = CareerAgent()
    career_result = await career_agent.analyze("I want to become a Data Scientist")
    
    # Course Catalog Agent
    course_agent = CourseCatalogAgent()
    course_result = await course_agent.analyze("What courses should I take for data science?")
    
    print("Career Guidance:", career_result)
    print("Course Recommendations:", course_result)

asyncio.run(run_agents())
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

## 🏗️ Architecture

```
main.py                        # Streamlit web interface
├── agents/
│   ├── simple_career_agent.py    # Career guidance agent
│   └── course_catalog_agent.py   # Course catalog analysis with KB
├── utils/                     # Utility functions
├── aws_credentials.env         # AWS configuration
├── knowledge_base_setup_guide.md # KB setup instructions
└── requirements.txt           # Dependencies
```

## 🔧 Configuration

### Environment Variables

**Required:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (default: us-east-2)

**Optional (for Knowledge Base):**
- `INFERENCE_PROFILE_ARN_SONNET` - Inference profile ARN for Claude Sonnet 4.5
- `BEDROCK_KB_ID` - Knowledge Base ID for enhanced document retrieval
- `KB_MAX_RESULTS` - Maximum retrieval results (default: 5)
- `KB_SIMILARITY_THRESHOLD` - Similarity threshold for retrieval (default: 0.7)

### AWS Bedrock Setup

1. Enable Claude Sonnet 4.5 in your AWS Bedrock console
2. Ensure your AWS credentials have Bedrock access
3. For Knowledge Base integration, follow `knowledge_base_setup_guide.md`

## 📚 Knowledge Base Integration

The Course Catalog Agent supports AWS Bedrock Knowledge Base integration for enhanced document retrieval:

### Features
- **Document Ingestion** - Upload course catalogs, syllabi, and academic documents
- **Semantic Search** - Find relevant courses using natural language queries
- **Citation Support** - Responses include source document references
- **Flexible Configuration** - Works with or without Knowledge Base

### Setup
1. Follow the detailed guide in `knowledge_base_setup_guide.md`
2. Configure `BEDROCK_KB_ID` and `INFERENCE_PROFILE_ARN_SONNET` in your environment
3. Upload your course documents to the Knowledge Base
4. The agent automatically uses Knowledge Base when available

### Benefits
- More accurate course recommendations based on actual course content
- Better understanding of prerequisites and course relationships
- Enhanced context for complex academic queries

## 🤖 Agent Details

### Career Agent
- Generates personalized career recommendations using Claude Sonnet 4.5
- Provides actionable career guidance and project suggestions
- Offers empathetic, practical career coaching
- Creates learning roadmaps and skill development plans

### Course Catalog Agent
- Analyzes UTD course descriptions with Knowledge Base integration
- Maps courses to skills and competencies using document retrieval
- Provides detailed course information and prerequisites
- Supports both direct Claude invocation and Knowledge Base retrieval

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
```bash
pytest tests/
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