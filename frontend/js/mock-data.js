/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — Mock Data Engine (mock-data.js)
   Comprehensive missions, 3-tier progressive hints, XP bounties,
   and 3D Learning Journey Constellation Graph
   ═══════════════════════════════════════════════════════════════ */

const MockData = (() => {
  // ── Student Profile (Player State) ──────────────────────────
  const student = {
    id: "STU2024001",
    name: "Suravi",
    fullName: "Suravi R",
    email: "suravi@college.edu",
    section: "A",
    semester: 3,
    avatar: null,
    level: 8,
    rank: "Code Architect",
    xp: 2840,
    problemsCompleted: 18,
    totalProblems: 25,
    averageScore: 8.6,
    successRate: 82,
    streak: 5,
    totalAttempts: 67,
    totalErrors: 34,
    errorsFixed: 31,
    creativeSolutions: 4,
    joinedDate: "2026-07-15",
    lastActive: "2026-08-20",
  };

  // ── Daily Motivational Messages ─────────────────────────────
  const dailyMessages = [
    { quote: "Every compiler error is a learning step towards mastery.", sub: "Keep experimenting. Keep debugging. Build skills." },
    { quote: "The best debugger is a curious mind.", sub: "Question everything your code executes." },
    { quote: "Great programmers write clear code and master debugging.", sub: "Every error solved builds confidence." },
    { quote: "Functions are the building blocks of algorithms.", sub: "Build clean, reusable logic." },
    { quote: "Syntax errors are simply typos in logic.", sub: "Fix them to master programming logic." },
    { quote: "Code does not judge. It only calculates.", sub: "Stay persistent in your practice." },
    { quote: "Alternative approaches show true mastery.", sub: "Experiment with creative solutions." },
    { quote: "Pointers control raw memory. Harness their power.", sub: "Complex programs build strong problem-solving skills." }
  ];


  // ── 3D Learning Journey Map Hierarchy ───────────────────────
  const journeyNodes = [
    { id: "var", name: "Variables & I/O", level: 1, status: "completed", x: -8, y: -4, z: 0, problems: 4, avgScore: 9.6 },
    { id: "cond", name: "Conditionals", level: 2, status: "completed", x: -4, y: -1, z: 2, problems: 4, avgScore: 9.2 },
    { id: "loops", name: "Iteration & Loops", level: 3, status: "completed", x: 0, y: 2, z: -1, problems: 5, avgScore: 8.8 },
    { id: "arrays", name: "Arrays & Strings", level: 4, status: "completed", x: 4, y: 0, z: 1, problems: 5, avgScore: 8.2 },
    { id: "func", name: "Modular Functions", level: 5, status: "completed", x: 8, y: 3, z: -2, problems: 3, avgScore: 8.5 },
    { id: "struct", name: "Data Structures", level: 6, status: "current", x: 12, y: 1, z: 0, problems: 2, avgScore: 7.5 },
    { id: "ptrs", name: "Pointers & Memory", level: 7, status: "unlocked", x: 16, y: -2, z: 2, problems: 2, avgScore: 6.8 },
    { id: "dma", name: "Dynamic Memory", level: 8, status: "locked", x: 20, y: 2, z: -1, problems: 0, avgScore: 0 }
  ];

  // ── Missions / Problems ─────────────────────────────────────
  const problems = [
    {
      id: 1,
      title: "Hello World",
      description: "Write a C program that prints \"Hello, World!\" to the console.",
      difficulty: "easy",
      xpReward: 100,
      concepts: ["printf", "basics"],
      expectedOutput: "Hello, World!",
      sampleInput: null,
      sampleOutput: "Hello, World!",
      starterCode: '#include <stdio.h>\n\nint main() {\n    // Write your code here\n    \n    return 0;\n}\n',
      hints: [
        "Use printf() to print text to the console",
        "Don't forget to include <stdio.h>",
        "Remember the \\n for newline and terminating semicolon"
      ],
      progressiveHints: [
        { tier: 1, title: "Output Function", text: "Look for the standard I/O library function designed to format and print text to standard output." },
        { tier: 2, title: "Exact String Match", text: "Make sure the string inside the double quotes exactly matches 'Hello, World!' including capitalization and comma." },
        { tier: 3, title: "Full Code Solution Hint", text: "Use printf(\"Hello, World!\\n\"); inside your main function and return 0." }
      ],
      status: "completed",
      bestScore: 10,
      attempts: 1,
    },
    {
      id: 2,
      title: "Sum of Two Numbers",
      description: "Write a C program that reads two integers from the user and prints their sum.",
      difficulty: "easy",
      xpReward: 100,
      concepts: ["scanf", "variables", "arithmetic"],
      expectedOutput: "Sum = 15",
      sampleInput: "5 10",
      sampleOutput: "Sum = 15",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int a, b;\n    // Read two numbers and print their sum\n    \n    return 0;\n}\n',
      hints: [
        "Use scanf() to read input from the user",
        "Declare variables to store the numbers",
        "Use %d format specifier for integers"
      ],
      progressiveHints: [
        { tier: 1, title: "Variable Declaration", text: "Ensure you have declared integer variables to store the inputs and the computed sum." },
        { tier: 2, title: "Address Operator in Scanf", text: "Remember to pass the memory address of the variables using & (e.g., &a, &b) in scanf." },
        { tier: 3, title: "Addition Logic", text: "Compute sum = a + b; and display it formatted with printf(\"Sum = %d\\n\", sum);" }
      ],
      status: "completed",
      bestScore: 9.5,
      attempts: 2,
    },
    {
      id: 3,
      title: "Largest of Three",
      description: "Write a C program to find and print the largest of three numbers entered by the user.",
      difficulty: "easy",
      xpReward: 100,
      concepts: ["if", "else", "comparison"],
      expectedOutput: "Largest = 42",
      sampleInput: "15 42 28",
      sampleOutput: "Largest = 42",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int a, b, c;\n    // Read three numbers and find the largest\n    \n    return 0;\n}\n',
      hints: [
        "Compare numbers using if-else statements",
        "Consider using nested if-else or logical operators (&&)",
        "Think about what happens when numbers are equal"
      ],
      progressiveHints: [
        { tier: 1, title: "Branching Logic", text: "A number is the largest if it is greater than or equal to both of the other two numbers simultaneously." },
        { tier: 2, title: "Logical AND Operator", text: "Use (a >= b && a >= c) to test if 'a' is greatest, then an else-if for 'b'." },
        { tier: 3, title: "Ternary or If-Else", text: "You can also use a temporary 'max' variable: max = (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c);" }
      ],
      status: "completed",
      bestScore: 9.0,
      attempts: 3,
    },
    {
      id: 4,
      title: "Even or Odd",
      description: "Write a C program that checks whether a given number is even or odd.",
      difficulty: "easy",
      xpReward: 100,
      concepts: ["if", "modulus", "operators"],
      expectedOutput: "Even",
      sampleInput: "4",
      sampleOutput: "Even",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int num;\n    // Check if the number is even or odd\n    \n    return 0;\n}\n',
      hints: [
        "Use the modulus operator (%) to find the remainder",
        "A number is even if num % 2 == 0",
        "Otherwise, it is odd"
      ],
      progressiveHints: [
        { tier: 1, title: "Remainder Check", text: "Even numbers leave zero remainder when divided by 2." },
        { tier: 2, title: "Modulus Operator", text: "In C, the expression (num % 2 == 0) evaluates to true for even numbers." },
        { tier: 3, title: "Bitwise Alternative", text: "Creative trick: You can also use bitwise AND: if ((num & 1) == 0) for extra performance!" }
      ],
      status: "completed",
      bestScore: 10,
      attempts: 1,
    },
    {
      id: 5,
      title: "Factorial Calculation",
      description: "Write a C program to calculate the factorial of a given positive integer using a loop.",
      difficulty: "easy",
      xpReward: 100,
      concepts: ["loops", "for", "multiplication"],
      expectedOutput: "Factorial of 5 = 120",
      sampleInput: "5",
      sampleOutput: "Factorial of 5 = 120",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int n;\n    long long fact = 1;\n    // Calculate factorial of n\n    \n    return 0;\n}\n',
      hints: [
        "Use a for loop from 1 to n",
        "Multiply the result variable iteratively",
        "Use long long to prevent integer overflow"
      ],
      progressiveHints: [
        { tier: 1, title: "Accumulator Variable", text: "Initialize your factorial accumulator to 1, not 0, because 0 multiplied by anything is 0." },
        { tier: 2, title: "Loop Boundary", text: "Loop from i = 1 up to i <= n with fact *= i in each iteration." },
        { tier: 3, title: "Format Specifier", text: "When printing long long, remember to use the %lld format specifier in printf." }
      ],
      status: "completed",
      bestScore: 9.2,
      attempts: 2,
    },
    {
      id: 6,
      title: "Fibonacci Series",
      description: "Write a C program to generate the first N terms of the Fibonacci series.",
      difficulty: "medium",
      xpReward: 120,
      concepts: ["loops", "while", "series"],
      expectedOutput: "0 1 1 2 3 5 8 13",
      sampleInput: "8",
      sampleOutput: "0 1 1 2 3 5 8 13",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int n;\n    // Generate Fibonacci series\n    \n    return 0;\n}\n',
      hints: [
        "Start with two base values: t1 = 0 and t2 = 1",
        "Each successive term is nextTerm = t1 + t2",
        "Shift variables: t1 = t2, t2 = nextTerm"
      ],
      progressiveHints: [
        { tier: 1, title: "Base Sequence", text: "Fibonacci sequence starts with 0 and 1. Print these initial terms first." },
        { tier: 2, title: "Variable Swapping", text: "In a loop of n terms, compute next = t1 + t2, print next, then assign t1 = t2; t2 = next;" },
        { tier: 3, title: "Edge Cases", text: "Handle small inputs like n = 1 or n = 2 gracefully before entering the loop." }
      ],
      status: "completed",
      bestScore: 8.8,
      attempts: 4,
    },
    {
      id: 7,
      title: "Prime Number Check",
      description: "Write a C program that checks whether a given number is a prime number or not.",
      difficulty: "medium",
      xpReward: 120,
      concepts: ["loops", "if", "modulus", "optimization"],
      expectedOutput: "17 is a prime number",
      sampleInput: "17",
      sampleOutput: "17 is a prime number",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int n;\n    // Check if n is prime\n    \n    return 0;\n}\n',
      hints: [
        "A prime is only divisible by 1 and itself",
        "Optimize by checking divisibility only up to sqrt(n)",
        "Handle edge cases: numbers <= 1 are not prime"
      ],
      progressiveHints: [
        { tier: 1, title: "Divisibility Test", text: "If any number i between 2 and n/2 divides n with zero remainder, n is composite." },
        { tier: 2, title: "Efficiency Optimization", text: "You only need to loop while (i * i <= n). If no divisor is found up to sqrt(n), it is prime." },
        { tier: 3, title: "Flag Variable", text: "Use an integer isPrime = 1; set isPrime = 0 and break if a divisor is found." }
      ],
      status: "completed",
      bestScore: 8.5,
      attempts: 3,
    },
    {
      id: 8,
      title: "Reverse a Number",
      description: "Write a C program to reverse the digits of a given integer.",
      difficulty: "medium",
      xpReward: 120,
      concepts: ["while", "modulus", "arithmetic"],
      expectedOutput: "Reversed: 54321",
      sampleInput: "12345",
      sampleOutput: "Reversed: 54321",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int num;\n    // Reverse the digits\n    \n    return 0;\n}\n',
      hints: [
        "Extract the last digit using modulus (% 10)",
        "Build the reversed number: rev = rev * 10 + digit",
        "Use integer division (num /= 10) to remove the processed digit"
      ],
      progressiveHints: [
        { tier: 1, title: "Extracting Digits", text: "In a while loop (num > 0), remainder = num % 10 isolates the rightmost digit." },
        { tier: 2, title: "Accumulating Reverse", text: "Shift existing reversed digits left by multiplying by 10 and adding the remainder." },
        { tier: 3, title: "Loop Termination", text: "Truncate the original number with num = num / 10 until num reaches 0." }
      ],
      status: "completed",
      bestScore: 9.0,
      attempts: 2,
    },
    {
      id: 18,
      title: "Pointer Arithmetic",
      description: "Write a C program to demonstrate pointer arithmetic by traversing an array using pointers.",
      difficulty: "hard",
      xpReward: 150,
      concepts: ["pointers", "arrays", "memory"],
      expectedOutput: "Elements: 10 20 30 40 50",
      sampleInput: null,
      sampleOutput: "Elements: 10 20 30 40 50",
      starterCode: '#include <stdio.h>\n\nint main() {\n    int arr[] = {10, 20, 30, 40, 50};\n    int *ptr = arr;\n    // Traverse array using pointer arithmetic\n    \n    return 0;\n}\n',
      hints: [
        "An array name decays to a pointer to its first element",
        "ptr++ advances the pointer by sizeof(int) bytes",
        "Dereference *(ptr + i) to access the value"
      ],
      progressiveHints: [
        { tier: 1, title: "Pointer Initialization", text: "Assign ptr = arr; to point to the base memory address of the integer array." },
        { tier: 2, title: "Pointer Offset", text: "*(ptr + i) is mathematically and practically equivalent to arr[i]." },
        { tier: 3, title: "Pointer Traversal", text: "Loop from i = 0 to 4 and print with printf(\"%d \", *ptr++);" }
      ],
      status: "completed",
      bestScore: 7.0,
      attempts: 6,
    },
    {
      id: 19,
      title: "Dynamic Memory Allocation",
      description: "Write a C program that uses malloc() to dynamically allocate memory for an array of n integers, reads values, and calculates their average.",
      difficulty: "hard",
      xpReward: 150,
      concepts: ["pointers", "malloc", "dynamic memory"],
      expectedOutput: "Average = 30.00",
      sampleInput: "5\n10 20 30 40 50",
      sampleOutput: "Average = 30.00",
      starterCode: '#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    int *arr, n;\n    // Dynamically allocate memory and compute average\n    \n    return 0;\n}\n',
      hints: [
        "Include <stdlib.h> for malloc and free",
        "Allocate: arr = (int*)malloc(n * sizeof(int))",
        "Always free allocated heap memory with free(arr)"
      ],
      progressiveHints: [
        { tier: 1, title: "Memory Allocation", text: "Calculate total bytes: n * sizeof(int), and cast the return of malloc to (int*)." },
        { tier: 2, title: "Null Pointer Validation", text: "Check if (arr == NULL) before writing to memory in case heap allocation failed." },
        { tier: 3, title: "Heap Cleanup", text: "After computing and printing the float average, execute free(arr); to prevent memory leaks." }
      ],
      status: "attempted",
      bestScore: 5.5,
      attempts: 4,
    }
  ];

  // ── Recent Submissions ──────────────────────────────────────
  const submissions = [
    { problemId: 18, title: "Pointer Arithmetic", score: 7.0, attempts: 6, date: "2026-08-20", status: "completed", xpEarned: 150 },
    { problemId: 7, title: "Prime Number Check", score: 8.5, attempts: 3, date: "2026-08-19", status: "completed", xpEarned: 120 },
    { problemId: 6, title: "Fibonacci Series", score: 8.8, attempts: 4, date: "2026-08-18", status: "completed", xpEarned: 120 },
    { problemId: 5, title: "Factorial Calculation", score: 9.2, attempts: 2, date: "2026-08-17", status: "completed", xpEarned: 100 },
    { problemId: 19, title: "Dynamic Memory Allocation", score: 5.5, attempts: 4, date: "2026-08-16", status: "attempted", xpEarned: 40 }
  ];

  // ── Skills / Competency Matrix ──────────────────────────────
  const skills = [
    { name: "Loops & Iteration", percentage: 90, level: "master" },
    { name: "Conditionals", percentage: 88, level: "master" },
    { name: "Arrays & Matrices", percentage: 76, level: "advanced" },
    { name: "Functions & Scope", percentage: 72, level: "advanced" },
    { name: "String Manipulation", percentage: 68, level: "competent" },
    { name: "Pointers & Memory", percentage: 48, level: "developing" },
    { name: "Dynamic Memory", percentage: 38, level: "developing" }
  ];

  // ── Weekly Progress Analytics ───────────────────────────────
  const weeklyProgress = [
    { week: "Week 1", problems: 5, avgScore: 9.2, errors: 8, successRate: 90, xp: 620 },
    { week: "Week 2", problems: 5, avgScore: 8.8, errors: 12, successRate: 85, xp: 740 },
    { week: "Week 3", problems: 5, avgScore: 8.2, errors: 15, successRate: 78, xp: 810 },
    { week: "Week 4", problems: 3, avgScore: 7.5, errors: 10, successRate: 75, xp: 670 }
  ];

  // ── Achievements Definition ─────────────────────────────────
  const achievements = [
    { id: "first_run", title: "First Program Executed", description: "Successfully compiled and executed your first C program.", icon: "🚀", xp: 100, earned: true, earnedDate: "2026-07-16", category: "milestone" },
    { id: "debugger", title: "Effective Debugger", description: "Resolved 10 compiler errors through independent debugging.", icon: "🛠", xp: 200, earned: true, earnedDate: "2026-07-25", category: "skill" },
    { id: "week_streak", title: "Study Streak", description: "Maintained a 5-day continuous coding practice streak.", icon: "🔥", xp: 250, earned: true, earnedDate: "2026-08-02", category: "consistency" },
    { id: "explorer", title: "Code Explorer", description: "Solved problems using alternative efficient algorithms.", icon: "✦", xp: 175, earned: true, earnedDate: "2026-08-10", category: "creativity" },
    { id: "perfect_ten", title: "Flawless Execution", description: "Scored a perfect 10/10 on a laboratory program.", icon: "💯", xp: 300, earned: true, earnedDate: "2026-07-16", category: "excellence" },
    { id: "memory_master", title: "Pointer Pioneer", description: "Completed your first Pointer & Memory management program.", icon: "🧠", xp: 250, earned: true, earnedDate: "2026-08-18", category: "milestone" },
    { id: "master_architect", title: "Advanced Programmer", description: "Reach Level 10 in laboratory progress.", icon: "👑", xp: 500, earned: false, earnedDate: null, category: "excellence" }
  ];

  // ── AI Feedback Mock Scenarios ──────────────────────────────
  const aiFeedback = {
    compilationError: {
      explanation: "Your program has a missing semicolon after the printf statement. In C syntax, semicolons delineate executable statements.",
      reason: "The compiler encountered the closing brace '}' while still expecting a statement terminator for the previous line.",
      hint: "Inspect line 4. Verify that the printf() expression terminates with a ';'.",
      concept: "Statement Termination — Semicolons inform the lexical analyzer where one instruction ends and the next begins.",
      line: 4,
      debuggingXP: 40
    },
    evaluation: {
      score: 9.4,
      xpEarned: 100,
      correctness: { value: 6, max: 6 },
      approach: { value: 1.8, max: 2 },
      codeQuality: { value: 0.9, max: 1 },
      creativity: { value: 0.7, max: 1 },
      feedback: "Program solved successfully! Your algorithm executes efficiently and adheres to C standards.",
      isCreative: false,
    },

    evaluationCreative: {
      score: 9.8,
      xpEarned: 175,
      correctness: { value: 6, max: 6 },
      approach: { value: 2.0, max: 2 },
      codeQuality: { value: 0.9, max: 1 },
      creativity: { value: 0.9, max: 1 },
      feedback: "Creative solution detected! You utilized an optimized algorithmic approach differing from the common pattern.",
      isCreative: true,
    }
  };

  // ── Faculty Class Data ──────────────────────────────────────
  const faculty = {
    name: "Dr. Anand Kumar",
    department: "Computer Science",
    totalStudents: 56,
    classAverage: 82,
    completionRate: 76,
    needsAttention: 8,
    activeSessions: 2,
  };

  const studentList = [
    { id: "STU2024001", name: "Suravi R", score: 8.6, successRate: 82, problems: 18, xp: 2840, status: "active", attention: false },
    { id: "STU2024002", name: "Rahul M", score: 7.8, successRate: 75, problems: 15, xp: 2200, status: "active", attention: false },
    { id: "STU2024003", name: "Priya K", score: 9.1, successRate: 91, problems: 22, xp: 3450, status: "active", attention: false },
    { id: "STU2024004", name: "Amit S", score: 5.2, successRate: 48, problems: 8, xp: 950, status: "struggling", attention: true },
    { id: "STU2024005", name: "Neha P", score: 8.0, successRate: 80, problems: 16, xp: 2400, status: "active", attention: false },
    { id: "STU2024006", name: "Vikram T", score: 4.8, successRate: 42, problems: 6, xp: 720, status: "struggling", attention: true },
    { id: "STU2024007", name: "Divya L", score: 7.2, successRate: 70, problems: 14, xp: 1980, status: "active", attention: false }
  ];

  const errorDistribution = [
    { type: "Missing Semicolon", count: 156, percentage: 28 },
    { type: "Undeclared Variable", count: 89, percentage: 16 },
    { type: "Type Mismatch / Format Specifier", count: 78, percentage: 14 },
    { type: "Missing Return Statement", count: 56, percentage: 10 },
    { type: "Array Bounds / Pointer Errors", count: 45, percentage: 8 },
    { type: "Header & Syntax Errors", count: 80, percentage: 24 }
  ];

  function getDailyMessage() {
    const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
    return dailyMessages[dayOfYear % dailyMessages.length];
  }

  function getProblem(id) {
    return problems.find(p => p.id === id) || problems[0];
  }

  function getNextRecommended() {
    return problems.find(p => p.status === "attempted") || problems.find(p => p.status === "pending") || problems[0];
  }

  return {
    student,
    dailyMessages,
    journeyNodes,
    problems,
    submissions,
    skills,
    weeklyProgress,
    achievements,
    aiFeedback,
    faculty,
    studentList,
    errorDistribution,
    getDailyMessage,
    getProblem,
    getNextRecommended
  };
})();
