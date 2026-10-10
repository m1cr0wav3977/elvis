
from collections import deque

from elvis_botnet.order import Order


class OrderQueue:
    """Per-node FIFO for pending orders, retaining records after processing."""

    def __init__(self) -> None:
        self._pending: deque[Order] = deque()
        self._orders_by_id: dict[str, Order] = {}

    def enqueue(self, order: Order) -> None:
        if order.order_id in self._orders_by_id:
            raise ValueError(f"Order {order.order_id} is already in this queue")
        self._orders_by_id[order.order_id] = order
        self._pending.append(order)

    def take_next(self) -> Order | None:
        if not self._pending:
            return None
        return self._pending.popleft()

    def get(self, order_id: str) -> Order | None:
        return self._orders_by_id.get(order_id)

    def __len__(self) -> int:
        return len(self._pending)