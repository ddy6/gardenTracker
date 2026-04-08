import asgi
from workers import WorkerEntrypoint

from app import create_app


class Default(WorkerEntrypoint):
    def __init__(self):
        super().__init__()
        self._app = None

    async def fetch(self, request):
        if self._app is None:
            self._app = create_app()
        return await asgi.fetch(self._app, request, self.env)
