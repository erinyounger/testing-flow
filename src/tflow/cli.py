import click
from tflow.commands.quick import quick
from tflow.commands.plan import plan
from tflow.commands.execute import execute


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Testing-Flow - Task execution workflow system"""
    pass


cli.add_command(quick)
cli.add_command(plan)
cli.add_command(execute)


if __name__ == "__main__":
    cli()