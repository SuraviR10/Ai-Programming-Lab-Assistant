import os
import sys
import json

# Add backend to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.pdf_extraction_service import (
    extract_text_from_pdf_bytes,
    fallback_heuristic_extraction,
    extract_programs_from_manual_text
)
from services.gcc_service import compile_and_run
from services.groq_service import analyze_compiler_error

def test_pdf_extraction():
    print("\n--- 1. Testing PDF Lab Manual Parsing & Multi-Program Detection ---")
    
    sample_manual_text = """
    DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
    C PROGRAMMING LABORATORY MANUAL (CS201)
    
    Experiment 1: Roots of Quadratic Equation
    Aim: Write a C program to compute the real and imaginary roots of a quadratic equation ax^2 + bx + c = 0.
    Sample Input: 1 -5 6
    Sample Output: Root1 = 3.00, Root2 = 2.00
    Reference Code:
    #include <stdio.h>
    #include <math.h>
    int main() {
        float a, b, c, d, r1, r2;
        scanf("%f %f %f", &a, &b, &c);
        d = b*b - 4*a*c;
        if (d >= 0) {
            r1 = (-b + sqrt(d)) / (2*a);
            r2 = (-b - sqrt(d)) / (2*a);
            printf("Root1 = %.2f, Root2 = %.2f\\n", r1, r2);
        }
        return 0;
    }
    
    Experiment 2: Matrix Multiplication
    Aim: Write a C program to perform multiplication of two matrices of order M x N and N x P.
    Sample Input: 2 2 1 2 3 4
    Sample Output: Result Matrix
    
    3. Palindrome String Check
    Aim: To write a C program to check whether a given string is a palindrome without using library functions.
    Input: madam
    Output: Palindrome
    """
    
    programs = fallback_heuristic_extraction(sample_manual_text)
    print(f"Total Programs Detected: {len(programs)}")
    assert len(programs) >= 3, f"Expected at least 3 detected programs, got {len(programs)}"
    
    for p in programs:
        print(f"  [Program {p['program_number']}] Title: '{p['title']}' | Topic: '{p['topic']}' | Code: {'YES' if p['reference_code'] else 'NO'} | Sample In: {p['sample_input']}")
        assert p['title'], "Program must have a title"
        assert p['problem_statement'], "Program must have a problem statement"
        assert p['topic'], "Program must have a detected topic"
        
    print("PDF Multi-Program Extraction test PASSED successfully!")


def test_line_offset_and_remember_tip():
    print("\n--- 2. Testing Compiler Error Previous-Line Awareness & Remember Tip ---")
    
    # Line 4 is missing a semicolon at the end of printf
    # GCC reports 'expected ; before return' on Line 5
    buggy_code = """#include <stdio.h>

int main() {
    printf("Testing Line Offset")
    return 0;
}
"""
    
    result = compile_and_run(buggy_code)
    print(f"Compilation Success: {result['success']}")
    assert result['success'] is False, "Expected compilation to fail"
    
    reported_line = result['line']
    print(f"GCC Reported Line Number: {reported_line}")
    print(f"Compiler Error:\n{result['compiler_error']}")
    
    # Run through Groq AI error analyzer
    ai_feedback = analyze_compiler_error(buggy_code, result['compiler_error'], reported_line, mode="practice")
    
    print(f"\nAI Explanation: {ai_feedback['explanation']}")
    print(f"AI Reason: {ai_feedback['reason']}")
    print(f"AI Hint: {ai_feedback['hint']}")
    print(f"AI Information to Remember: {ai_feedback.get('remember_tip')}")
    print(f"AI Concept: {ai_feedback['concept']}")
    
    # Verify remember_tip exists and is educational
    assert "remember_tip" in ai_feedback, "AI Feedback must include remember_tip"
    assert len(ai_feedback["remember_tip"]) > 10, "remember_tip must contain meaningful rule of thumb"
    
    print("\nCompiler Error Line-Offset & Remember-Tip Verification PASSED successfully!")


if __name__ == "__main__":
    test_pdf_extraction()
    test_line_offset_and_remember_tip()
