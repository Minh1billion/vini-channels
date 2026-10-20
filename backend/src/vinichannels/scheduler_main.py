import asyncio
import logging

from vinichannels.bootstrap.container import build_scheduler
from vinichannels.bootstrap.settings import Settings


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    scheduler = build_scheduler(Settings.from_env())
    asyncio.run(scheduler.run())


if __name__ == "__main__":
    main()
