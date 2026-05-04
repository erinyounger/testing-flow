"""tflow CLI entry point"""

import click
import sys
from pathlib import Path

from tflow import __version__
from tflow.core import AgentExecutor, AgentType, ExecutionMode, BackendType, RunOptions


@click.group()
@click.version_option(version=__version__)
def cli():
    """tflow - Workflow orchestration CLI with MCP endpoint support"""
    pass


@cli.command()
@click.option("--goal", required=True, help="Workflow goal")
@click.option("--scope", multiple=True, help="Scope paths")
@click.option("--plan", help="Execution plan file")
def run(goal: str, scope: tuple, plan: str):
    """Execute a workflow with the given goal"""
    click.echo(f"Running workflow: {goal}")
    click.echo(f"Scope: {', '.join(scope) if scope else 'all'}")

    executor = AgentExecutor()

    options = RunOptions(
        prompt=goal,
        tool=AgentType.CLAUDE_CODE,
        mode=ExecutionMode.ANALYSIS,
        work_dir=Path.cwd(),
    )

    try:
        import asyncio
        result = asyncio.run(executor.run(options))
        click.echo(f"Exit code: {result.exit_code}")
        click.echo(f"Success: {result.success}")
        if result.output:
            click.echo(f"Output:\n{result.output[:500]}...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("prompt")
@click.option("--to", "agent", default="claude-code", help="Agent type (claude-code, gemini, qwen, codex, opencode)")
@click.option("--mode", default="analysis", type=click.Choice(["analysis", "write"]), help="Execution mode")
@click.option("--model", help="Model to use")
def delegate(prompt: str, agent: str, mode: str, model: str):
    """Delegate a task to an agent"""
    agent_type_map = {
        "claude-code": AgentType.CLAUDE_CODE,
        "gemini": AgentType.GEMINI,
        "qwen": AgentType.QWEN,
        "codex": AgentType.CODEX,
        "opencode": AgentType.OPENCODE,
    }

    agent_type = agent_type_map.get(agent, AgentType.CLAUDE_CODE)
    exec_mode = ExecutionMode.WRITE if mode == "write" else ExecutionMode.ANALYSIS

    click.echo(f"Delegating to {agent}: {prompt[:50]}...")

    executor = AgentExecutor()

    options = RunOptions(
        prompt=prompt,
        tool=agent_type,
        mode=exec_mode,
        work_dir=Path.cwd(),
        model=model,
    )

    try:
        import asyncio
        result = asyncio.run(executor.run(options))
        click.echo(f"Exit code: {result.exit_code}")
        click.echo(f"Success: {result.success}")
        if result.output:
            click.echo(f"Output:\n{result.output}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("session", required=False)
def status(session: str | None):
    """Check workflow/status. If session ID provided, show session status."""
    if session:
        click.echo(f"Status for session: {session}")
    else:
        click.echo("tflow status: system operational")

    # Try to connect to broker if available
    try:
        import asyncio
        from tflow.broker import JsonBroker
        broker = JsonBroker()
        jobs = asyncio.run(broker.list_jobs())
        click.echo(f"Active jobs: {len(jobs)}")
    except Exception as e:
        click.echo(f"Broker not available: {e}")


@cli.group()
def session():
    """Manage execution sessions"""
    pass


@session.command("list")
def session_list():
    """List all sessions"""
    click.echo("Sessions:")
    try:
        import asyncio
        from tflow.broker import JsonBroker
        broker = JsonBroker()
        jobs = asyncio.run(broker.list_jobs())
        for job in jobs:
            click.echo(f"  - {job.job_id}: {job.status.value}")
    except Exception as e:
        click.echo(f"No sessions found: {e}")


@session.command("show")
@click.argument("session_id")
def session_show(session_id: str):
    """Show details of a specific session"""
    click.echo(f"Session: {session_id}")
    try:
        import asyncio
        from tflow.broker import JsonBroker
        broker = JsonBroker()
        job = asyncio.run(broker.get_job(session_id))
        if job:
            click.echo(f"  Status: {job.status.value}")
            click.echo(f"  Created: {job.created_at}")
        else:
            click.echo("  Not found")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    cli()
