import click
from pathlib import Path

from tflow.artifacts.plan import PlanArtifact
from tflow.state.state_manager import StateManager


WORKFLOW_DIR = ".workflow"


@click.command()
@click.argument("phase")
@click.option("--output", "-o", help="Output file for plan")
def plan(phase: str, output: str):
    """Plan phase for workflow"""
    click.echo(f"Planning phase: {phase}")

    # Create workflow directory
    workflow_path = Path(WORKFLOW_DIR)
    workflow_path.mkdir(exist_ok=True)

    # Initialize artifacts
    plan_artifact = PlanArtifact(WORKFLOW_DIR)
    state_manager = StateManager(WORKFLOW_DIR)

    # Create plan
    plan = plan_artifact.create(f"Planning: {phase}", {"approach": "planning"})

    # Update state
    state = state_manager.load()
    state.status = "planning"
    state_manager.save(state)

    if output:
        click.echo(f"Output will be saved to: {output}")

    click.echo(f"Plan created: {plan.id}")
    click.echo("Planning completed")


if __name__ == "__main__":
    plan()