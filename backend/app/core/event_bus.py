"""
Bus de eventos SSE en memoria.

LIMITACIÓN: el estado es por-proceso. En un deployment multi-worker, los
clientes conectados a distintos workers no reciben los eventos entre sí.
Para producción multi-worker, reemplazar por Redis pub/sub.
"""

import asyncio
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, conductor_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[conductor_id].add(q)
        return q

    def unsubscribe(self, conductor_id: int, q: asyncio.Queue) -> None:
        self._subscribers[conductor_id].discard(q)

    async def publish(self, conductor_id: int, event: dict) -> None:
        for q in list(self._subscribers[conductor_id]):
            await q.put(event)


event_bus = EventBus()
