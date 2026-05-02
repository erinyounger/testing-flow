import re
from pathlib import Path
from typing import Dict, Any, List


class WorkflowEngine:
    """Workflow template engine with variable substitution and conditionals"""

    def __init__(self, workflow_dir: str):
        self.workflow_dir = Path(workflow_dir)

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