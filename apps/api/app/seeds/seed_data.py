import asyncio
import random
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import select

from app.database import AsyncSessionLocal, Base, engine
from app.models.analytics import Badge, DailyStats, Mastery
from app.models.concept import Concept
from app.models.problem import Problem
from app.models.user import Course, Enrollment, Institution, User
from app.services.auth_service import AuthService

SUBJECTS = [
    "Programming Basics",
    "Data Structures & Algorithms",
    "Calculus & Linear Algebra",
    "Physics Mechanics",
    "Digital Logic",
    "Probability & Statistics",
]


CONCEPTS_DATA = [
    # Programming
    {
        "id": "cs-var-loops",
        "name": "Variables & Control Flow",
        "subject": "Programming Basics",
        "parent_id": None,
    },
    {
        "id": "cs-functions",
        "name": "Functions & Scope",
        "subject": "Programming Basics",
        "parent_id": "cs-var-loops",
    },
    {
        "id": "cs-recursion",
        "name": "Recursion",
        "subject": "Programming Basics",
        "parent_id": "cs-functions",
    },
    # DSA
    {
        "id": "dsa-arrays",
        "name": "Arrays & Strings",
        "subject": "Data Structures & Algorithms",
        "parent_id": None,
    },
    {
        "id": "dsa-linked-list",
        "name": "Linked Lists",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-arrays",
    },
    {
        "id": "dsa-stacks-queues",
        "name": "Stacks & Queues",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-linked-list",
    },
    {
        "id": "dsa-binary-search",
        "name": "Binary Search",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-arrays",
    },
    {
        "id": "dsa-trees",
        "name": "Trees & Traversals",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-recursion",
    },
    {
        "id": "dsa-graphs",
        "name": "Graphs & BFS/DFS",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-trees",
    },
    {
        "id": "dsa-dp",
        "name": "Dynamic Programming",
        "subject": "Data Structures & Algorithms",
        "parent_id": "dsa-recursion",
    },
    # Math
    {
        "id": "math-limits",
        "name": "Limits & Continuity",
        "subject": "Calculus & Linear Algebra",
        "parent_id": None,
    },
    {
        "id": "math-derivatives",
        "name": "Derivatives & Chain Rule",
        "subject": "Calculus & Linear Algebra",
        "parent_id": "math-limits",
    },
    {
        "id": "math-integration",
        "name": "Definite & Indefinite Integrals",
        "subject": "Calculus & Linear Algebra",
        "parent_id": "math-derivatives",
    },
    {
        "id": "math-vectors",
        "name": "Vectors & Dot/Cross Products",
        "subject": "Calculus & Linear Algebra",
        "parent_id": None,
    },
    {
        "id": "math-matrices",
        "name": "Matrix Algebra & Determinants",
        "subject": "Calculus & Linear Algebra",
        "parent_id": "math-vectors",
    },
    {
        "id": "math-eigen",
        "name": "Eigenvalues & Eigenvectors",
        "subject": "Calculus & Linear Algebra",
        "parent_id": "math-matrices",
    },
    # Physics
    {
        "id": "phy-kinematics",
        "name": "1D & 2D Kinematics",
        "subject": "Physics Mechanics",
        "parent_id": None,
    },
    {
        "id": "phy-newton",
        "name": "Newton's Laws of Motion",
        "subject": "Physics Mechanics",
        "parent_id": "phy-kinematics",
    },
    {
        "id": "phy-energy",
        "name": "Work, Energy & Conservation",
        "subject": "Physics Mechanics",
        "parent_id": "phy-newton",
    },
    {
        "id": "phy-momentum",
        "name": "Linear Momentum & Collisions",
        "subject": "Physics Mechanics",
        "parent_id": "phy-newton",
    },
    # Digital Logic
    {
        "id": "dl-boolean",
        "name": "Boolean Algebra & Gates",
        "subject": "Digital Logic",
        "parent_id": None,
    },
    {
        "id": "dl-kmap",
        "name": "Karnaugh Maps",
        "subject": "Digital Logic",
        "parent_id": "dl-boolean",
    },
    {
        "id": "dl-combinational",
        "name": "Combinational Circuits (Adders/Mux)",
        "subject": "Digital Logic",
        "parent_id": "dl-kmap",
    },
    # Probability
    {
        "id": "prob-bayes",
        "name": "Conditional Probability & Bayes Rule",
        "subject": "Probability & Statistics",
        "parent_id": None,
    },
    {
        "id": "prob-random-var",
        "name": "Random Variables & Distributions",
        "subject": "Probability & Statistics",
        "parent_id": "prob-bayes",
    },
]


