import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import NotRequired, TypeAlias, TypedDict


JSONValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | list["JSONValue"]
    | dict[str, "JSONValue"]
)


class ExecutePayload(TypedDict):
    command: str
    arguments: NotRequired[list[str]]


class HttpRequestPayload(TypedDict):
    method: str
    url: str
    headers: NotRequired[dict[str, str]]
    body: NotRequired[JSONValue]


class OrderType(str, Enum):
    EXECUTE = "execute"
    HTTP_REQUEST = "http_request"


OrderPayload: TypeAlias = ExecutePayload | HttpRequestPayload


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"


@dataclass(slots=True)
class Order:
    """A typed, dry-run order received by ``POST /orders``.

    Request JSON uses a common envelope and one of two kind-specific payloads:

    System command (descriptive only; never executed)::

        {
            "origin_node_id": "manager-1",
            "kind": "execute",
            "payload": {
                "command": "echo",
                "arguments": ["hello"]
            }
        }

    HTTP request (descriptive only; never sent)::

        {
            "origin_node_id": "manager-1",
            "kind": "http_request",
            "payload": {
                "method": "GET",
                "url": "https://example.invalid/health",
                "headers": {"Accept": "application/json"}
            }
        }

    ``order_id`` may be supplied at the top level; when omitted, one is
    generated. ``created_at`` and ``status`` are managed by the receiving node,
    not supplied in the request. The endpoint also requires a bearer token.
    """

    origin_node_id: str
    kind: OrderType
    payload: OrderPayload
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: OrderStatus = OrderStatus.PENDING

    def mark_processing(self) -> None:
        if self.status is not OrderStatus.PENDING:
            raise ValueError(f"Cannot process an order with status {self.status.value}")
        self.status = OrderStatus.PROCESSING

    def mark_completed(self) -> None:
        if self.status is not OrderStatus.PROCESSING:
            raise ValueError(f"Cannot complete an order with status {self.status.value}")
        self.status = OrderStatus.COMPLETED
