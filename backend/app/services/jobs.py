"""
In-memory job registry for async extraction.

The extract endpoint used to run the whole pipeline synchronously inside
the request lifecycle, so the frontend had no way to show live progress
or let the user abort a long-running job. This module introduces a
lightweight, single-process job store:

  - POST /extract creates an ExtractionJob and returns immediately (202)
  - the pipeline runs as a background asyncio.Task
  - GET /extract/jobs/{id} returns progress/stage/result snapshots
  - POST /extract/jobs/{id}/cancel signals the running task to stop

Jobs live only in memory, so a server restart loses them - acceptable
for this deployment size; the proper fix (Celery/RQ + persistent store)
is tracked in weakness.md as a Hard item.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from loguru import logger


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = frozenset(
    {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
)


class JobCancelledError(Exception):
    """Internal signal raised by the runner when a job was cancelled mid-flight."""


@dataclass
class ExtractionJob:
    """Single extraction run tracked by the job registry."""

    job_id: str
    file_id: str
    ocr_engine: str
    output_format: str
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    stage: str = "Queued"
    error: str | None = None
    result: dict | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    task: asyncio.Task | None = field(default=None, repr=False)

    def update(self, progress: int, stage: str) -> None:
        """Non-terminal progress update - ignored once the job is done/cancelled."""
        if self.status in TERMINAL_STATUSES:
            return
        self.progress = max(0, min(100, int(progress)))
        self.stage = stage

    def cancel(self) -> None:
        """
        Signals cancellation. A QUEUED job transitions straight to
        CANCELLED (its task hasn't started); a PROCESSING job stays
        PROCESSING with stage "Cancelling…" until the runner hits its
        next checkpoint and finalises the state itself - so the snapshot
        always matches reality (the old text may still be running).
        """
        self.cancel_event.set()
        if self.status is JobStatus.QUEUED:
            self.status = JobStatus.CANCELLED
            self.stage = "Cancelled"
        elif self.status is JobStatus.PROCESSING:
            self.stage = "Cancelling…"

    def check_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def to_response(self) -> dict:
        return {
            "job_id": self.job_id,
            "file_id": self.file_id,
            "status": self.status.value,
            "progress": self.progress,
            "stage": self.stage,
            "created_at": self.created_at,
            "error": self.error,
            "result": self.result,
        }


class JobManager:
    """Registry of in-flight and recent ExtractionJobs (single process)."""

    _MAX_JOBS = 200

    def __init__(self) -> None:
        self._jobs: dict[str, ExtractionJob] = {}

    def create(
        self, file_id: str, ocr_engine: str, output_format: str
    ) -> ExtractionJob:
        self._prune()
        job = ExtractionJob(
            job_id=uuid.uuid4().hex,
            file_id=file_id,
            ocr_engine=ocr_engine,
            output_format=output_format,
        )
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> ExtractionJob | None:
        return self._jobs.get(job_id)

    def attach(self, job: ExtractionJob, task: asyncio.Task) -> None:
        """Keep a strong reference to the task so it isn't garbage-collected."""
        job.task = task
        self._jobs[job.job_id] = job

    def cancel(self, job_id: str) -> ExtractionJob | None:
        job = self.get(job_id)
        if job is not None:
            job.cancel()
        return job

    def _prune(self) -> None:
        """Evict oldest completed/failed/cancelled jobs once the cap is reached."""
        if len(self._jobs) < self._MAX_JOBS:
            return

        finished = [
            job for job in self._jobs.values() if job.status in TERMINAL_STATUSES
        ]
        evictable = sorted(finished, key=lambda job: job.created_at)
        for job in evictable:
            if len(self._jobs) < self._MAX_JOBS:
                break
            self._jobs.pop(job.job_id, None)

        if len(self._jobs) >= self._MAX_JOBS:
            logger.warning("Job registry at capacity; not evicting running jobs.")


# Single shared registry for the whole process.
job_manager = JobManager()