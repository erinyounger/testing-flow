"""Agent 统一执行器 - 对应 Maestro 的 CliAgentRunner"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable
import asyncio
import subprocess
from pathlib import Path
import uuid
import time


class AgentType(Enum):
    CLAUDE_CODE = "claude-code"
    GEMINI = "gemini"
    QWEN = "qwen"
    CODEX = "codex"
    OPENCODE = "opencode"


class ExecutionMode(Enum):
    ANALYSIS = "analysis"
    WRITE = "write"


class BackendType(Enum):
    DIRECT = "direct"
    TERMINAL = "terminal"


@dataclass
class RunOptions:
    prompt: str
    tool: AgentType
    mode: ExecutionMode
    work_dir: Path
    model: str | None = None
    rule: str | None = None
    exec_id: str | None = None
    backend: BackendType = BackendType.DIRECT
    settings_file: str | None = None
    session_id: str | None = None


@dataclass
class ExecutionResult:
    exec_id: str
    exit_code: int | None
    output: str
    success: bool
    duration_ms: int
    entries: list[dict] = field(default_factory=list)


class AgentProcess:
    """Agent 进程封装"""

    def __init__(self, process: subprocess.Popen, exec_id: str, agent_type: AgentType):
        self.process = process
        self.exec_id = exec_id
        self.agent_type = agent_type
        self._output = ""

    async def wait(self) -> int:
        """等待进程完成"""
        self._output, _ = self.process.communicate()
        return self.process.returncode

    def get_output(self) -> str:
        """获取输出"""
        return self._output

    def stop(self) -> None:
        """停止进程"""
        self.process.terminate()


class AgentExecutor:
    """统一 Agent 执行器"""

    TOOL_MAP = {
        "gemini": AgentType.GEMINI,
        "qwen": AgentType.QWEN,
        "codex": AgentType.CODEX,
        "claude": AgentType.CLAUDE_CODE,
        "opencode": AgentType.OPENCODE,
    }

    def __init__(
        self,
        broker_client=None,
        session_store=None,
        realtime_bridge=None,
    ):
        self.broker = broker_client
        self.store = session_store
        self.bridge = realtime_bridge
        self._entry_handlers: list[Callable] = []

    async def run(self, options: RunOptions) -> ExecutionResult:
        """执行 Agent 并返回结果"""
        start = time.time()

        # 1. 确定 Agent 类型
        agent_type = self.TOOL_MAP.get(options.tool.value, options.tool)

        # 2. 组装 Prompt
        full_prompt = self._assemble_prompt(options)

        # 3. 启动进程
        process = await self._spawn_process(agent_type, full_prompt, options)

        # 4. 收集输出和事件
        entries = []
        if self.store:
            self.store.append_entry(process.exec_id, {"type": "spawn", "process": process})

        # 5. 等待完成
        exit_code = await process.wait()
        output = process.get_output()

        # 6. 保存历史
        if self.store:
            self.store.append_entry(process.exec_id, {
                "type": "completion",
                "exit_code": exit_code,
                "output": output,
            })

        return ExecutionResult(
            exec_id=process.exec_id,
            exit_code=exit_code,
            output=output,
            success=exit_code == 0,
            duration_ms=int((time.time() - start) * 1000),
            entries=entries,
        )

    async def run_async(
        self,
        options: RunOptions,
        on_entry: Callable[[dict], Awaitable[None]] | None = None,
    ) -> str:
        """异步执行，返回 exec_id"""
        exec_id = options.exec_id or f"run-{uuid.uuid4().hex[:8]}"
        options.exec_id = exec_id

        async def _run():
            result = await self.run(options)
            if on_entry:
                await on_entry({
                    "type": "completion",
                    "exec_id": exec_id,
                    "result": result,
                })

        asyncio.create_task(_run())
        return exec_id

    async def _spawn_process(
        self,
        agent_type: AgentType,
        prompt: str,
        options: RunOptions,
    ) -> AgentProcess:
        """启动 Agent 进程"""
        cmd = self._build_command(agent_type, prompt, options)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=options.work_dir,
            text=True,
        )

        return AgentProcess(
            process=process,
            exec_id=options.exec_id or str(process.pid),
            agent_type=agent_type,
        )

    def _build_command(
        self,
        agent_type: AgentType,
        prompt: str,
        options: RunOptions,
    ) -> list[str]:
        """构建 agent 特定命令行

        支持的 agent 类型及调用方式:
        - CLAUDE_CODE: claude -p <prompt> [--model <model>] [--no-input]
        - GEMINI: gemini -p <prompt> [--model <model>] [--api-key <key>]
        - QWEN: qwen chat -p <prompt> [--model <model>]
        - CODEX: codex '<prompt>' [--language <lang>]
        - OPENCODE: opencode -p <prompt> [--provider <provider>]
        """
        cmd: list[str] = []

        if agent_type == AgentType.CLAUDE_CODE:
            cmd = ["claude", "-p", prompt, "--no-input"]
            if options.model:
                cmd.extend(["--model", options.model])
            if options.settings_file:
                cmd.extend(["--settings", options.settings_file])

        elif agent_type == AgentType.GEMINI:
            cmd = ["gemini", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        elif agent_type == AgentType.QWEN:
            cmd = ["qwen", "chat", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        elif agent_type == AgentType.CODEX:
            cmd = ["codex", f"'{prompt}'"]
            if options.model:
                cmd.extend(["--language", options.model])

        elif agent_type == AgentType.OPENCODE:
            cmd = ["opencode", "-p", prompt]
            if options.model:
                cmd.extend(["--model", options.model])

        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        return cmd

    def _assemble_prompt(
        self,
        options: RunOptions,
        context: dict | None = None,
    ) -> str:
        """组装 agent 特定 Prompt

        不同 agent 有不同的 prompt 格式偏好，这里做差异化处理。
        """
        parts = []

        # 1. Agent 特定的 system prompt
        system_prompts = {
            AgentType.CLAUDE_CODE: "You are a helpful coding assistant. Follow the user's instructions precisely.",
            AgentType.GEMINI: "You are Gemini, a helpful AI assistant.",
            AgentType.QWEN: "你是阿里云通义千问助手，请根据用户的问题提供准确的回答。",
            AgentType.CODEX: "You are Claude Code, an AI coding assistant.",
            AgentType.OPENCODE: "You are an AI assistant powered by OpenCode.",
        }
        if options.tool in system_prompts:
            parts.append(f"# System\n{system_prompts[options.tool]}")

        # 2. Mode 相关的指令
        if options.mode == ExecutionMode.WRITE:
            parts.append("# Mode\nYou are in write mode. Write clean, well-documented code.")
        else:
            parts.append("# Mode\nYou are in analysis mode. Provide clear analysis and reasoning.")

        # 3. Workflow Context (如果提供)
        if context:
            if "goal" in context:
                parts.append(f"# Goal\n{context['goal']}")
            if "scope" in context:
                parts.append(f"# Scope\n{', '.join(context['scope'])}")
            if "plan" in context:
                parts.append(f"# Plan\n{context['plan']}")

        # 4. Rule (如果提供)
        if options.rule:
            parts.append(f"# Rules\n{options.rule}")

        # 5. User prompt
        parts.append(f"# Task\n{options.prompt}")

        return "\n\n".join(parts)
