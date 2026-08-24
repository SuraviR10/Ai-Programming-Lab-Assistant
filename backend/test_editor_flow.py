import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.gcc_service import compile_and_run

def test_editor_flow():
    print("--- 1. Testing Code Editor Execution Flow ---")
    
    # 1. Type initial code
    initial_code = """#include <stdio.h>

int main() {
    printf("Testing Initial Typing Flow\\n");
    return 0;
}
"""
    res1 = compile_and_run(initial_code)
    print("Initial Code Execution:", res1)
    assert res1["success"] is True
    assert "Testing Initial Typing Flow" in res1["output"]
    
    # 2. Modify code (Simulating student typing/modifying)
    modified_code = """#include <stdio.h>

int main() {
    int a = 15, b = 25;
    printf("Sum is: %d\\n", a + b);
    return 0;
}
"""
    res2 = compile_and_run(modified_code)
    print("Modified Code Execution:", res2)
    assert res2["success"] is True
    assert "Sum is: 40" in res2["output"]
    
    # 3. Paste external code (Simulating student pasting code)
    pasted_code = """#include <stdio.h>

int main() {
    char greeting[] = "Hello from Pasted Text!";
    printf("%s\\n", greeting);
    return 0;
}
"""
    res3 = compile_and_run(pasted_code)
    print("Pasted Code Execution:", res3)
    assert res3["success"] is True
    assert "Hello from Pasted Text!" in res3["output"]
    
    print("\nALL EDITOR COMPILATION FLOW TESTS PASSED SUCCESSFULLY WITH 100% ACCURACY!")

if __name__ == "__main__":
    test_editor_flow()
