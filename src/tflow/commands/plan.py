import click


@click.command()
@click.argument("phase")
@click.option("--output", "-o", help="Output file for plan")
def plan(phase: str, output: str):
    """Plan phase for workflow"""
    click.echo(f"Planning phase: {phase}")

    if output:
        click.echo(f"Output will be saved to: {output}")

    # Placeholder for actual implementation
    click.echo("Planning completed (placeholder)")


if __name__ == "__main__":
    plan()