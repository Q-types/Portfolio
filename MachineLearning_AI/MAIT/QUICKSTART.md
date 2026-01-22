# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up API Key

1. Get an OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. Create a `.env` file in the `src/` directory:

```bash
cd src
cp .env.example .env
```

3. Edit `.env` and add your API key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Run the Lesson Planner

```bash
cd src
python lesson_planner.py
```

This will generate an example lesson plan for Biology Chapter 4.1.3.2.

### Step 4: View Your Lesson Plan

Check the `generated_lesson_plans/` directory for:
- **JSON file**: `Biology_4.1.3.2_lesson_plan.json` (structured data)
- **PDF file**: `Biology_4.1.3.2_lesson_plan.pdf` (printable format)

---

## 🎯 Custom Lesson Plans

### Option 1: Modify the Script

Edit `lesson_planner.py` and change these lines at the bottom:

```python
subject = "Biology"  # Change to "Chemistry" or "Physics"
chapter = "4.1.3.2"  # Change to any AQA chapter code
```

### Option 2: Use as a Module

```python
from lesson_planner import LessonPlanner

planner = LessonPlanner()

# Generate lesson for Physics
lesson = planner.generate_lesson_plan(
    subject="Physics",
    chapter="4.1.1.1"
)

# Generate lesson for Chemistry
lesson = planner.generate_lesson_plan(
    subject="Chemistry",
    chapter="4.2.1.1"
)
```

---

## 📖 Available Subjects and Chapters

### Biology
- Check `data/syllabus/syllabus_aqa_biology.json` for chapter codes
- Example: `4.1.3.2` (Cell specialisation)

### Chemistry
- Check `data/syllabus/syllabus_aqa_chemistry.json` for chapter codes
- Example: `4.2.1.1` (Atoms, elements and compounds)

### Physics
- Check `data/syllabus/syllabus_aqa_physics.json` for chapter codes
- Example: `4.1.1.1` (Energy stores and systems)

---

## 🔧 Troubleshooting

### "OpenAI API key not found"
- Make sure your `.env` file is in the `src/` directory
- Check that the API key is correctly formatted (starts with `sk-`)

### "Rate limit exceeded"
- The script includes automatic retry logic
- If it persists, wait a few minutes and try again
- Consider upgrading your OpenAI API plan

### "Syllabus file not found"
- Make sure you're running the script from the `src/` directory
- Check that `data/syllabus/` contains the JSON files

### "Chapter not found in syllabus"
- Verify the chapter code exists in the syllabus JSON file
- Chapter codes are case-sensitive

---

## 💰 Cost Considerations

Generating one complete lesson plan costs approximately:
- **GPT-3.5-turbo**: $0.10 - $0.30 USD per lesson plan
- Includes all sections and 4 differentiation levels

To minimize costs during testing:
- Use GPT-3.5-turbo (default)
- Generate fewer sections initially
- Reduce max_tokens in the code if needed

---

## 📚 Next Steps

1. **Review Examples**: Look at `examples/` for sample outputs
2. **Read Documentation**: See `README.md` for full details
3. **Customize**: Modify prompts in `lesson_planner.py` to suit your needs
4. **Extend**: Add new subjects or teaching techniques

---

## 🆘 Need Help?

- **Full Documentation**: See `README.md`
- **Technical Details**: See `docs/PORTFOLIO_NOTES.md`
- **Teaching Methods**: See `docs/TEACHING_TECHNIQUES.md`

---

**Happy Lesson Planning! 🎓**
