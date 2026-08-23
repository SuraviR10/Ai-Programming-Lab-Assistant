"""
AI Practice Mode Service — AI Challenge Generator
Dynamically creates C programming practice challenges based on student performance,
assigned concepts, and difficulty progression.
"""

import os
import json
import re
import random
from groq import Groq
from dotenv import load_dotenv
from database import SessionLocal, Problem, TestCase, User
from services.groq_service import _client, GROQ_MODELS

load_dotenv()

_CHALLENGE_PROMPT = """You are an AI Computer Science Professor designing an adaptive C Programming Practice Challenge for a student.

Target Concept: {concept}
Target Difficulty: {difficulty}
Student Level: {student_level}

Create a brand new C programming problem related to "{concept}".

Return ONLY valid JSON in this exact structure:
{{
  "title": "Short descriptive title",
  "description": "Clear problem statement requiring standard C input/output.",
  "difficulty": "{difficulty}",
  "concepts": ["{concept}", "logic"],
  "starter_code": "#include <stdio.h>\\n\\nint main() {{\\n    // Write your code here\\n    return 0;\\n}}\\n",
  "sample_input": "sample input string",
  "sample_output": "Expected Output",
  "expected_output": "Expected Output",
  "xp_reward": 150,
  "hints": ["Hint 1", "Hint 2"],
  "progressive_hints": [
    {{"tier": 1, "title": "Concept Overview", "text": "Focus on array traversal."}},
    {{"tier": 2, "title": "Algorithmic Step", "text": "Compare adjacent elements."}},
    {{"tier": 3, "title": "Implementation Detail", "text": "Use a loop with boundary checks."}}
  ],
  "test_cases": [
    {{"input": "sample input string", "expected": "Expected Output", "is_hidden": false}},
    {{"input": "hidden input string", "expected": "Hidden Expected Output", "is_hidden": true}}
  ]
}}"""


PRACTICE_TEMPLATES = {
    "Arrays": [
        {
            "title": "Array Sum & Average",
            "description": "Write a C program that reads N numbers into an array and prints their sum and integer average in the format: Sum = X, Avg = Y",
            "difficulty": "medium",
            "concepts": ["Arrays", "Loops", "Arithmetic"],
            "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        int arr[100], sum = 0;\n        for (int i = 0; i < n; i++) {\n            scanf("%d", &arr[i]);\n            sum += arr[i];\n        }\n        printf("Sum = %d, Avg = %d\\n", sum, sum / n);\n    }\n    return 0;\n}\n',
            "sample_input": "4\n10 20 30 40",
            "sample_output": "Sum = 100, Avg = 25",
            "expected_output": "Sum = 100, Avg = 25",
            "xp_reward": 150,
            "hints": ["Store numbers in array", "Accumulate total sum inside loop"],
            "progressive_hints": [
                {"tier": 1, "title": "Array Declaration", "text": "Declare int arr[100]; and loop N times."},
                {"tier": 2, "title": "Sum Accumulation", "text": "Add each scanned number to a sum variable."},
                {"tier": 3, "title": "Average Computation", "text": "Integer average is sum / N."}
            ],
            "test_cases": [
                {"input": "4\n10 20 30 40", "expected": "Sum = 100, Avg = 25", "is_hidden": False},
                {"input": "3\n5 15 25", "expected": "Sum = 45, Avg = 15", "is_hidden": True}
            ]
        },
        {
            "title": "Find Maximum in Array",
            "description": "Write a C program that reads N elements of an array and finds the maximum element in the format: Max = X",
            "difficulty": "medium",
            "concepts": ["Arrays", "Loops", "Comparison"],
            "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1 && n > 0) {\n        int arr[100];\n        for (int i = 0; i < n; i++) scanf("%d", &arr[i]);\n        int max = arr[0];\n        for (int i = 1; i < n; i++) {\n            if (arr[i] > max) max = arr[i];\n        }\n        printf("Max = %d\\n", max);\n    }\n    return 0;\n}\n',
            "sample_input": "5\n12 45 7 89 23",
            "sample_output": "Max = 89",
            "expected_output": "Max = 89",
            "xp_reward": 150,
            "hints": ["Initialize max with arr[0]", "Update max whenever arr[i] > max"],
            "progressive_hints": [
                {"tier": 1, "title": "Base Initialization", "text": "Assume first element is maximum."},
                {"tier": 2, "title": "Loop Comparison", "text": "Iterate from index 1 to N-1."},
                {"tier": 3, "title": "Update Condition", "text": "If current element > max, set max = current element."}
            ],
            "test_cases": [
                {"input": "5\n12 45 7 89 23", "expected": "Max = 89", "is_hidden": False},
                {"input": "4\n-5 -2 -10 -1", "expected": "Max = -1", "is_hidden": True}
            ]
        }
    ],
    "Loops": [
        {
            "title": "Count Digits in Integer",
            "description": "Write a C program that reads an integer N and counts its total digits in the format: Count = X",
            "difficulty": "easy",
            "concepts": ["Loops", "while loop", "Arithmetic"],
            "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    if (scanf("%d", &n) == 1) {\n        int count = 0, temp = n;\n        if (temp == 0) count = 1;\n        while (temp != 0) {\n            count++;\n            temp /= 10;\n        }\n        printf("Count = %d\\n", count);\n    }\n    return 0;\n}\n',
            "sample_input": "98765",
            "sample_output": "Count = 5",
            "expected_output": "Count = 5",
            "xp_reward": 120,
            "hints": ["Divide by 10 in a loop", "Increment counter in each step"],
            "progressive_hints": [
                {"tier": 1, "title": "Division Step", "text": "Dividing an integer by 10 removes its last digit."},
                {"tier": 2, "title": "Loop Condition", "text": "Continue while n != 0."},
                {"tier": 3, "title": "Zero Case", "text": "If N is 0, total digits is 1."}
            ],
            "test_cases": [
                {"input": "98765", "expected": "Count = 5", "is_hidden": False},
                {"input": "0", "expected": "Count = 1", "is_hidden": True},
                {"input": "123", "expected": "Count = 3", "is_hidden": True}
            ]
        }
    ]
}


