import click
from pathlib import Path

from tflow.engine.workflow_engine import WorkflowEngine
from tflow.artifacts.plan import PlanArtifact
from tflow.state.state_manager import StateManager


WORKFLOW_DIR = ".workflow"


@click.command()
@click.argument("phase")
@click.option("--watch", is_flag=True, help="Watch for changes")
def execute(phase: str, watch: bool):
    """Execute phase workflow"""
    click.echo(f"Executing phase: {phase}")

    # Initialize artifacts
    plan_artifact = PlanArtifact(WORKFLOW_DIR)
    state_manager = StateManager(WORKFLOW_DIR)

    # Initialize workflow engine
    engine = WorkflowEngine(WORKFLOW_DIR, plan_artifact)

    # Execute phase
    context = {
        "workflow_name": phase,
        "phase": phase
    }

    result = engine.execute(context)

    # Update state
    state = state_manager.load()
    state.status = "executing"
    state_manager.save(state)

    if watch:
        click.echo("Watching for changes...")

    execution_results = result.get("execution_results", [])
    click.echo(f"Executed {len(execution_results)} steps")

    for exec_result in execution_results:
        status = "OK" if exec_result.get("success") else "FAILED"
        click.echo(f"  - {exec_result.get('step')}: {status}")

    click.echo("Execution completed")


if __name__ == "__main__":
    execute()