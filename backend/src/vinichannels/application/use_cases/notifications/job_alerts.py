from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.jobs.fetch_jobs import FetchJob, JobStatus
from vinichannels.application.use_cases.notifications.push import PushNotifier
from vinichannels.domain.notifications.entities import Notification, NotificationKind
from vinichannels.domain.shared.ids import ChannelId, new_id


class JobFinishedNotifier:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        clock: Clock,
        push: PushNotifier | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._push = push

    async def notify(self, job: FetchJob) -> None:
        if job.status is JobStatus.RUNNING:
            return
        succeeded = job.status is JobStatus.SUCCESS
        title = (
            f"Đã lấy dữ liệu: {job.label}" if succeeded else f"Lấy dữ liệu thất bại: {job.label}"
        )
        item = Notification(
            id=new_id(),
            kind=NotificationKind.JOB_SUCCEEDED if succeeded else NotificationKind.JOB_FAILED,
            channel_id=ChannelId(job.channel_id or ""),
            dedupe_key=f"job:{job.id}",
            title=title[:200],
            message=job.message or ("Hoàn tất" if succeeded else "Thất bại"),
            created_at=self._clock.now(),
        )
        async with self._uow_factory() as uow:
            if await uow.notifications.exists(item.dedupe_key):
                return
            await uow.notifications.add(item)
            await uow.commit()
        if self._push is not None:
            await self._push.notify([item])
