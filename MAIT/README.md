# MAIT - AI-Powered Adaptive Lesson Planner

## 🎓 Overview

**MAIT (My AI Teaching Assistant)** is an intelligent lesson planning system designed for AQA GCSE Science teachers. It leverages artificial intelligence and evidence-based PGCE teaching practices to generate comprehensive, differentiated lesson plans that adapt to diverse student needs.

### Key Features

- **🤖 AI-Powered Content Generation**: Uses OpenAI's GPT models to generate contextually relevant lesson content
- **📚 PGCE Best Practices**: Embeds evidence-based teaching techniques from UK teacher training
- **🎯 Differentiated Learning**: Automatically creates tasks for four attainment levels:
  - High Attainers
  - Mid Attainers
  - Low Attainers
  - SEN (Special Educational Needs) Students
- **📖 AQA Syllabus Aligned**: Directly references official AQA GCSE Science specifications
- **🔄 Adaptive Teaching**: Provides multiple pathways through lesson stages
- **📄 Multiple Output Formats**: Generates both JSON and PDF lesson plans

---

## 🎯 Project Goals

This project addresses a critical challenge in education: **creating high-quality, differentiated lesson plans that meet the needs of all learners while maintaining alignment with curriculum standards.**

### Educational Philosophy

The system is built on three pedagogical pillars:

1. **Backward Design** - Starting with learning objectives and assessment criteria
2. **Differentiation** - Recognizing that students learn at different paces and in different ways
3. **Evidence-Based Practice** - Incorporating research-backed teaching strategies from PGCE training

---

## 🏗️ Architecture

### System Components

```
MAIT-Portfolio/
│
├── src/
│   └── lesson_planner.py          # Core lesson planning engine
│
├── data/
│   ├── syllabus/                  # AQA GCSE syllabus data (Biology, Chemistry, Physics)
│   │   ├── syllabus_aqa_biology.json
│   │   ├── syllabus_aqa_chemistry.json
│   │   └── syllabus_aqa_physics.json
│   │
│   └── teaching_techniques/       # PGCE teaching strategies
│       ├── general_lesson_structure.json
│       ├── curriculum_planning.json
│       ├── explaining_and_modelling.json
│       ├── questioning_and_feedback.json
│       ├── practice_and_retrieval.json
│       ├── mode_b_teaching.json
│       ├── scaffolding.json
│       └── differentiation.json
│
├── examples/                      # Sample generated lesson plans
│   ├── Biology_4.1.3.2_lesson_plan.json
│   └── Physics_4.1.1.1_lesson_plan.json
│
├── docs/                         # Additional documentation
│   ├── PORTFOLIO_NOTES.md        # Detailed project notes
│   └── TEACHING_TECHNIQUES.md    # Explanation of pedagogical approaches
│
└── generated_lesson_plans/       # Output directory (created at runtime)
```

### Lesson Structure

Each generated lesson follows a research-backed structure:

1. **Lesson Objectives** - Clear, measurable learning outcomes
2. **Recall/Starter** - Activates prior knowledge
3. **New Knowledge** - Core content delivery with teaching strategies
4. **Connection to Real World** - Practical applications and relevance
5. **Apply to Demonstrate** - Practice activities and assessment
6. **Lesson Summary** - Consolidation and key takeaways
7. **Past Exam Questions** - AQA-style assessment practice
8. **Questions and Answers** - Formative assessment tools

---

## 🚀 Getting Started

### Prerequisites

```bash
Python 3.8+
pip (Python package manager)
OpenAI API key
```

### Installation

1. **Clone or download this repository**

```bash
cd MAIT-Portfolio
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the `src/` directory:

```env
OPENAI_API_KEY=your_api_key_here
```

⚠️ **Important**: Never commit your `.env` file to version control!

### Usage

#### Basic Usage

```python
from lesson_planner import LessonPlanner

# Initialize the planner
planner = LessonPlanner()

