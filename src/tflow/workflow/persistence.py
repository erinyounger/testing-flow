"""Workflow 会话持久化"""

from .state import WorkflowState, WorkflowPersistence

# 为了向后兼容，导出相同的类
__all__ = ["WorkflowState", "WorkflowPersistence"]
