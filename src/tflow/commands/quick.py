import click
from pathlib import Path

from tflow.engine.workflow_engine import WorkflowEngine
from tflow.artifacts.plan import PlanArtifact
from tflow.artifacts.verification import VerificationArtifact
from tflow.state.state_manager import StateManager


WORKFLOW_DIR = ".workflow"


@click.command()
@click.argument("task")
@click.option("--full", is_flag=True, help="Run full workflow")
@click.option("--discuss", is_flag=True, help="Include discussion phase")
def quick(task: str, full: bool, discuss: bool):
    """Quick task execution workflow"""
    click.echo(f"Quick task: {task}")

    # Create workflow directory structure
    workflow_path = Path(WORKFLOW_DIR)
    workflow_path.mkdir(exist_ok=True)

    # Initialize artifacts
    plan_artifact = PlanArtifact(WORKFLOW_DIR)
    verification_artifact = VerificationArtifact(WORKFLOW_DIR)
    state_manager = StateManager(WORKFLOW_DIR)

    # Create plan
    plan = plan_artifact.create(task, {"approach": "quick"})

    # Update state
    state = state_manager.load()
    state.status = "executing"
    state_manager.save(state)

    # Initialize workflow engine
    engine = WorkflowEngine(WORKFLOW_DIR, plan_artifact)

    # Create quick workflow file if it doesn't exist
    quick_workflow = workflow_path / "quick.md"
    if not quick_workflow.exists():
        quick_workflow.write_text(_default_quick_workflow())

    # Execute workflow
    context = {
        "workflow_name": "quick",
        "task": task,
        "discuss": discuss,
        "full": full
    }

    result = engine.execute(context)

    # Update state on completion
    state = state_manager.load()
    state.status = "completed"
    state_manager.save(state)

    click.echo(f"Workflow completed. Steps executed: {len(result.get('execution_results', []))}")


def _default_quick_workflow() -> str:
    """Default quick workflow template"""
    return """# Quick Workflow

{{#if discuss}}
讨论阶段
{{/if}}

Step: plan
Step: execute
Step: verify
Step: commit
"""


if __name__ == "__main__":
    quick()