# Generate a lesson plan
lesson_plan = planner.generate_lesson_plan(
    subject="Biology",
    chapter="4.1.3.2"  # AQA chapter reference
)
```

#### Command Line Usage

```bash
cd src
python lesson_planner.py
```

This will generate example lesson plans with output in both JSON and PDF formats.

---

## 📊 Lesson Plan Output

### JSON Structure

```json
{
  "Lesson Objectives": {
    "content": "Detailed objectives...",
    "differentiated_tasks": {
      "High Attainers": "Advanced tasks...",
      "Mid Attainers": "Standard tasks...",
      "Low Attainers": "Supported tasks...",
      "SEN Students": "Accessible tasks with scaffolding..."
    }
  },
  "Recall/Starter": { ... },
  "New Knowledge": { ... },
  ...
}
```

### Example Output

See the `examples/` folder for complete generated lesson plans:
- `Biology_4.1.3.2_lesson_plan.json` - Cell Biology lesson
- `Physics_4.1.1.1_lesson_plan.json` - Energy lesson

---

## 🎓 Pedagogical Approach

### PGCE Teaching Techniques Embedded

#### 1. **Curriculum Planning**
- Backward Design
- Curriculum Mapping
- Interleaving and Spacing
- Knowledge Organizers
- Sequencing Learning

#### 2. **Explaining and Modelling**
- Dual Coding (visual + verbal)
- Worked Examples
- I-We-You Method (gradual release)
- Cognitive Load Management
- Conceptual Modelling

#### 3. **Questioning and Feedback**
- Cold Calling
- Socratic Questioning
- Think-Pair-Share
- Effective Questioning Techniques
- Feedback Loops

#### 4. **Practice and Retrieval**
- Retrieval Practice
- Spacing and Interleaving
- Deliberate Practice
- Quizzing and Testing
- Distributed Practice

#### 5. **Mode B Teaching**
- Flipped Classroom
- Project-Based Learning
- Independent Study
- Peer Teaching
- Inquiry-Based Learning

#### 6. **Scaffolding Techniques**
- Breaking Down Tasks
- Providing Hints
- Visual Aids
- Feedback and Encouragement

#### 7. **Differentiation Strategies**
- Varied Instructional Approaches
- Multiple Means of Engagement
- Different Modes of Assessment
- Flexible Grouping

For detailed explanations, see `docs/TEACHING_TECHNIQUES.md`

---

## 🔍 How It Works

### 1. **Syllabus Analysis**
The system loads AQA GCSE Science syllabuses (Biology, Chemistry, Physics) structured by chapter references.

### 2. **Prompt Engineering**
For each lesson section, the system constructs detailed prompts that include:
- Syllabus content
- Skills development opportunities
- Section-specific pedagogical guidance
- Differentiation requirements

### 3. **AI Content Generation**
OpenAI's GPT-3.5-turbo generates:
- Lesson content aligned with learning objectives
- Teaching activities and strategies
- Differentiated tasks for each attainment level
- Assessment questions

### 4. **Quality Assurance**
- Retry logic for API rate limits
- Content validation
- Error handling and logging

### 5. **Multi-Format Output**
- JSON for programmatic access and integration
- PDF for printing and traditional lesson planning

---

## 💡 Use Cases

### For Teachers
- **Save time**: Generate comprehensive lesson plans in minutes instead of hours
- **Ensure quality**: All plans follow PGCE best practices and curriculum standards
- **Differentiate easily**: Automatically receive tasks for all ability levels
- **Stay current**: Plans include real-world applications and modern examples

### For Teacher Training
- **Model best practice**: Demonstrates how to structure effective lessons
- **Show differentiation**: Provides concrete examples of adapting content
- **Integrate technology**: Illustrates AI-assisted teaching
- **Research tool**: Analyze generated content for pedagogical insights

### For Curriculum Development
- **Consistency**: Ensure all lessons follow the same high-quality structure
- **Alignment**: Maintain direct links to curriculum specifications
- **Scalability**: Generate entire schemes of work efficiently
- **Version control**: Track changes and improvements over time

---

## 🔧 Technical Stack

- **Language**: Python 3.8+
- **AI Model**: OpenAI GPT-3.5-turbo
- **PDF Generation**: ReportLab
- **Data Format**: JSON
- **Environment Management**: python-dotenv
- **API Integration**: OpenAI Python Library

---

## 📈 Future Enhancements

### Planned Features
- [ ] Interactive web interface
- [ ] PowerPoint generation
- [ ] Student assessment tracking
- [ ] Lesson customization GUI
- [ ] Export to Google Classroom / MS Teams
- [ ] Multi-language support
- [ ] Offline mode with pre-generated templates
- [ ] Lesson effectiveness analytics
- [ ] Collaborative lesson planning
- [ ] Integration with school MIS systems

### Research Directions
- Analyze effectiveness of AI-generated vs. teacher-created lessons
- Study impact on teacher workload and wellbeing
- Evaluate student outcomes with differentiated materials
- Explore personalization at individual student level

---

## 📝 Requirements

```
openai==0.27.0
reportlab==4.2.0
python-dotenv==0.21.0
```

---

## ⚖️ License

This project is provided for educational and portfolio purposes.

---

## 👤 Author

**[Your Name]**
- Portfolio Project
- Created: 2024
- Focus: AI in Education, Adaptive Learning, PGCE Best Practices

---

## 🙏 Acknowledgments

- **AQA Examination Board** - For comprehensive GCSE Science specifications
- **PGCE Training Programs** - For evidence-based teaching methodologies
- **OpenAI** - For GPT-3.5-turbo API enabling intelligent content generation
- **Teaching Community** - For feedback and real-world insights

---

## 📚 Further Reading

- [AQA GCSE Science Specifications](https://www.aqa.org.uk/subjects/science/gcse)
- [Evidence-Based Teaching Strategies](https://educationendowmentfoundation.org.uk/education-evidence/teaching-learning-toolkit)
- [Differentiated Instruction](https://www.understood.org/en/articles/differentiated-instruction-what-you-need-to-know)
- [AI in Education](https://www.oecd.org/education/artificial-intelligence-in-education/)

---

## 📧 Contact

For questions, suggestions, or collaboration opportunities, please reach out via your preferred contact method.

---

**Note**: This is a demonstration project showcasing the integration of AI technology with evidence-based teaching practices. Always review and adapt generated content to your specific classroom context and student needs.
