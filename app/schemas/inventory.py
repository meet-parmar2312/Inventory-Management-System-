from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StockAdjustRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., description="Quantity delta to adjust (positive to restock, negative to reduce)")
    reason: str = Field(default="Stock manual adjustment", min_length=2)


class StockTransferRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    source_warehouse_id: int = Field(..., gt=0)
    destination_warehouse_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, description="Positive quantity to transfer")


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockItem(BaseModel):
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    reorder_level: int


class InventorySummary(BaseModel):
    total_products: int
    total_stock_units: int
    total_reserved_units: int
    total_available_units: int
    low_stock_products_count: int
    total_warehouses: int
