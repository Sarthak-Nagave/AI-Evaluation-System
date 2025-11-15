from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def generate_aptitude_questions(department, count=60):
    """Generate aptitude MCQ questions using OpenAI."""
    
    prompt = f"""Generate {count} multiple-choice aptitude questions suitable for {department} department students.
    
    Include a mix of:
    - Logical reasoning (15 questions)
    - Quantitative aptitude (15 questions)
    - Verbal ability (10 questions)
    - Technical aptitude related to {department} (20 questions)
    
    Return ONLY a JSON array with exactly {count} questions in this format:
    [
        {{
            "question": "question text",
            "option_a": "option A text",
            "option_b": "option B text",
            "option_c": "option C text",
            "option_d": "option D text",
            "correct_answer": "A"
        }}
    ]
    
    Make sure:
    - Each question is clear and unambiguous
    - Options are mutually exclusive
    - Correct answer is marked with A, B, C, or D
    - Questions are of moderate difficulty
    - No duplicate questions
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "You are an expert at creating aptitude test questions. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=12000
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        questions = json.loads(content)
        return questions[:count]
    
    except Exception as e:
        print(f"Error generating questions: {e}")
        return []

def evaluate_non_technical_answer(question, answer):
    """Evaluate non-technical subjective answer using AI."""
    
    prompt = f"""Evaluate the following answer to a non-technical question.
    
    Question: {question}
    Answer: {answer}
    
    Evaluate based on:
    1. Relevance to the question
    2. Depth of understanding
    3. Clarity of expression
    4. Completeness
    
    Provide:
    - Score out of 100
    - Detailed feedback
    
    Return ONLY a JSON object in this format:
    {{
        "score": <number 0-100>,
        "feedback": "detailed feedback text"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert evaluator. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        result = json.loads(content)
        return result.get('score', 0), result.get('feedback', '')
    
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return 0, "Error evaluating answer"

def evaluate_mock_interview(transcript):
    """Evaluate mock interview transcript using AI."""
    
    prompt = f"""Evaluate the following HR mock interview transcript.
    
    Transcript: {transcript}
    
    Evaluate the candidate on:
    1. Communication Skills (0-100): Clarity, fluency, and articulation
    2. Confidence (0-100): Self-assurance and composure
    3. Clarity (0-100): Ability to express thoughts clearly
    4. Relevance (0-100): How well answers relate to questions
    
    Provide detailed feedback and individual scores.
    
    Return ONLY a JSON object in this format:
    {{
        "communication_score": <number 0-100>,
        "confidence_score": <number 0-100>,
        "clarity_score": <number 0-100>,
        "relevance_score": <number 0-100>,
        "feedback": "detailed feedback text"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert HR interviewer. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        result = json.loads(content)
        return result
    
    except Exception as e:
        print(f"Error evaluating interview: {e}")
        return {
            "communication_score": 0,
            "confidence_score": 0,
            "clarity_score": 0,
            "relevance_score": 0,
            "feedback": "Error evaluating interview"
        }
