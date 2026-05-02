import click
from pathlib import Path


@click.command()
@click.argument("task")
@click.option("--full", is_flag=True, help="Run full workflow")
@click.option("--discuss", is_flag=True, help="Include discussion phase")
def quick(task: str, full: bool, discuss: bool):
    """Quick task execution workflow"""
    click.echo(f"Quick task: {task}")

    if full:
        click.echo("Running full workflow")
    if discuss:
        click.echo("Including discussion phase")

    # Placeholder for actual implementation
    click.echo(f"Executing: {task}")
    click.echo("Workflow completed (placeholder)")


if __name__ == "__main__":
    quick()