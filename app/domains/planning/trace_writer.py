"""
trace_writer.py — 决策链 trace 写入工具

将城市圈决策链路每一步的 trace 写入 generation_runs / generation_step_runs，
复用现有 trace 表结构，不新建表。
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.trace import GenerationRun, GenerationStepRun

logger = logging.getLogger(__name__)


class CircleTraceWriter:
    """
    城市圈决策链路的 trace 写入器。

    用法：
        writer = CircleTraceWriter(session, plan_id)
        await writer.start_run(profile_snapshot={...})

        with writer.step("circle_selection") as s:
            result = await select_city_circle(...)
            s.set_output({"selected": result.selected_circle_id})
            s.set_trace(result.trace)

        await writer.finish_run()
    """

    def __init__(self, session: AsyncSession, plan_id: uuid.UUID):
        self._session = session
        self._plan_id = plan_id
        self._run: Optional[GenerationRun] = None
        self._step_order = 0

    async def start_run(
        self,
        profile_snapshot: Optional[dict] = None,
        mode: str = "full",
    ) -> uuid.UUID:
        """创建一条 generation_run 记录。"""
        self._run = GenerationRun(
            plan_id=self._plan_id,
            mode=mode,
            status="running",
            triggered_by="system",
            profile_snapshot=profile_snapshot,
            generation_mode="circle_pipeline",
        )
        self._session.add(self._run)
        await self._session.flush()  # 拿到 run_id
        logger.debug("trace_writer: run started run_id=%s plan=%s", self._run.run_id, self._plan_id)
        return self._run.run_id

    def step(self, step_name: str) -> _StepContext:
        """返回一个 step 上下文管理器。"""
        self._step_order += 1
        return _StepContext(
            session=self._session,
            run=self._run,
            step_name=step_name,
            step_order=self._step_order,
        )

    async def finish_run(
        self,
        status: str = "completed",
        quality_gate_passed: Optional[bool] = None,
    ) -> None:
        """标记 run 完成。"""
        if self._run:
            self._run.status = status
            self._run.total_steps = self._step_order
            self._run.quality_gate_passed = quality_gate_passed
            self._run.finished_at = datetime.now(tz=timezone.utc)
            await self._session.flush()


class _StepContext:
    """单步 trace 上下文管理器，支持 async with。"""

    def __init__(
        self,
        session: AsyncSession,
        run: GenerationRun,
        step_name: str,
        step_order: int,
    ):
        self._session = session
        self._run = run
        self._step_name = step_name
        self._step_order = step_order
        self._step_run: Optional[GenerationStepRun] = None
        self._start_time: float = 0
        self._output: Optional[dict] = None
        self._warnings: list[str] = []
        self._errors: list[str] = []

    def set_output(self, output: dict) -> None:
        self._output = output

    def set_trace(self, trace: list[str]) -> None:
        """把模块返回的 trace list 存为 warnings（复用现有字段）。"""
        self._warnings = trace

    def add_error(self, error: str) -> None:
        self._errors.append(error)

    async def __aenter__(self) -> "_StepContext":
        self._start_time = time.monotonic()
        self._step_run = GenerationStepRun(
            run_id=self._run.run_id,
            step_name=self._step_name,
            step_order=self._step_order,
            status="running",
        )
        self._session.add(self._step_run)
        await self._session.flush()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        elapsed_ms = int((time.monotonic() - self._start_time) * 1000)
        step = self._step_run

        if exc_type is not None:
            step.status = "failed"
            self._errors.append(f"{exc_type.__name__}: {exc_val}")
        else:
            step.status = "completed"

        step.output_summary = self._output
        step.warnings = self._warnings if self._warnings else None
        step.errors = self._errors if self._errors else None
        step.latency_ms = elapsed_ms
        step.finished_at = datetime.now(tz=timezone.utc)

        await self._session.flush()
        logger.debug(
            "trace_writer: step %s %s (%dms)",
            self._step_name, step.status, elapsed_ms,
        )
        # 不吞异常
        return False
