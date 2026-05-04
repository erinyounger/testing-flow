"""WorkflowEngine - 简单状态机工作流引擎"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable
import asyncio
import uuid
from datetime import datetime

from .state import WorkflowState, WorkflowStatus, WorkflowType


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: str
    success: bool
    output: Any = None
    error: str | None = None


class WorkflowEngine:
    """简单状态机工作流引擎

    线性流程：PARSING → VALIDATING → PLANNING → EXECUTING → VERIFYING → COMPLETING → COMPLETED

    特点：
    - 简单线性状态机，适合固定顺序的流程
    - 易于理解和维护
    - 支持暂停/恢复
    - 事件驱动便于扩展
    """

    # 状态转换定义：当前状态 -> (下一状态, 是否结束)
    TRANSITIONS = {
        WorkflowStatus.IDLE: WorkflowStatus.PARSING,
        WorkflowStatus.PARSING: WorkflowStatus.VALIDATING,
        WorkflowStatus.VALIDATING: WorkflowStatus.PLANNING,
        WorkflowStatus.PLANNING: WorkflowStatus.EXECUTING,
        WorkflowStatus.EXECUTING: WorkflowStatus.VERIFYING,
        WorkflowStatus.VERIFYING: WorkflowStatus.COMPLETING,
        WorkflowStatus.COMPLETING: WorkflowStatus.COMPLETED,
    }

    def __init__(
        self,
        job_manager,           # JobManager 实例
        agent_executor,         # AgentExecutor 实例
        persistence: Any = None,  # 可选持久化
    ):
        self.job_manager = job_manager
        self.agent_executor = agent_executor
        self.persistence = persistence

        # 阶段处理器
        self._handlers: dict[WorkflowStatus, Callable] = {
            WorkflowStatus.PARSING: self._handle_parsing,
            WorkflowStatus.VALIDATING: self._handle_validating,
            WorkflowStatus.PLANNING: self._handle_planning,
            WorkflowStatus.EXECUTING: self._handle_executing,
            WorkflowStatus.VERIFYING: self._handle_verifying,
            WorkflowStatus.COMPLETING: self._handle_completing,
        }

        # 事件订阅
        self._subscribers: list[Callable[[WorkflowState], None]] = []

    async def execute(
        self,
        workflow_type: str,
        goal: str,
        scope: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ) -> WorkflowState:
        """执行工作流"""
        session_id = f"wf-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        workflow_id = f"wf-{uuid.uuid4().hex[:12]}"

        # 初始化状态
        state = WorkflowState(
            workflow_type=WorkflowType(workflow_type),
            workflow_id=workflow_id,
            session_id=session_id,
            status=WorkflowStatus.PARSING,
            current_phase="parsing",
            context={
                "goal": goal,
                "scope": scope or [],
                "options": options or {},
            },
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        # 创建 Job
        job = await self.job_manager.create_job(
            job_type=f"workflow_{workflow_type}",
            metadata={"session_id": session_id, "goal": goal},
        )

        state.context["job_id"] = job.job_id

        # 持久化初始状态
        if self.persistence:
            self.persistence.save_state(state)

        # 通知订阅者
        self._emit(state)

        # 执行状态机循环
        try:
            state = await self._run_loop(state)
        except Exception as e:
            state.status = WorkflowStatus.FAILED
            state.result["error"] = str(e)

        # 最终状态
        state.updated_at = datetime.now().isoformat()
        if self.persistence:
            self.persistence.save_state(state)

        # 更新 Job 状态
        final_status = "completed" if state.status == WorkflowStatus.COMPLETED else "failed"
        await self.job_manager.update_status(
            job.job_id,
            self._to_job_status(state.status),
            "workflow_finished",
            {"status": final_status, "result": state.result},
        )

        self._emit(state)
        return state

    async def _run_loop(self, state: WorkflowState) -> WorkflowState:
        """状态机主循环"""
        while state.status not in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED):
            # 处理暂停状态
            if state.status == WorkflowStatus.PAUSED:
                # 等待恢复信号（实际实现中应该是队列或事件）
                await asyncio.sleep(0.1)
                continue

            handler = self._handlers.get(state.status)
            if handler is None:
                state.status = WorkflowStatus.FAILED
                state.result["error"] = f"No handler for status: {state.status}"
                break

            # 执行当前阶段
            phase_result = await handler(state)

            # 检查阶段执行是否成功，失败则立即停止
            if not phase_result.success:
                state.status = WorkflowStatus.FAILED
                state.result["error"] = phase_result.error
                state.updated_at = datetime.now().isoformat()
                if self.persistence:
                    self.persistence.save_state(state)
                self._emit(state)
                break

            # 更新状态
            next_status = self.TRANSITIONS.get(state.status)
            if next_status is None:
                state.status = WorkflowStatus.COMPLETED
            else:
                state.status = next_status

            state.current_phase = state.status.value
            state.updated_at = datetime.now().isoformat()

            # 持久化（wave 执行完成为单位，避免中间状态不一致）
            if self.persistence:
                self.persistence.save_state(state)

            # 通知订阅者
            self._emit(state)

        return state

    async def pause(self, session_id: str) -> None:
        """暂停工作流"""
        state = self.persistence.load_state(session_id) if self.persistence else None
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        state.status = WorkflowStatus.PAUSED
        state.updated_at = datetime.now().isoformat()

        if self.persistence:
            self.persistence.save_state(state)

        # 同步更新 JobManager
        job_id = state.context.get("job_id")
        if job_id:
            await self.job_manager.update_status(
                job_id,
                "input_required",
                "workflow_paused",
                {"session_id": session_id},
            )

        self._emit(state)

    async def resume(self, session_id: str) -> WorkflowState:
        """恢复工作流"""
        state = self.persistence.load_state(session_id) if self.persistence else None
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        # 从暂停状态恢复到执行状态
        # 如果有 current_phase，可以从该阶段继续
        if state.status == WorkflowStatus.PAUSED:
            # 恢复到上一个状态继续执行
            state.status = WorkflowStatus.PLANNING  # 或根据 current_phase 推断

        state.updated_at = datetime.now().isoformat()

        # 同步更新 JobManager
        job_id = state.context.get("job_id")
        if job_id:
            await self.job_manager.update_status(
                job_id,
                "running",
                "workflow_resumed",
                {"session_id": session_id},
            )

        # 继续状态机循环
        return await self._run_loop(state)

    async def cancel(self, session_id: str, force: bool = False) -> None:
        """取消工作流

        Args:
            session_id: 会话 ID
            force: 是否强制终止 (杀死运行中的进程)
        """
        state = self.persistence.load_state(session_id) if self.persistence else None
        if not state:
            raise ValueError(f"Session not found: {session_id}")

        state.status = WorkflowStatus.FAILED
        state.result["cancelled"] = True
        state.result["force_cancelled"] = force
        state.updated_at = datetime.now().isoformat()

        if self.persistence:
            self.persistence.save_state(state)

        # 通知 JobManager 杀死相关进程
        job_id = state.context.get("job_id")
        if job_id and force:
            # 强制模式下，通知 JobManager 终止相关任务
            await self.job_manager.update_status(
                job_id,
                "cancelled",
                "force_cancelled",
                {"force": True}
            )

        # 同步更新 JobManager
        job_id = state.context.get("job_id")
        if job_id:
            await self.job_manager.update_status(
                job_id,
                "cancelled",
                "workflow_cancelled",
                {"session_id": session_id},
            )

        self._emit(state)

    def get_status(self, session_id: str) -> WorkflowState | None:
        """查询工作流状态"""
        return self.persistence.load_state(session_id) if self.persistence else None

    def list_sessions(self) -> list[str]:
        """列出所有工作流会话"""
        if not self.persistence:
            return []
        return self.persistence.list_sessions()

    async def _handle_parsing(self, state: WorkflowState) -> PhaseResult:
        """解析阶段"""
        try:
            goal = state.context["goal"]
            scope = state.context["scope"]

            # 解析参数和目标
            state.context["parsed_goal"] = goal
            state.context["parsed_scope"] = scope

            return PhaseResult(phase="parsing", success=True, output={"goal": goal, "scope": scope})
        except Exception as e:
            return PhaseResult(phase="parsing", success=False, error=str(e))

    async def _handle_validating(self, state: WorkflowState) -> PhaseResult:
        """验证阶段"""
        try:
            scope = state.context.get("parsed_scope", [])

            # 验证项目结构
            # TODO: 调用验证器

            state.context["validation_passed"] = True
            return PhaseResult(phase="validating", success=True, output={"valid": True})
        except Exception as e:
            return PhaseResult(phase="validating", success=False, error=str(e))

    async def _handle_planning(self, state: WorkflowState) -> PhaseResult:
        """规划阶段 - 调用 Planner Agent"""
        try:
            goal = state.context["parsed_goal"]
            scope = state.context["parsed_scope"]

            # 调用 Planner Agent
            result = await self.agent_executor.run(
                {"prompt": f"分析需求并制定测试计划: {goal}\n范围: {scope}"}
            )

            state.context["plan"] = result.output if hasattr(result, 'output') else str(result)
            state.result["plan"] = state.context["plan"]

            return PhaseResult(phase="planning", success=True, output=state.context["plan"])
        except Exception as e:
            return PhaseResult(phase="planning", success=False, error=str(e))

    async def _handle_executing(self, state: WorkflowState) -> PhaseResult:
        """执行阶段 - 支持 Waves 分批并行执行

        plan.json 定义了 waves 结构:
        {
            "waves": [
                {"wave": 1, "tasks": ["TASK-001", "TASK-002"]},
                {"wave": 2, "tasks": ["TASK-003", "TASK-004"]},
            ]
        }

        每个 wave 内的 tasks 可以并行执行，所有 wave 串行执行。
        """
        try:
            plan = state.context.get("plan", {})
            waves = plan.get("waves", [[]])  # 默认一个 wave 包含所有任务
            tasks = state.context.get("tasks", [])

            if not waves or waves == [[]]:
                # 没有 waves 结构，降级为传统方式：整体执行
                waves = [[t["id"] for t in tasks]] if tasks else [[]]

            wave_results = []
            total_tasks = sum(len(w["tasks"]) for w in waves)
            completed_tasks = 0

            for wave_idx, wave in enumerate(waves):
                wave_tasks = wave.get("tasks", [])
                wave_result = {
                    "wave": wave_idx + 1,
                    "tasks": [],
                    "completed": 0,
                    "failed": 0,
                }

                # 并行执行当前 wave 内的所有 tasks
                async def execute_single_task(task_id: str) -> dict:
                    task = next((t for t in tasks if t.get("id") == task_id), None)
                    if not task:
                        return {"task_id": task_id, "success": False, "error": "Task not found"}

                    # 调用 Executor Agent 执行单个任务
                    result = await self.agent_executor.run(
                        {"prompt": f"执行任务 {task_id}:\n{task.get('description', '')}\n范围: {task.get('scope', '')}"}
                    )

                    return {
                        "task_id": task_id,
                        "success": result.success if hasattr(result, 'success') else True,
                        "output": result.output if hasattr(result, 'output') else str(result),
                        "exit_code": result.exit_code if hasattr(result, 'exit_code') else 0,
                    }

                # 执行当前 wave 的所有任务（并行）
                task_results = await asyncio.gather(
                    *[execute_single_task(tid) for tid in wave_tasks],
                    return_exceptions=True,
                )

                # 收集结果
                for task_result in task_results:
                    if isinstance(task_result, Exception):
                        wave_result["failed"] += 1
                        wave_result["tasks"].append({
                            "error": str(task_result),
                        })
                    elif task_result.get("success"):
                        wave_result["completed"] += 1
                        wave_result["tasks"].append(task_result)
                    else:
                        wave_result["failed"] += 1
                        wave_result["tasks"].append(task_result)

                    completed_tasks += 1

                # 更新进度
                state.context["tasks_completed"] = completed_tasks
                state.context["tasks_total"] = total_tasks

                # 持久化进度
                if self.persistence:
                    self.persistence.save_state(state)

                wave_results.append(wave_result)

                # 如果当前 wave 有失败的任务，可以选择停止或继续
                if wave_result["failed"] > 0 and state.context.get("options", {}).get("stop_on_failure"):
                    break

            state.result["waves"] = wave_results
            state.result["execution"] = {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "wave_count": len(waves),
                "wave_results": wave_results,
            }

            return PhaseResult(
                phase="executing",
                success=True,
                output={
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "wave_count": len(waves),
                },
            )
        except Exception as e:
            return PhaseResult(phase="executing", success=False, error=str(e))

    async def _handle_verifying(self, state: WorkflowState) -> PhaseResult:
        """验证阶段 - 调用 Verifier Agent"""
        try:
            execution = state.result.get("execution", "")

            # 调用 Verifier Agent
            result = await self.agent_executor.run(
                {"prompt": f"验证测试执行结果:\n{execution}"}
            )

            state.result["verification"] = result.output if hasattr(result, 'output') else str(result)

            return PhaseResult(phase="verifying", success=True, output=state.result["verification"])
        except Exception as e:
            return PhaseResult(phase="verifying", success=False, error=str(e))

    async def _handle_completing(self, state: WorkflowState) -> PhaseResult:
        """完成阶段 - 生成总结"""
        try:
            # 汇总所有结果
            summary = {
                "goal": state.context.get("parsed_goal"),
                "plan": state.result.get("plan"),
                "execution": state.result.get("execution"),
                "verification": state.result.get("verification"),
            }

            state.result["summary"] = summary

            return PhaseResult(phase="completing", success=True, output=summary)
        except Exception as e:
            return PhaseResult(phase="completing", success=False, error=str(e))

    def _to_job_status(self, status: WorkflowStatus) -> str:
        """工作流状态 -> Job 状态"""
        mapping = {
            WorkflowStatus.PARSING: "running",
            WorkflowStatus.VALIDATING: "running",
            WorkflowStatus.PLANNING: "running",
            WorkflowStatus.EXECUTING: "running",
            WorkflowStatus.VERIFYING: "running",
            WorkflowStatus.COMPLETING: "running",
            WorkflowStatus.COMPLETED: "completed",
            WorkflowStatus.FAILED: "failed",
            WorkflowStatus.PAUSED: "input_required",
        }
        return mapping.get(status, "failed")

    def subscribe(
        self,
        callback: Callable[[WorkflowState], None],
    ) -> Callable[[], None]:
        """订阅状态变化"""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

    def _emit(self, state: WorkflowState) -> None:
        """通知订阅者"""
        for callback in self._subscribers:
            try:
                callback(state)
            except Exception:
                pass
