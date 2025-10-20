# Career Path Recommender System

A production-grade multi-agent system using the **Strands Framework** and **AWS Bedrock Claude Sonnet 4.5** to help UTD students make informed career decisions by connecting job market data, course catalog, and personalized recommendations.

## 🎯 Overview

This system consists of three autonomous AI agents that work together to provide comprehensive career guidance:

### 🧩 Agents

1. **Job Market Agent** - Scrapes and analyzes job postings from LinkedIn, Indeed, and Glassdoor
2. **Course Catalog Agent** - Analyzes UTD course catalog and maps courses to skills
3. **Career Matching Agent** - Generates personalized recommendations and project suggestions

### 🚀 Features

- **Real-time Job Market Analysis** - Scrapes job postings and identifies trending skills
- **Course-Skill Mapping** - Maps UTD courses to career requirements
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
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

4. **Configure Bedrock model (optional)**
```bash
export BEDROCK_CLAUDE_SONNET_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

## 🚀 Usage

### Independent Agent Usage

Each agent can now run completely independently:

```bash
# Run Job Market Agent independently
python run_job_market_agent.py

# Run Course Catalog Agent independently  
python run_course_catalog_agent.py

# Run Career Matching Agent independently
python run_career_matching_agent.py
```

### Orchestrated Usage

```bash
# Run the main system with agent selection
python main.py
```

### Programmatic Usage

```python
from agents.job_market_agent import JobMarketAgent
from agents.course_catalog_agent import CourseCatalogAgent
from agents.career_matching_agent import CareerMatchingAgent
import asyncio

async def run_independent_agents():
    # Job Market Agent
    job_agent = JobMarketAgent()
    job_result = await job_agent.run_independent_analysis("Data Scientist")
    
    # Course Catalog Agent
    course_agent = CourseCatalogAgent()
    course_result = await course_agent.run_independent_analysis("Data Scientist")
    
    # Career Matching Agent
    career_agent = CareerMatchingAgent()
    career_result = await career_agent.run_independent_analysis(
        "What projects should I do for data science?",
        "Data Scientist"
    )

asyncio.run(run_independent_agents())
```

## 📊 Example Output

```json
{
  "user_query": "for data science roles, what projects i have to do",
  "career_goal": "Data Scientist",
  "recommended_courses": [
    "CS 6375 - Machine Learning",
    "CS 6360 - Database Design",
    "CS 6350 - Big Data Management and Analytics"
  ],
  "projects": [
    "End-to-end ML pipeline on AWS",
    "Model deployment with SageMaker",
    "Real-time data processing with Spark"
  ],
  "frameworks_to_learn": [
    "TensorFlow",
    "PyTorch", 
    "AWS SageMaker",
    "Apache Spark"
  ],
  "portfolio_guidance": "Build 2-3 projects showing model training + deployment"
}
```

## 🏗️ Architecture

```
main.py
├── agents/
│   ├── base_agent.py          # Base StrandAgent class
│   ├── job_market_agent.py    # Job market analysis
│   ├── course_catalog_agent.py # Course catalog analysis
│   └── career_matching_agent.py # Career recommendations
├── utils/
│   ├── config.py              # Configuration management
│   └── logger.py              # Logging setup
└── requirements.txt           # Dependencies
```

## 🔧 Configuration

### Environment Variables

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (default: us-east-1)
- `BEDROCK_CLAUDE_SONNET_MODEL_ID` - Claude model ID
- `LOG_LEVEL` - Logging level (default: INFO)
- `SCRAPING_DELAY` - Delay between requests (default: 1.0)

### AWS Bedrock Setup

1. Enable Claude Sonnet 4.5 in your AWS Bedrock console
2. Ensure your AWS credentials have Bedrock access
3. Configure the model ID in your environment

## 🤖 Agent Details

### Job Market Agent
- Scrapes job postings from multiple sources
- Extracts skills, requirements, and salary data
- Identifies trending technologies and demand patterns

### Course Catalog Agent
- Analyzes UTD course descriptions and prerequisites
- Maps courses to skills and competencies
- Identifies learning paths and dependencies

### Career Matching Agent
- Coordinates with other agents
- Generates personalized recommendations
- Creates learning roadmaps and project suggestions

## 📈 Workflow

1. **User Query** → Input career goal and specific question
2. **Job Market Analysis** → Scrape and analyze job postings
3. **Course Analysis** → Map courses to career requirements
4. **Career Matching** → Generate personalized recommendations
5. **Output** → Comprehensive career guidance with actionable steps

## 🔍 Example Queries

- "What courses should I take for data science?"
- "What projects should I build for machine learning roles?"
- "How do I prepare for cloud engineering positions?"
- "What skills are in demand for software engineering?"

## 🛡️ Security & Best Practices

- AWS credentials stored as environment variables
- Rate limiting for web scraping
- Error handling and logging
- Modular, testable architecture
- Clean separation of concerns

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
1. Inherit from `BaseStrandAgent`
2. Implement required abstract methods
3. Add to orchestrator workflow
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