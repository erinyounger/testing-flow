# Built-in prompts for agents

DEFAULT_SHELL_PROMPT = """Execute the following shell command and return the output:
{prompt}
"""

DEFAULT_CLAUDE_PROMPT = """You are a coding assistant. Respond to the following request:
{prompt}
"""

CLAUDE_CODE_PROMPT = """You are an expert programmer. Write code to solve the following problem:
{prompt}

Provide only the code solution, no explanations.
"""

PLAN_ANALYSIS_PROMPT = """Analyze the following task and create a structured plan:

Task: {task}

Consider:
1. Scope and requirements
2. Potential challenges
3. Implementation approach
4. Verification criteria

Provide a detailed plan with steps.
"""

PLANNER_PROMPT = """You are a task decomposition specialist. Break down the following task into specific, actionable implementation steps.

Task: {task}

Output your response in this format:
1. Step name: description of what to do
2. Step name: description of what to do
...

Focus on concrete, executable steps that produce verifiable results.
"""

EXECUTOR_PROMPT = """You are an expert programmer. Implement the following task and output only the code.

Task: {task}
Filename: {filename}

Write complete, working code. Output only the filename and code content wrapped in ```.
"""