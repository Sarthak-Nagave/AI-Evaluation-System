from openai import OpenAI
import os
import json

# This function prevents the app from crashing on startup if the API key is missing.
def get_openai_client():
    """Initializes and returns the OpenAI client, raising an error if the key is missing."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. AI scoring is disabled.")
    return OpenAI(api_key=api_key)

def generate_aptitude_questions(department, count=60):
    """(OBSOLETE - Using hardcoded questions in app.py)"""
    return []

def evaluate_non_technical_answer(question, answer):
    """Evaluate non-technical subjective answer using AI."""
    
    try:
        client = get_openai_client() # Client is initialized here, only when needed.
    except ValueError as e:
        print(f"AI EVALUATION FAILED: {e}")
        return 0, str(e) # Return a score of 0 and the error message
    
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
        return result.get('score', 0), result.get('feedback', 'No feedback provided by AI.')
    
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return 0, f"AI Processing Error: {str(e)}"

def evaluate_mock_interview(transcript):
    """Evaluate mock interview transcript using AI."""
    
    try:
        client = get_openai_client() # Client is initialized here, only when needed.
    except ValueError as e:
        print(f"AI EVALUATION FAILED: {e}")
        return {
            "communication_score": 0,
            "confidence_score": 0,
            "clarity_score": 0,
            "relevance_score": 0,
            "feedback": str(e) # Return the error as feedback
        }
    
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
            "feedback": f"AI Processing Error: {str(e)}"
        }