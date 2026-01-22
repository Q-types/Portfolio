"""
MAIT - AI-Powered Adaptive Lesson Planner
==========================================

An intelligent lesson planning tool for AQA GCSE Science that generates 
differentiated, pedagogically-sound lesson plans using AI and evidence-based 
teaching practices from PGCE training.

Author: [Your Name]
Date: 2024
"""

import openai
import json
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found. Please set it in the .env file.")

openai.api_key = api_key

# Ensure output directories exist
os.makedirs("../generated_lesson_plans", exist_ok=True)


class LessonPlanner:
    """
    Generates adaptive lesson plans with differentiated tasks for different 
    attainment levels using AI and PGCE best practices.
    """
    
    # Map subjects to syllabus files
    SYLLABUS_FILES = {
        "physics": "../data/syllabus/syllabus_aqa_physics.json",
        "chemistry": "../data/syllabus/syllabus_aqa_chemistry.json",
        "biology": "../data/syllabus/syllabus_aqa_biology.json"
    }
    
    ATTAINMENT_LEVELS = ["High Attainers", "Mid Attainers", "Low Attainers", "SEN Students"]
    
    def __init__(self):
        """Initialize the lesson planner with necessary data structures."""
        self.general_structure = self._load_general_structure()
        self.teaching_techniques = self._load_teaching_techniques()
    
    def _load_syllabus(self, file_path):
        """Load syllabus data from JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Syllabus file not found: {file_path}")
        with open(file_path, 'r') as file:
            return json.load(file)
    
    def _load_general_structure(self):
        """Load general lesson structure from JSON file."""
        file_path = '../data/teaching_techniques/general_lesson_structure.json'
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"General lesson structure file not found: {file_path}")
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('general_lesson_structure', [])
    
    def _load_teaching_techniques(self):
        """Load all teaching techniques from JSON files."""
        techniques = {}
        technique_files = [
            'curriculum_planning.json',
            'explaining_and_modelling.json',
            'questioning_and_feedback.json',
            'practice_and_retrieval.json',
            'mode_b_teaching.json',
            'scaffolding.json',
            'differentiation.json'
        ]
        
        for file in technique_files:
            file_path = f'../data/teaching_techniques/{file}'
            if not os.path.exists(file_path):
                print(f"Warning: Teaching technique file not found: {file_path}")
                continue
            with open(file_path, 'r') as f:
                data = json.load(f)
                techniques[file.split('.')[0]] = data.get('techniques', [])
        
        return techniques
    
    def _generate_content_with_retry(self, prompt, max_retries=3):
        """
        Generate content using OpenAI API with retry logic for rate limits.
        
        Args:
            prompt (str): The prompt to send to the API
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: Generated content from the API
        """
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert lesson planner for AQA GCSE Science in the United Kingdom, trained in PGCE best practices."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                
                content = response['choices'][0]['message']['content'].strip()
                if not content:
                    raise ValueError("No content found in the response.")
                
                print(f"✓ Content generated successfully")
                return content
                
            except openai.error.RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 60 * (attempt + 1)
                    print(f"Rate limit exceeded. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    return f"Error: Rate limit exceeded after {max_retries} attempts."
                    
            except openai.error.OpenAIError as e:
                return f"Error generating content: {e}"
                
            except Exception as e:
                return f"Unexpected error: {e}"
        
        return "Error: Failed to generate content after multiple attempts."
    
    def _generate_differentiated_tasks(self, section_name, subject, chapter, chapter_content):
        """
        Generate differentiated tasks for different attainment levels.
        
        Args:
            section_name (str): Name of the lesson section
            subject (str): Subject name (e.g., Biology, Chemistry, Physics)
            chapter (str): Chapter reference (e.g., 4.1.3.2)
            chapter_content (dict): Content from the syllabus
            
        Returns:
            dict: Differentiated tasks for each attainment level
        """
        tasks = {}
        
        for level in self.ATTAINMENT_LEVELS:
            print(f"  Generating tasks for {level}...")
            
            prompt = f"""
Create differentiated tasks for {level} in the {section_name} section of a lesson on {subject}, chapter {chapter}.

Topic Content: {chapter_content.get('content', 'N/A')}

Requirements:
1. Tasks should be appropriate for {level} ability level
2. Include scaffolding techniques to support their learning
3. Reference specific PGCE teaching strategies where applicable
4. Make tasks engaging and relevant to GCSE science
5. Ensure tasks align with AQA assessment objectives

