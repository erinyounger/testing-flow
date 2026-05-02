import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from tflow.agents.subprocess_agent import SubprocessAgent
from tflow.agents.builtin_prompts import PLANNER_PROMPT, EXECUTOR_PROMPT
from tflow.artifacts.plan import PlanArtifact


class WorkflowEngine:
    """Workflow template engine with variable substitution and conditionals"""

    def __init__(self, workflow_dir: str, plan_artifact: Optional[PlanArtifact] = None):
        self.workflow_dir = Path(workflow_dir)
        self.plan_artifact = plan_artifact
        self.agent = SubprocessAgent()

    def load(self, workflow_name: str) -> str:
        """Load workflow template"""
        workflow_file = self.workflow_dir / f"{workflow_name}.md"

        if not workflow_file.exists():
            return ""

        return workflow_file.read_text()

    def run(self, context: Dict[str, Any], skip_steps: List[str] = None) -> Dict[str, Any]:
        """Execute workflow with context"""
        workflow_name = context.get("workflow_name", "quick")
        template = self.load(workflow_name)

        if not template:
            return {"prepared": "", "steps": [], "skipped": []}

        skip_steps = skip_steps or []

        # Variable substitution
        prepared = self._substitute(template, context)

        # Process conditional blocks
        steps = self._process_conditionals(prepared, context)

        # Extract step names and filter skipped
        step_names = []
        for line in steps:
            line = line.strip()
            if not line:
                continue
            # Skip markdown headers
            if line.startswith("#"):
                continue
            # Try "Step: name" pattern first
            match = re.match(r"Step:\s*(\w+)\s*$", line)
            if match:
                step_names.append(match.group(1))
            else:
                # Use the whole line as step name
                step_names.append(line)

        filtered_steps = [s for s in step_names if s not in skip_steps]

        return {
            "prepared": prepared,
            "steps": filtered_steps,
            "skipped": skip_steps
        }

    def execute(self, context: Dict[str, Any], skip_steps: List[str] = None) -> Dict[str, Any]:
        """Execute workflow steps and return results"""
        result = self.run(context, skip_steps)
        steps = result.get("steps", [])

        execution_results = []
        for step in steps:
            step_result = self._execute_step(step, context)
            execution_results.append(step_result)

        result["execution_results"] = execution_results
        return result

    def _execute_step(self, step: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step using SubprocessAgent"""
        # Build command from step template
        command = self._build_step_command(step, context)

        if not command:
            return {"step": step, "success": False, "error": "No command defined for step"}

        # Execute via agent - use "claude" agent_type for real code generation
        agent_result = self.agent.run(command, agent_type="claude", timeout=120)

        return {
            "step": step,
            "success": agent_result.success,
            "output": agent_result.output,
            "error": agent_result.error
        }

    def _build_step_command(self, step: str, context: Dict[str, Any]) -> str:
        """Build command for a step using Claude prompts"""
        task = context.get("task", "")
        filename = context.get("filename", self._task_to_filename(task))

        if step == "plan":
            prompt = PLANNER_PROMPT.format(task=task)
            return prompt
        elif step == "execute":
            prompt = EXECUTOR_PROMPT.format(task=task, filename=filename)
            return prompt
        elif step == "verify":
            return f"echo 'Verifying implementation for task: {task}'"
        elif step == "commit":
            return f"echo 'Committing changes for task: {task}'"

        return f"echo 'Running step: {step}'"

    def _task_to_filename(self, task: str) -> str:
        """Convert task description to a reasonable filename"""
        # Simple heuristic: take first few words, lowercase, underscores
        words = task.split()[:3]
        filename = "_".join(words).lower()
        # Add .py if it looks like code
        if not filename.endswith(".py"):
            filename = f"{filename}.py"
        return filename

    def _substitute(self, template: str, context: Dict[str, Any]) -> str:
        """Replace {{variable}} with context values"""
        result = template

        for key, value in context.items():
            pattern = r"\{\{\s*" + re.escape(key) + r"\s*\}\}"
            result = re.sub(pattern, str(value), result)

        return result

    def _process_conditionals(self, text: str, context: Dict[str, Any]) -> List[str]:
        """Process {{#if}} blocks and return lines"""
        lines = text.split("\n")
        result_lines = []
        skip_block = False
        skip_else = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle {{#if condition}}
            if_match = re.match(r"\{\{#if\s+(\w+)\s*\}\}", line)
            if if_match:
                condition_var = if_match.group(1)
                if not context.get(condition_var, False):
                    skip_block = True
                i += 1
                continue

            # Handle {{/if}}
            if re.match(r"\{\{/if\}\}", line):
                skip_block = False
                skip_else = False
                i += 1
                continue

            # Handle {{#else}}
            if re.match(r"\{\{#else\}\}", line):
                skip_block = not skip_block
                i += 1
                continue

            # Skip block content if in skip mode
            if skip_block:
                i += 1
                continue

            result_lines.append(line)
            i += 1

        return result_lines