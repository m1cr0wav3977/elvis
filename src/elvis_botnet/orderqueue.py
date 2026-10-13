
from collections import deque
from threading import Lock

from elvis_botnet.order import Order, OrderStatus


class OrderQueue:
    """Per-node FIFO for pending orders, retaining records after processing."""

    def __init__(self) -> None:
        self._pending: deque[Order] = deque()
        self._orders_by_id: dict[str, Order] = {}
        self._lock = Lock()

    def enqueue(self, order: Order) -> None:
        with self._lock:
            if order.order_id in self._orders_by_id:
                raise ValueError(f"Order {order.order_id} is already in this queue")
            self._orders_by_id[order.order_id] = order
            self._pending.append(order)

    def take_next(self) -> Order | None:
        with self._lock:
            if not self._pending:
                return None
            return self._pending.popleft()

    def take_pending_batch(self) -> list[Order]:
        with self._lock:
            orders = list(self._pending)
            self._pending.clear()
            for order in orders:
                order.mark_processing()
            return orders

    def mark_completed(self, order: Order) -> None:
        with self._lock:
            if self._orders_by_id.get(order.order_id) is not order:
                raise ValueError(f"Order {order.order_id} is not in this queue")
            order.mark_completed()

    def get(self, order_id: str) -> Order | None:
        with self._lock:
            return self._orders_by_id.get(order_id)

    def active_orders(self) -> list[Order]:
        with self._lock:
            return [
                order
                for order in self._orders_by_id.values()
                if order.status in {OrderStatus.PENDING, OrderStatus.PROCESSING}
            ]

    def __len__(self) -> int:
        with self._lock:
            return len(self._pending)