"""
AI Engine - DeepSeek Integration for Adaptive Learning
"""

import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()  # ← This line MUST exist to read .env files

class AIEngine:
    """AI-powered adaptive learning engine using DeepSeek"""
    
    def __init__(self):
        self.api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        
        # Fallback to mock mode if no API key
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            print("⚠️  DeepSeek API key not found. Running in MOCK MODE.")
            print("   Set DEEPSEEK_API_KEY environment variable for real AI features.")
    
    def _call_api(self, messages, temperature=0.7, max_tokens=500):
        """Call DeepSeek API"""
        if self.mock_mode:
            return self._mock_response(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"❌ DeepSeek API error: {e}")
            return self._mock_response(messages)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return self._mock_response(messages)
    
    def _mock_response(self, messages):
        """Generate mock responses when API is unavailable"""
        user_message = messages[-1]['content'].lower()
        
        # Mock hint generation
        if 'hint' in user_message or 'help' in user_message:
            hints = [
                "Start by examining the input validation - what happens when you provide unexpected input?",
                "Think about how the application processes your data. Can you manipulate it in an unexpected way?",
                "Consider the fundamental vulnerability type for this category. What are common attack vectors?",
                "Try testing edge cases and boundary conditions. What assumptions is the code making?",
                "Look for ways to bypass filters or validation. Sometimes simple techniques work best."
            ]
            import random
            return random.choice(hints)
        
        # Mock learning path
        elif 'learning path' in user_message or 'recommend' in user_message:
            return json.dumps({
                "recommendations": [
                    {"challenge_id": 1, "reason": "Start with fundamentals"},
                    {"challenge_id": 2, "reason": "Build on previous knowledge"},
                    {"challenge_id": 3, "reason": "Increase difficulty gradually"}
                ],
                "focus_areas": ["Web Security", "Input Validation"]
            })
        
        # Default mock response
        return "This is a mock AI response. Set DEEPSEEK_API_KEY environment variable for real AI features."
    
    def generate_hint(self, challenge, attempts, hints_used, context=""):
        """Generate adaptive hint based on challenge and user progress"""
        
        difficulty_levels = {
            1: "beginner-friendly",
            2: "intermediate",
            3: "advanced"
        }
        
        difficulty = difficulty_levels.get(challenge.get('difficulty', 1), "intermediate")
        
        system_prompt = f"""You are an expert cybersecurity instructor helping students learn ethical hacking.
Your role is to provide educational hints that guide thinking without giving away solutions.
Adapt your hints based on the student's progress and maintain an encouraging tone."""

        user_prompt = f"""Challenge: {challenge['name']}
Category: {challenge['category']}
Difficulty: {difficulty}
Description: {challenge['description']}

Student Progress:
- Attempts so far: {attempts}
- Hints already used: {hints_used}
{f"- Student's question: {context}" if context else ""}

Provide a helpful hint that:
1. Guides thinking without revealing the solution
2. Is appropriate for the difficulty level
3. Builds on what they should know from attempts
4. Encourages exploration and learning
5. Is concise (2-3 sentences max)

Hint:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        hint = self._call_api(messages, temperature=0.7, max_tokens=200)
        return hint.strip()
    
    def generate_learning_path(self, completed_challenges, available_challenges):
        """Generate personalized learning path"""
        
        # Build context about user's progress
        completed_categories = list(set([c['category'] for c in completed_challenges]))
        completed_difficulties = [c['difficulty'] for c in completed_challenges]
        avg_difficulty = sum(completed_difficulties) / len(completed_difficulties) if completed_difficulties else 1
        
        system_prompt = """You are an adaptive learning AI that creates personalized cybersecurity learning paths.
