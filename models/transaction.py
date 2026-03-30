from dataclasses import dataclass, field
from datetime import datetime
from .trade_order import TradeOrder
import uuid

@dataclass
class Transaction:
    id: str
    trade_order: TradeOrder
    timestamp: datetime
    status: str          # "FILLED" or "REJECTED"

    @staticmethod
    def create(trade_order: TradeOrder, status: str) -> "Transaction":
        return Transaction(
            id=str(uuid.uuid4())[:8],
            trade_order=trade_order,
            timestamp=datetime.now(),
            status=status,
        )
