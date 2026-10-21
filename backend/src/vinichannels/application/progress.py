from collections.abc import Awaitable, Callable

Progress = Callable[[str, int, int | None], Awaitable[None]]
