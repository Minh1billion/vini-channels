from fastapi import APIRouter, Response

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/thumbnails/{video_id}")
async def get_thumbnail(video_id: str, user: CurrentUser, use_cases: UseCasesDep) -> Response:
    image = await use_cases.get_thumbnail.execute(user, video_id)
    return Response(
        content=image.content,
        media_type=image.content_type,
        headers={"Cache-Control": "private, max-age=604800"},
    )