def generate_seed_problems() -> List[Dict[str, Any]]:
    problems = []

    # 15 Coding Problems
    coding_defs = [
        (
            "Two Sum Problem",
            "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to target.",
            "dsa-arrays",
            1.0,
            "def two_sum(nums, target):\n    lookup = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in lookup:\n            return [lookup[diff], i]\n        lookup[num] = i\n    return []",
            [
                {"input": "[2,7,11,15]\n9", "expected_output": "[0, 1]"},
                {"input": "[3,2,4]\n6", "expected_output": "[1, 2]"},
                {"input": "[3,3]\n6", "expected_output": "[0, 1]"},
            ],
        ),
        (
            "Reverse a Singly Linked List",
            "Given the head of a singly linked list, reverse the list, and return the reversed list.",
            "dsa-linked-list",
            1.2,
            "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\ndef reverse_list(head):\n    prev = None\n    curr = head\n    while curr:\n        next_temp = curr.next\n        curr.next = prev\n        prev = curr\n        curr = next_temp\n    return prev",
            [{"input": "[1,2,3,4,5]", "expected_output": "[5,4,3,2,1]"}],
        ),
        (
            "Valid Parentheses",
            "Given a string `s` containing just `'(', ')', '{', '}', '[' and ']'`, determine if the input string is valid.",
            "dsa-stacks-queues",
            1.1,
            "def is_valid(s: str) -> bool:\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack",
            [
                {"input": "()[]{}", "expected_output": "true"},
                {"input": "(]", "expected_output": "false"},
            ],
        ),
        (
            "Binary Search Implementation",
            "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, search target in `nums`. If target exists, return its index. Otherwise, return -1 in O(log n) time.",
            "dsa-binary-search",
            1.0,
            "def search(nums, target):\n    l, r = 0, len(nums) - 1\n    while l <= r:\n        mid = (l + r) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            l = mid + 1\n        else:\n            r = mid - 1\n    return -1",
            [
                {"input": "[-1,0,3,5,9,12]\n9", "expected_output": "4"},
                {"input": "[-1,0,3,5,9,12]\n2", "expected_output": "-1"},
            ],
        ),
        (
            "Invert Binary Tree",
            "Given the root of a binary tree, invert the tree, and return its root.",
            "dsa-trees",
            1.2,
            "def invert_tree(root):\n    if not root:\n        return None\n    root.left, root.right = invert_tree(root.right), invert_tree(root.left)\n    return root",
            [{"input": "[4,2,7,1,3,6,9]", "expected_output": "[4,7,2,9,6,3,1]"}],
        ),
        (
            "Climbing Stairs (DP)",
            "You are climbing a staircase. It takes `n` steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
            "dsa-dp",
            1.1,
            "def climb_stairs(n: int) -> int:\n    if n <= 2:\n        return n\n    a, b = 1, 2\n    for _ in range(3, n + 1):\n        a, b = b, a + b\n    return b",
            [
                {"input": "2", "expected_output": "2"},
                {"input": "3", "expected_output": "3"},
                {"input": "5", "expected_output": "8"},
            ],
        ),
        (
            "Coin Change",
            "Given an integer array `coins` representing coins of different denominations and an integer `amount`, return the fewest number of coins that you need to make up that amount.",
            "dsa-dp",
            1.6,
            "def coin_change(coins, amount):\n    dp = [float('inf')] * (amount + 1)\n    dp[0] = 0\n    for coin in coins:\n        for x in range(coin, amount + 1):\n            dp[x] = min(dp[x], dp[x - coin] + 1)\n    return dp[amount] if dp[amount] != float('inf') else -1",
            [
                {"input": "[1,2,5]\n11", "expected_output": "3"},
                {"input": "[2]\n3", "expected_output": "-1"},
            ],
        ),
        (
            "Detect Cycle in Directed Graph",
            "Given a directed graph with `V` vertices and `adj` list, determine if there is a cycle using DFS coloring.",
            "dsa-graphs",
            1.5,
            "def is_cyclic(V, adj):\n    visited = [0] * V\n    def dfs(u):\n        visited[u] = 1\n        for v in adj[u]:\n            if visited[v] == 1:\n                return True\n            if visited[v] == 0 and dfs(v):\n                return True\n        visited[u] = 2\n        return False\n    return any(dfs(i) for i in range(V) if visited[i] == 0)",
            [{"input": "4\n[[1],[2],[0],[0]]", "expected_output": "true"}],
        ),
        (
            "Merge Two Sorted Lists",
            "Merge two sorted linked lists and return it as a sorted list.",
            "dsa-linked-list",
            1.1,
            "def merge_two_lists(l1, l2):\n    dummy = ListNode()\n    curr = dummy\n    while l1 and l2:\n        if l1.val < l2.val:\n            curr.next = l1\n            l1 = l1.next\n        else:\n            curr.next = l2\n            l2 = l2.next\n        curr = curr.next\n    curr.next = l1 or l2\n    return dummy.next",
            [{"input": "[1,2,4]\n[1,3,4]", "expected_output": "[1,1,2,3,4,4]"}],
        ),
        (
            "Maximum Subarray (Kadane's Algorithm)",
            "Find the contiguous subarray with the largest sum and return its sum.",
            "dsa-arrays",
            1.2,
            "def max_sub_array(nums):\n    max_so_far = max_ending_here = nums[0]\n    for x in nums[1:]:\n        max_ending_here = max(x, max_ending_here + x)\n        max_so_far = max(max_so_far, max_ending_here)\n    return max_so_far",
            [{"input": "[-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6"}],
        ),
        (
            "Longest Common Subsequence",
            "Given two strings `text1` and `text2`, return the length of their longest common subsequence.",
            "dsa-dp",
            1.4,
            "def longest_common_subsequence(text1, text2):\n    m, n = len(text1), len(text2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(m):\n        for j in range(n):\n            if text1[i] == text2[j]:\n                dp[i+1][j+1] = dp[i][j] + 1\n            else:\n                dp[i+1][j+1] = max(dp[i+1][j], dp[i][j+1])\n    return dp[m][n]",
            [{"input": '"abcde"\n"ace"', "expected_output": "3"}],
        ),
        (
            "Implement Queue using Stacks",
            "Implement a FIFO queue using only two standard LIFO stacks.",
            "dsa-stacks-queues",
            1.1,
            "class MyQueue:\n    def __init__(self):\n        self.s1 = []\n        self.s2 = []\n    def push(self, x: int) -> None:\n        self.s1.append(x)\n    def pop(self) -> int:\n        self.peek()\n        return self.s2.pop()\n    def peek(self) -> int:\n        if not self.s2:\n            while self.s1:\n                self.s2.append(self.s1.pop())\n        return self.s2[-1]\n    def empty(self) -> bool:\n        return not self.s1 and not self.s2",
            [
                {
                    "input": "push(1), push(2), peek(), pop(), empty()",
                    "expected_output": "[1, 1, false]",
                }
            ],
        ),
        (
            "Fibonacci Number via Memoization",
            "Compute F(n) in O(n) time and O(n) space.",
            "cs-recursion",
            0.9,
            "def fib(n, memo={}):\n    if n <= 1:\n        return n\n    if n not in memo:\n        memo[n] = fib(n-1, memo) + fib(n-2, memo)\n    return memo[n]",
            [{"input": "10", "expected_output": "55"}],
        ),
        (
            "Breadth-First Search on Grid",
            "Given an `m x n` grid where 0 is empty and 1 is obstacle, find the shortest path from top-left to bottom-right.",
            "dsa-graphs",
            1.4,
            "from collections import deque\ndef shortest_path(grid):\n    if grid[0][0] == 1:\n        return -1\n    m, n = len(grid), len(grid[0])\n    q = deque([(0, 0, 1)])\n    visited = {(0, 0)}\n    while q:\n        r, c, dist = q.popleft()\n        if r == m - 1 and c == n - 1:\n            return dist\n        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:\n            nr, nc = r + dr, c + dc\n            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 0 and (nr, nc) not in visited:\n                visited.add((nr, nc))\n                q.append((nr, nc, dist + 1))\n    return -1",
            [{"input": "[[0,0,0],[1,1,0],[0,0,0]]", "expected_output": "5"}],
        ),
        (
            "Matrix Transposition",
            "Given a 2D matrix, return its transpose without modifying original dimensions.",
            "cs-var-loops",
            0.8,
            "def transpose(matrix):\n    return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]",
            [{"input": "[[1,2,3],[4,5,6]]", "expected_output": "[[1,4],[2,5],[3,6]]"}],
        ),
    ]

    for title, stmt, concept, diff, sol, tc in coding_defs:
        problems.append(
            {
                "title": title,
                "statement_md": stmt,
                "subject": "Data Structures & Algorithms"
                if "dsa" in concept
                else "Programming Basics",
                "difficulty_b": diff,
                "type": "coding",
                "reference_solution_md": sol,
                "concept_ids": [concept],
                "rubric": {
                    "correctness": "Passes all base and edge test cases",
                    "time_complexity": "Optimal time complexity achieved",
                    "space_complexity": "No unnecessary memory allocations",
                },
                "test_cases": tc,
                "visibility": "public",
            }
        )

    # 10 Numeric Problems
    numeric_defs = [
        (
            "Definite Integral of Polynomial",
            "Calculate the value of $\\int_{0}^{3} (2x^2 - 4x + 5) dx$. Provide the exact fractional or decimal answer.",
            "math-integration",
            1.1,
            "Let $f(x) = 2x^2 - 4x + 5$.\nAntiderivative $F(x) = \\frac{2}{3}x^3 - 2x^2 + 5x$.\n$F(3) = \\frac{2}{3}(27) - 2(9) + 5(3) = 18 - 18 + 15 = 15$.\n$F(0) = 0$.\nResult = 15.",
            "15",
        ),
        (
            "Matrix Determinant 3x3",
            "Find the determinant of matrix $A = \\begin{pmatrix} 1 & 2 & 3 \\\\ 0 & 1 & 4 \\\\ 5 & 6 & 0 \\end{pmatrix}$.",
            "math-matrices",
            1.2,
            "Expanding along row 1:\n$1(0 - 24) - 2(0 - 20) + 3(0 - 5) = -24 + 40 - 15 = 1$.\nDeterminant is 1.",
            "1",
        ),
        (
            "Kinematics Stopping Distance",
            "A car travels at $25\\text{ m/s}$ and decelerates uniformly at $5\\text{ m/s}^2$. Calculate the stopping distance in meters.",
            "phy-kinematics",
            0.9,
            "Using $v^2 = u^2 + 2as$ with $v=0, u=25, a=-5$:\n$0 = 625 - 10s \\implies s = 62.5\\text{ m}$.",
            "62.5",
        ),
        (
            "Work Done by Variable Force",
            "A force $F(x) = 3x^2 + 2x$ Newtons acts on an object from $x = 1\\text{ m}$ to $x = 3\\text{ m}$. Compute the total work done in Joules.",
            "phy-energy",
            1.0,
            "$W = \\int_{1}^{3} (3x^2 + 2x) dx = [x^3 + x^2]_{1}^{3} = (27 + 9) - (1 + 1) = 36 - 2 = 34\\text{ J}$.",
            "34",
        ),
        (
            "Bayes Rule Posterior Probability",
            "Disease prevalence is $1\\%$. Test has $95\\%$ sensitivity and $90\\%$ specificity. What is $P(\\text{Disease}|\\text{Positive})$ to 3 decimal places?",
            "prob-bayes",
            1.3,
            "$P(D) = 0.01, P(+|D) = 0.95, P(+|\\neg D) = 0.10$.\n$P(+) = 0.01(0.95) + 0.99(0.10) = 0.0095 + 0.0990 = 0.1085$.\n$P(D|+) = 0.0095 / 0.1085 \\approx 0.0875$.",
            "0.088",
        ),
        (
            "Eigenvalues of 2x2 Matrix",
            "Find the sum of eigenvalues for matrix $M = \\begin{pmatrix} 7 & 3 \\\\ 2 & 4 \\end{pmatrix}$.",
            "math-eigen",
            1.0,
            "The sum of eigenvalues equals the trace of the matrix:\n$\\text{Tr}(M) = 7 + 4 = 11$.",
            "11",
        ),
        (
            "Inelastic Collision Velocity",
            "A $2\\text{ kg}$ block moving at $6\\text{ m/s}$ collides and sticks with a stationary $4\\text{ kg}$ block. Find the final combined velocity in m/s.",
            "phy-momentum",
            1.0,
            "Conservation of momentum:\n$m_1 v_1 + m_2 v_2 = (m_1 + m_2) v_f$\n$2(6) + 0 = 6 v_f \\implies v_f = 2\\text{ m/s}$.",
            "2",
        ),
        (
            "Derivative at a Point",
            "Find $f'(2)$ where $f(x) = \\frac{x^3}{x + 1}$. Round to 2 decimal places.",
            "math-derivatives",
            1.1,
            "Using quotient rule: $f'(x) = \\frac{3x^2(x+1) - x^3(1)}{(x+1)^2}$.\nAt $x=2$: $\\frac{3(4)(3) - 8}{9} = \\frac{36 - 8}{9} = \\frac{28}{9} \\approx 3.11$.",
            "3.11",
        ),
        (
            "Combinations Count",
            "Calculate the number of ways to choose a committee of 4 members from a group of 9 people.",
            "prob-random-var",
            0.9,
            "$\\binom{9}{4} = \\frac{9 \\times 8 \\times 7 \\times 6}{4 \\times 3 \\times 2 \\times 1} = 126$.",
            "126",
        ),
        (
            "Karnaugh Map Minimized Term Count",
            "Given minterms $\\Sigma m(0, 1, 2, 3, 8, 9, 10, 11)$ in a 4-variable map, how many literals are in the single essential prime implicant?",
            "dl-kmap",
            1.2,
            "The group covers 8 minterms: $B=0$. Thus the minimized expression is $B'$, which has 1 literal.",
            "1",
        ),
    ]

    for title, stmt, concept, diff, sol, num_ans in numeric_defs:
        subject = (
            "Calculus & Linear Algebra"
            if "math" in concept
            else (
                "Physics Mechanics"
                if "phy" in concept
                else ("Probability & Statistics" if "prob" in concept else "Digital Logic")
            )
        )
        problems.append(
            {
                "title": title,
                "statement_md": stmt,
                "subject": subject,
                "difficulty_b": diff,
                "type": "numeric",
                "reference_solution_md": sol,
                "concept_ids": [concept],
                "rubric": {
                    "setup": "States correct formula or physical conservation law",
                    "execution": "Shows step-by-step substitution without arithmetic errors",
                    "final_answer": f"Final numerical answer matches reference ({num_ans})",
                },
                "test_cases": None,
                "visibility": "public",
            }
        )

    # 15 Theory Problems
    theory_defs = [
        (
            "Explain Principle of Conservation of Energy",
            "Explain the Law of Conservation of Energy and describe how mechanical energy transforms between potential and kinetic in an oscillating simple pendulum.",
            "phy-energy",
            1.0,
            "Energy can neither be created nor destroyed, only transformed from one form to another. In a simple pendulum:\n1. At maximum displacement (amplitude), velocity is zero so Kinetic Energy $KE = 0$, while Gravitational Potential Energy $PE = mgh$ is at maximum.\n2. As the bob swings downward, PE is converted into KE.\n3. At the lowest equilibrium point, PE is minimum (or zero relative to datum) and KE is at its peak (maximum velocity).\n4. Total mechanical energy $E = KE + PE$ remains constant in the absence of air resistance and friction.",
        ),
        (
            "Explain Amortized Analysis in Dynamic Arrays",
            "Explain what amortized time complexity is and demonstrate why appending to a dynamic array has $O(1)$ amortized time despite the occasional $O(n)$ reallocation.",
            "dsa-arrays",
            1.2,
            "Amortized analysis averages the running time of all operations in a sequence over the entire sequence. In a dynamic array that doubles its capacity when full:\n- An array doubling at size $N$ takes $O(N)$ operations to copy elements.\n- However, this expensive operation only occurs after $N/2$ cheap $O(1)$ insertions.\n- Using the aggregate method or accounting method, assigning 3 tokens to each insertion (1 for inserting, 2 saved to copy the item later) covers all future reallocation costs.\n- Therefore, the amortized cost per append is strictly $O(1)$.",
        ),
        (
            "Differentiate BFS vs DFS",
            "Compare Breadth-First Search (BFS) and Depth-First Search (DFS) in terms of data structures used, space complexity on balanced trees, and optimal use cases.",
            "dsa-graphs",
            1.1,
            "1. Data Structure: BFS uses a Queue (FIFO); DFS uses a Stack (LIFO or recursion call stack).\n2. Space Complexity: On a tree of branching factor $b$ and depth $d$, BFS requires $O(b^d)$ memory for the frontier, whereas DFS requires $O(d)$ memory proportional to height.\n3. Use Cases: BFS finds the shortest path in unweighted graphs. DFS is ideal for topological sorting, cycle detection, and maze solving/exhaustive branch exploration.",
        ),
        (
            "Explain Bayes Theorem Conceptually",
            "Explain the intuitive meaning of Prior, Likelihood, and Posterior in Bayes' Theorem. Why is understanding the base rate fallacy critical in medical testing?",
            "prob-bayes",
            1.1,
            "Bayes Theorem calculates $P(A|B) = \\frac{P(B|A)P(A)}{P(B)}$.\n- Prior $P(A)$: Our initial degree of belief before observing evidence.\n- Likelihood $P(B|A)$: How probable the evidence is under hypothesis A.\n- Posterior $P(A|B)$: The updated belief given evidence B.\nThe Base Rate Fallacy occurs when people ignore the low prior $P(A)$ (e.g. rare disease of 0.1%). Even with high test accuracy, false positives in a huge healthy population can easily outnumber true positives.",
        ),
        (
            "Eigenvectors and Linear Transformations",
            "Geometrically describe what an eigenvector and eigenvalue represent for a 2x2 matrix transformation in $\\mathbb{R}^2$.",
            "math-eigen",
            1.2,
            "An eigenvector of a linear transformation $A$ is a non-zero vector whose direction does not change when the transformation is applied. It is only scaled by a scalar factor $\\lambda$, called the eigenvalue: $A\\vec{v} = \\lambda \\vec{v}$. For example, if $\\lambda = 2$, vectors along that span stretch by 2; if $\\lambda = -1$, they reflect across the origin without rotating off their line.",
        ),
        (
            "Newton's Third Law Misconceptions",
            "State Newton's Third Law and explain why action-reaction force pairs never cancel each other out.",
            "phy-newton",
            1.0,
            "Newton's Third Law states: When body A exerts a force on body B, body B exerts an equal in magnitude and opposite in direction force on body A. The crucial reason action and reaction pairs never cancel each other out is that they act on two different bodies. Forces can only cancel if they act on the same free-body diagram.",
        ),
        (
            "Explain the Halting Problem",
            "Summarize Turing's Halting Problem and explain why an algorithm that decides whether any arbitrary program halts cannot exist.",
            "cs-recursion",
            1.3,
            "The Halting Problem asks whether a program can determine, for any arbitrary program $P$ and input $I$, whether $P(I)$ will eventually halt or run forever. Turing proved this impossible using a diagonal proof by contradiction: Suppose a decider $H(P, I)$ exists. Construct a program $D(X)$ that calls $H(X, X)$. If $H$ returns True (halts), $D$ enters an infinite loop. If $H$ returns False, $D$ terminates immediately. Evaluating $D(D)$ creates an impossible paradox ($D$ halts iff $D$ loops), proving no such general decider $H$ can exist.",
        ),
        (
            "Explain Karnaugh Map Minimization Logic",
            "Explain why Gray code ordering of rows and columns is essential in Karnaugh maps.",
            "dl-kmap",
            1.1,
            "Gray code ensures that adjacent cells differ by exactly one variable (one bit flip). By arranging adjacent cells to have Hamming distance 1, grouping adjacent cells of size $2^k$ enables algebraic simplification based on $x + x' = 1$. This directly eliminates variables whose states toggle across the group.",
        ),
        (
            "Explain Work-Energy Theorem",
            "Derive the relation between net work done and change in kinetic energy from Newton's Second Law for 1D motion.",
            "phy-energy",
            1.1,
            "$W_{\\text{net}} = \\int F_{\\text{net}} dx$. By Newton's second law, $F = m \\frac{dv}{dt}$. Since $dx = v dt$, $W_{\\text{net}} = \\int m \\frac{dv}{dt} v dt = \\int_{v_i}^{v_f} m v dv = \\frac{1}{2}m v_f^2 - \\frac{1}{2}m v_i^2 = \\Delta KE$.",
        ),
        (
            "Differentiate Process vs Thread",
            "Contrast a process and a thread in modern operating systems regarding memory space and context-switch overhead.",
            "cs-var-loops",
            1.0,
            "A process is an executing program instance with its own private virtual address space, file descriptors, and heap. A thread is the smallest unit of CPU execution within a process; multiple threads in the same process share the text, data, and heap segments but have their own registers and stack. Thread context switching has significantly lower overhead because virtual memory page tables do not need to be flushed.",
        ),
        (
            "Explain Quicksort Worst Case and Mitigation",
            "What causes Quicksort's worst-case $O(n^2)$ behavior, and how does randomized pivot selection or median-of-three fix it?",
            "dsa-arrays",
            1.2,
            "Quicksort suffers $O(n^2)$ time when the chosen pivot is repeatedly the extreme minimum or maximum element (such as picking the first element on already sorted data), resulting in partitions of size $0$ and $n-1$. Randomized pivot selection or median-of-three picks a pivot that with high probability divides the array roughly equally, ensuring $O(n \\log n)$ average performance.",
        ),
        (
            "Explain Principle of Superposition in Waves",
            "State the principle of superposition and explain constructive vs destructive interference.",
            "phy-kinematics",
            1.0,
            "The principle of superposition states that when two or more overlapping waves traverse the same medium, the net displacement of the medium at any point is the vector sum of the individual displacements. Constructive interference occurs when waves arrive in phase (peaks align with peaks), yielding maximum amplitude. Destructive interference occurs when waves arrive out of phase by $\\pi$ (peaks align with troughs), canceling displacement.",
        ),
        (
            "Explain Central Limit Theorem",
            "State the Central Limit Theorem and explain its profound significance in empirical data science.",
            "prob-random-var",
            1.3,
            "The Central Limit Theorem (CLT) states that given independent and identically distributed (i.i.d.) random variables with finite mean $\\mu$ and variance $\\sigma^2$, the normalized sample mean approaches a standard normal distribution $\\mathcal{N}(0, 1)$ as sample size $n \\to \\infty$, regardless of the underlying population distribution. This allows constructing confidence intervals and hypothesis tests without knowing the exact distribution.",
        ),
        (
            "Explain Dynamic Programming vs Divide & Conquer",
            "What are the two core prerequisites for Dynamic Programming, and how does it differ from standard Divide and Conquer?",
            "dsa-dp",
            1.2,
            "Dynamic Programming requires: 1) Optimal Substructure (optimal solution to problem contains optimal solutions to subproblems), and 2) Overlapping Subproblems. Standard Divide & Conquer (e.g. MergeSort) divides problems into independent, non-overlapping subproblems. In contrast, DP memoizes or tabulates solutions to recurring subproblems to avoid redundant exponential computation.",
        ),
        (
            "Explain Shannon's Expansion Theorem",
            "Explain Shannon's Expansion Theorem in Boolean logic and how it relates to multiplexer synthesis.",
            "dl-combinational",
            1.2,
            "Shannon's expansion states that any Boolean function $f(x_1, \\dots, x_n)$ can be expressed around variable $x_i$ as: $f = x_i \\cdot f(x_i=1) + x_i' \\cdot f(x_i=0)$. This maps directly to hardware: $x_i$ acts as the select line of a 2-to-1 Multiplexer, with $f(x_i=0)$ connected to input 0 and $f(x_i=1)$ connected to input 1.",
        ),
    ]

    for title, stmt, concept, diff, sol in theory_defs:
        subject = (
            "Data Structures & Algorithms"
            if "dsa" in concept
            else (
                "Programming Basics"
                if "cs" in concept
                else (
                    "Physics Mechanics"
                    if "phy" in concept
                    else (
                        "Calculus & Linear Algebra"
                        if "math" in concept
                        else ("Probability & Statistics" if "prob" in concept else "Digital Logic")
                    )
                )
            )
        )
        problems.append(
            {
                "title": title,
                "statement_md": stmt,
                "subject": subject,
                "difficulty_b": diff,
                "type": "theory",
                "reference_solution_md": sol,
                "concept_ids": [concept],
                "rubric": {
                    "definition": "Clearly defines core principles and scientific terms",
                    "derivation_or_mechanism": "Explains underlying physical/mathematical mechanism",
                    "synthesis": "Provides accurate comparison or real-world example",
                },
                "test_cases": None,
                "visibility": "public",
            }
        )

    return problems