def generate_challenge_problem(concept: str = "Arrays", student_id: str = "STU2024001", difficulty: str = "medium") -> dict:
    """
    Generates an adaptive C practice challenge problem using Groq AI LLM.
    If Groq is offline or fails, uses template-backed fallback.
    Saves problem & test cases to database and returns structured problem dict.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == student_id).first()
        student_level = user.level if user else 5

        problem_data = None

        # 1. Attempt Groq Generation if available
        if _client:
            prompt = _CHALLENGE_PROMPT.format(
                concept=concept,
                difficulty=difficulty,
                student_level=student_level
            )
            for model_name in GROQ_MODELS:
                try:
                    response = _client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=800,
                    )
                    raw_text = response.choices[0].message.content.strip()
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                    parsed = json.loads(raw_text)

                    if parsed.get("title") and parsed.get("starter_code"):
                        problem_data = parsed
                        break
                except Exception:
                    continue

        # 2. Fallback Template if Groq unavailable or parsing failed
        if not problem_data:
            templates = PRACTICE_TEMPLATES.get(concept, PRACTICE_TEMPLATES["Arrays"])
            problem_data = random.choice(templates)

        # 3. Save Challenge Problem to DB
        p = Problem(
            title=f"⚡ Practice: {problem_data['title']}",
            description=problem_data['description'],
            difficulty=problem_data.get('difficulty', difficulty),
            concepts=json.dumps(problem_data.get('concepts', [concept])),
            starter_code=problem_data['starter_code'],
            expected_output=problem_data['expected_output'],
            sample_input=problem_data.get('sample_input'),
            sample_output=problem_data.get('sample_output'),
            xp_reward=problem_data.get('xp_reward', 150),
            hints=json.dumps(problem_data.get('hints', [])),
            progressive_hints=json.dumps(problem_data.get('progressive_hints', [])),
            requires_input=True,
            allows_fixed_output=False,
            is_active=True
        )
        db.add(p)
        db.flush()

        test_cases = problem_data.get('test_cases', [])
        if not test_cases:
            test_cases = [{"input": problem_data.get('sample_input', ''), "expected": problem_data['expected_output'], "is_hidden": False}]

        for tc in test_cases:
            db.add(TestCase(
                problem_id=p.id,
                input_data=tc.get('input', ''),
                expected_output=tc.get('expected', ''),
                is_hidden=tc.get('is_hidden', False)
            ))

        db.commit()

        return {
            "success": True,
            "problem_id": p.id,
            "problem": {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "difficulty": p.difficulty,
                "concepts": json.loads(p.concepts),
                "starter_code": p.starter_code,
                "expected_output": p.expected_output,
                "sample_input": p.sample_input,
                "sample_output": p.sample_output,
                "xp_reward": p.xp_reward,
                "hints": json.loads(p.hints),
                "progressive_hints": json.loads(p.progressive_hints)
            }
        }
    finally:
        db.close()