Analyze the student's progress and recommend the best next challenges to optimize their learning."""

        user_prompt = f"""Student Progress:
- Completed {len(completed_challenges)} challenges
- Categories mastered: {', '.join(completed_categories) if completed_categories else 'None yet'}
- Average difficulty: {avg_difficulty:.1f}

Available Challenges (showing first 10):
{json.dumps([{'id': c['id'], 'name': c['name'], 'category': c['category'], 'difficulty': c['difficulty']} 
             for c in available_challenges[:10]], indent=2)}

Create a learning path that:
1. Builds on their current knowledge
2. Gradually increases difficulty
3. Covers diverse categories
4. Maintains engagement

Respond with JSON only:
{{
    "recommendations": [
        {{"challenge_id": <id>, "reason": "<why this challenge next>"}},
        ...
    ],
    "focus_areas": ["<area1>", "<area2>"]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_api(messages, temperature=0.7, max_tokens=400)
        
        try:
            # Try to parse JSON response
            path_data = json.loads(response)
            return path_data
        except json.JSONDecodeError:
            # Fallback to simple recommendation
            return {
                "recommendations": [
                    {"challenge_id": c['id'], "reason": "Recommended based on your progress"}
                    for c in available_challenges[:3]
                ],
                "focus_areas": list(set([c['category'] for c in available_challenges[:5]]))
            }
    
    def analyze_performance(self, user_stats, recent_activity):
        """Analyze user performance and provide insights"""
        
        system_prompt = """You are a performance analyst for cybersecurity education.
Provide constructive insights about a student's learning progress."""

        user_prompt = f"""Student Statistics:
- Challenges completed: {user_stats.get('challenges_completed', 0)}
- Hints used: {user_stats.get('hints_used', 0)}
- Total points: {user_stats.get('total_points', 0)}

Recent Activity (last 5 challenges):
{json.dumps(recent_activity, indent=2)}

Provide brief performance insights:
1. Strengths (1-2 sentences)
2. Areas for improvement (1-2 sentences)
3. Motivation/encouragement (1 sentence)

Keep it concise and encouraging."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        analysis = self._call_api(messages, temperature=0.7, max_tokens=300)
        return analysis.strip()
    
    def generate_custom_challenge(self, user_level, category, user_interests=""):
        """Generate a custom challenge based on user preferences"""
        
        system_prompt = """You are an expert cybersecurity challenge creator.
Generate educational, realistic challenges that teach specific skills."""

        user_prompt = f"""Create a {category} challenge for a skill level {user_level} student.
{f"Student interests: {user_interests}" if user_interests else ""}

Generate a challenge with:
1. Creative name
2. Engaging description/scenario
3. Clear learning objectives
4. Appropriate difficulty
5. Realistic flag format

Respond with JSON only:
{{
    "name": "<challenge name>",
    "description": "<detailed scenario>",
    "category": "{category}",
    "difficulty": {user_level},
    "learning_objectives": ["<objective1>", "<objective2>"],
    "hints": ["<hint1>", "<hint2>", "<hint3>"],
    "flag": "CTF{{<flag_content>}}"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self._call_api(messages, temperature=0.8, max_tokens=500)
        
        try:
            challenge_data = json.loads(response)
            return challenge_data
        except json.JSONDecodeError:
            # Return template challenge if parsing fails
            return {
                "name": f"Custom {category} Challenge",
                "description": "A custom-generated challenge tailored to your skill level.",
                "category": category,
                "difficulty": user_level,
                "learning_objectives": [f"Practice {category} skills"],
                "hints": ["Analyze the challenge carefully", "Think about common vulnerabilities"],
                "flag": "CTF{custom_challenge_flag}"
            }
    
    def get_educational_explanation(self, challenge, solution_approach):
        """Get educational explanation after solving a challenge"""
        
        system_prompt = """You are a cybersecurity educator explaining concepts after a challenge is solved.
Provide clear, educational explanations that reinforce learning."""

        user_prompt = f"""Challenge: {challenge['name']}
Category: {challenge['category']}

The student just solved this challenge. Provide:
1. Brief explanation of the vulnerability/concept (2-3 sentences)
2. Why this is important in real-world security (1-2 sentences)
3. How to defend against this (1-2 sentences)

Keep it educational and concise."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        explanation = self._call_api(messages, temperature=0.7, max_tokens=300)
        return explanation.strip()

# Example usage
if __name__ == '__main__':
    ai = AIEngine()
    
    # Test hint generation
    test_challenge = {
        'name': 'SQL Injection Basics',
        'category': 'Web Security',
        'difficulty': 1,
        'description': 'Learn to exploit SQL injection vulnerabilities'
    }
    
    print("Testing AI Engine...")
    print("\n" + "="*60)
    hint = ai.generate_hint(test_challenge, attempts=3, hints_used=0, context="I tried adding quotes but nothing happened")
    print(f"Generated Hint:\n{hint}")
    print("="*60)