Provide 2-3 specific, actionable tasks with clear instructions.
"""
            
            tasks[level] = self._generate_content_with_retry(prompt)
        
        return tasks
    
    def generate_lesson_plan(self, subject, chapter):
        """
        Generate a complete lesson plan for a given subject and chapter.
        
        Args:
            subject (str): Subject name (Biology, Chemistry, or Physics)
            chapter (str): Chapter reference from AQA syllabus
            
        Returns:
            dict: Complete lesson plan with all sections and differentiated tasks
        """
        print(f"\n{'='*60}")
        print(f"Generating Lesson Plan: {subject} - Chapter {chapter}")
        print(f"{'='*60}\n")
        
        # Load syllabus
        syllabus_file = self.SYLLABUS_FILES.get(subject.lower())
        if not syllabus_file:
            raise ValueError(f"Syllabus file not found for subject: {subject}")
        
        syllabus = self._load_syllabus(syllabus_file)
        chapter_content = syllabus.get(chapter, {})
        
        if not chapter_content:
            raise ValueError(f"Chapter {chapter} not found in {subject} syllabus")
        
        content = chapter_content.get('content', '')
        skills_development = chapter_content.get('Key opportunities for skills development', '')
        
        lesson_plan = {}
        
        # Generate each section of the lesson
        for idx, section in enumerate(self.general_structure, 1):
            section_name = section['section']
            print(f"\n[{idx}/{len(self.general_structure)}] Generating: {section_name}")
            print("-" * 60)
            
            # Build the prompt for this section
            prompt = f"""
Create the {section_name} section for an AQA GCSE Science lesson on {subject}, chapter {chapter}.

Syllabus Content: {content}

Skills Development Focus: {skills_development}

Section Guidelines:
- Definition: {section['meaning_content'].get('definition', 'No definition provided.')}
- Expected Content: {section['meaning_content'].get('content', 'No content provided.')}
- Pedagogical Importance: {section['meaning_content'].get('importance', 'No importance provided.')}

Please provide:
1. Detailed content for this section (3-5 paragraphs)
2. Specific activities or teaching strategies
3. How this section connects to AQA assessment objectives
4. Any key questions or discussion points
"""
            
            # Add hinge point question if applicable
            if 'hinge_point_question' in section:
                prompt += f"""
5. A hinge point question to assess understanding:
   - Create a diagnostic question that reveals student understanding
   - Provide the correct answer with brief explanation
"""
            
            # Generate main content for the section
            section_content = self._generate_content_with_retry(prompt)
            
            # Generate differentiated tasks
            differentiated_tasks = self._generate_differentiated_tasks(
                section_name, subject, chapter, chapter_content
            )
            
            lesson_plan[section_name] = {
                "content": section_content,
                "differentiated_tasks": differentiated_tasks
            }
        
        # Save the lesson plan
        self._save_lesson_plan_json(lesson_plan, subject, chapter)
        self._save_lesson_plan_pdf(lesson_plan, subject, chapter)
        
        print(f"\n{'='*60}")
        print(f"✓ Lesson plan generated successfully!")
        print(f"{'='*60}\n")
        
        return lesson_plan
    
    def _save_lesson_plan_json(self, lesson_plan, subject, chapter):
        """Save lesson plan as JSON file."""
        filename = f"../generated_lesson_plans/{subject}_{chapter}_lesson_plan.json".replace(" ", "_")
        with open(filename, 'w') as file:
            json.dump(lesson_plan, file, indent=4)
        print(f"\n✓ JSON saved: {filename}")
    
    def _save_lesson_plan_pdf(self, lesson_plan, subject, chapter):
        """Save lesson plan as PDF file."""
        filename = f"../generated_lesson_plans/{subject}_{chapter}_lesson_plan.pdf".replace(" ", "_")
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y_position = height - 40
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, y_position, f"Lesson Plan: {subject} - Chapter {chapter}")
        y_position -= 40
        
        c.setFont("Helvetica", 10)
        
        # Content
        for section, data in lesson_plan.items():
            # Section heading
            c.setFont("Helvetica-Bold", 12)
            c.drawString(30, y_position, f"{section}")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            
            # Section content
            text = data.get('content', '')
            lines = text.split('\n')
            for line in lines:
                # Wrap long lines
                if len(line) > 90:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 90:
                            current_line += word + " "
                        else:
                            c.drawString(50, y_position, current_line)
                            y_position -= 15
                            current_line = word + " "
                            if y_position < 40:
                                c.showPage()
                                y_position = height - 40
                                c.setFont("Helvetica", 10)
                    if current_line:
                        c.drawString(50, y_position, current_line)
                        y_position -= 15
                else:
                    c.drawString(50, y_position, line[:90])
                    y_position -= 15
                
                if y_position < 40:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 10)
            
            y_position -= 10
        
        c.save()
        print(f"✓ PDF saved: {filename}")


def main():
    """
    Main function to demonstrate lesson planner usage.
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       MAIT - AI-Powered Adaptive Lesson Planner             ║
║       for AQA GCSE Science                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Example usage
    planner = LessonPlanner()
    
    # Generate a lesson plan
    # Example: Biology Chapter 4.1.3.2
    subject = "Biology"
    chapter = "4.1.3.2"
    
    try:
        lesson_plan = planner.generate_lesson_plan(subject, chapter)
        print("\nLesson plan keys:", list(lesson_plan.keys()))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
