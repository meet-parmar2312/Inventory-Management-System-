from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    categories,
    customers,
    inventory,
    orders,
    products,
    suppliers,
    users,
    warehouses,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(suppliers.router)
api_router.include_router(warehouses.router)
api_router.include_router(inventory.router)
api_router.include_router(orders.router)
api_router.include_router(customers.router)
