from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.utils.enums import StockMovementType


class StockMovementResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    movement_type: StockMovementType
    quantity: int
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