async def seed_database():
    """Seed the database with complete initial data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Check if already seeded
        result = await session.execute(select(User).where(User.email == "alex.demo@thinkfree.demo"))
        if result.scalar_one_or_none():
            print("Database already contains seed data. Skipping.")
            return

        print(
            "Seeding ThinkFree database with 40 problems, concepts, demo professor and student..."
        )

        # 2. Institution
        inst = Institution(
            id="bits-pilani-f102",
            name="BITS Pilani (F102 Group 68)",
            lti_config={
                "client_id": "bits-f102-demo",
                "auth_url": "https://lms.bits-pilani.ac.in/auth",
            },
            plan="enterprise",
        )
        session.add(inst)

        # 3. Demo Professor
        prof = User(
            id="prof-sharma-1",
            name="Prof. Sharma (Instructor)",
            email="prof.sharma@thinkfree.demo",
            password_hash=AuthService.get_password_hash("thinkfree_prof_pass"),
            role="professor",
            institution_id=inst.id,
            locale="en",
        )
        session.add(prof)

        # 4. Demo Student
        student = User(
            id="student-alex-demo",
            name="Alex Chen (Demo Student)",
            email="alex.demo@thinkfree.demo",
            password_hash=AuthService.get_password_hash("thinkfree_student_pass"),
            role="student",
            institution_id=inst.id,
            locale="en",
            consent_flags={
                "audio_retention": True,
                "analytics_sharing": True,
                "professor_sharing": True,
            },
        )
        session.add(student)

        # 5. Course
        course = Course(
            id="course-cs101",
            institution_id=inst.id,
            name="CS F111: Computer Programming & Problem Solving",
            professor_id=prof.id,
        )
        session.add(course)

        # 6. Enrollment
        enrollment = Enrollment(course_id=course.id, student_id=student.id)
        session.add(enrollment)

        # 7. Concepts
        for c in CONCEPTS_DATA:
            concept = Concept(
                id=c["id"], name=c["name"], subject=c["subject"], parent_id=c["parent_id"]
            )
            session.add(concept)

        # 8. Problems (40 total)
        problems_data = generate_seed_problems()
        for p_data in problems_data:
            p = Problem(
                title=p_data["title"],
                statement_md=p_data["statement_md"],
                subject=p_data["subject"],
                difficulty_b=p_data["difficulty_b"],
                type=p_data["type"],
                reference_solution_md=p_data["reference_solution_md"],
                rubric=p_data["rubric"],
                test_cases=p_data["test_cases"],
                concept_ids=p_data["concept_ids"],
                created_by=prof.id,
                visibility=p_data["visibility"],
            )
            session.add(p)

        # 9. 60 Days of Synthetic Daily Stats for Demo Student
        today = date.today()
        base_its = 55.0
        base_adr = 0.50

        for day_offset in range(60, -1, -1):
            stat_date = today - timedelta(days=day_offset)
            # Simulated improvement trend over 60 days
            progress_factor = (60 - day_offset) / 60.0
            daily_active_mins = random.randint(30, 110)
            daily_flow_mins = int(daily_active_mins * random.uniform(0.4, 0.8))
            self_solves = int(random.randint(1, 4) * (1.0 + progress_factor))
            ai_assisted = max(0, int(random.randint(0, 3) * (1.2 - progress_factor * 0.7)))

            # ITS grows from ~55 up to ~84; ADR drops from ~0.50 down to ~0.18
            its_val = min(95.0, base_its + (progress_factor * 28.0) + random.uniform(-3.0, 3.0))
            adr_val = max(0.08, base_adr - (progress_factor * 0.32) + random.uniform(-0.04, 0.04))

            stat = DailyStats(
                student_id=student.id,
                date=stat_date,
                active_minutes=daily_active_mins,
                flow_minutes=daily_flow_mins,
                self_solves=self_solves,
                ai_assisted=ai_assisted,
                its=round(its_val, 1),
                adr=round(adr_val, 2),
            )
            session.add(stat)

        # 10. Sample Concept Mastery Records for Alex
        for c in CONCEPTS_DATA:
            p_known = random.uniform(0.45, 0.92)
            mastery = Mastery(
                student_id=student.id,
                concept_id=c["id"],
                p_known=p_known,
                updated_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                next_review_at=datetime.utcnow() + timedelta(days=random.randint(1, 7)),
                ease=2.5,
                interval_days=4.0,
            )
            session.add(mastery)

        # 11. Initial Badges for Alex
        badges_to_award = [
            (
                "independent_solver_20",
                "Independent Solver: 20 unaided solves",
                {"unaided_count": 24},
            ),
            (
                "streak_7_days",
                "Focus Streak: 7 consecutive days with no AI shortcuts",
                {"streak": 7},
            ),
            (
                "deep_explainer",
                "Voice Explainer: 10 validations at High Confidence",
                {"validations": 12},
            ),
        ]
        for kind, name, payload in badges_to_award:
            badge = Badge(
                student_id=student.id,
                kind=kind,
                payload={"title": name, **payload},
                signature=f"sig_{kind}_{student.id}_verified",
            )
            session.add(badge)

        await session.commit()
        print("Database successfully seeded!")


if __name__ == "__main__":
    asyncio.run(seed_database())
