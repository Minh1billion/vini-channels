import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vinichannels.application.authorization import require
from vinichannels.application.errors import ApplicationError, Conflict
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.progress import Progress
from vinichannels.application.use_cases.channels.common import load_channel
from vinichannels.application.use_cases.channels.register import (
    RegisterChannel,
    RegisterChannelCommand,
)
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import DomainError
from vinichannels.domain.shared.ids import new_id
from vinichannels.domain.syncing.entities import SyncStatus

_log = logging.getLogger(__name__)


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(slots=True)
class FetchJob:
    id: str
    kind: str
    label: str
    started_at: datetime
    status: JobStatus = JobStatus.RUNNING
    stage: str = "Đang chuẩn bị"
    done: int = 0
    total: int | None = None
    message: str = ""
    channel_id: str | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class JobOutcome:
    status: JobStatus
    message: str
    channel_id: str | None = None


Work = Callable[[Progress], Awaitable[JobOutcome]]
FinishHook = Callable[[FetchJob], Awaitable[None]]


class FetchJobs:
    def __init__(self, clock: Clock, keep: int = 30, on_finish: FinishHook | None = None) -> None:
        self._clock = clock
        self._on_finish = on_finish
        self._keep = keep
        self._jobs: list[FetchJob] = []
        self._tasks: set[asyncio.Task[None]] = set()

    def list(self) -> list[FetchJob]:
        return list(reversed(self._jobs))

    def launch(self, kind: str, label: str, channel_id: str | None, work: Work) -> FetchJob:
        if any(
            job.status is JobStatus.RUNNING and job.kind == kind and job.label == label
            for job in self._jobs
        ):
            raise Conflict(f"{label} đang được lấy dữ liệu")
        job = FetchJob(new_id(), kind, label, self._clock.now(), channel_id=channel_id)
        self._jobs.append(job)
        self._jobs = self._jobs[-self._keep :]
        task = asyncio.create_task(self._run(job, work))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    def _reporter(self, job: FetchJob) -> Progress:
        async def report(stage: str, done: int, total: int | None) -> None:
            job.stage = stage
            job.done = done
            job.total = total

        return report

    async def _run(self, job: FetchJob, work: Work) -> None:
        try:
            outcome = await work(self._reporter(job))
        except (ApplicationError, DomainError) as error:
            self._end(job, JobOutcome(JobStatus.FAILED, error.message))
        except Exception:
            _log.exception("Tác vụ lấy dữ liệu %s gặp lỗi", job.label)
            self._end(job, JobOutcome(JobStatus.FAILED, "Lỗi không xác định"))
        else:
            self._end(job, outcome)
        await self._announce(job)

    async def _announce(self, job: FetchJob) -> None:
        if self._on_finish is None:
            return
        try:
            await self._on_finish(job)
        except Exception:
            _log.exception("Tạo thông báo cho tác vụ %s thất bại", job.label)

    def _end(self, job: FetchJob, outcome: JobOutcome) -> None:
        job.status = outcome.status
        job.message = outcome.message
        job.channel_id = outcome.channel_id or job.channel_id
        job.finished_at = self._clock.now()
        job.stage = "Hoàn tất" if outcome.status is JobStatus.SUCCESS else "Thất bại"


class StartRegisterChannel:
    def __init__(self, jobs: FetchJobs, register: RegisterChannel) -> None:
        self._jobs = jobs
        self._register = register

    async def execute(self, actor: User, command: RegisterChannelCommand) -> FetchJob:
        require(actor, Permission.PARTNERS_WRITE)
        require(actor, Permission.SYNC_WRITE)
        handle = Handle(command.handle)

        async def work(progress: Progress) -> JobOutcome:
            channel = await self._register.execute(actor, command, progress)
            return JobOutcome(JobStatus.SUCCESS, "Đã thêm kênh và lấy dữ liệu", channel.id)

        return self._jobs.launch("register", handle.display, None, work)


class StartSyncChannel:
    def __init__(self, jobs: FetchJobs, sync: SyncChannel, uow_factory: UnitOfWorkFactory) -> None:
        self._jobs = jobs
        self._sync = sync
        self._uow_factory = uow_factory

    async def execute(self, actor: User, channel_id: str) -> FetchJob:
        require(actor, Permission.SYNC_WRITE)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
        label = channel.handle.display

        async def work(progress: Progress) -> JobOutcome:
            run = await self._sync.execute(actor, channel_id, progress=progress)
            if run.status is SyncStatus.FAILED:
                return JobOutcome(JobStatus.FAILED, run.error_message or "Đồng bộ thất bại")
            detail = f"{run.items_fetched} video"
            if run.error_message:
                detail = f"{detail} ({run.error_message})"
            return JobOutcome(JobStatus.SUCCESS, detail)

        return self._jobs.launch("sync", label, channel_id, work)


class ListFetchJobs:
    def __init__(self, jobs: FetchJobs) -> None:
        self._jobs = jobs

    async def execute(self, actor: User) -> list[FetchJob]:
        require(actor, Permission.ANALYTICS_READ)
        return self._jobs.list()
