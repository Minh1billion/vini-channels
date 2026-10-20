from fastapi import APIRouter, Response

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.analytics import PeriodDep
from vinichannels.application.use_cases.reports.export import ReportKind

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/export")
async def export_report(
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
    kind: ReportKind = ReportKind.CHANNELS,
    partner_id: str | None = None,
) -> Response:
    report = await use_cases.export_report.execute(user, kind, period, partner_id)
    return Response(
        content=report.content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{report.filename}"'},
    )
