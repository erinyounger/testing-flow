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