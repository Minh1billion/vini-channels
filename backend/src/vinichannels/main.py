from vinichannels.bootstrap.container import build_app
from vinichannels.bootstrap.settings import Settings

app = build_app(Settings.from_env())
