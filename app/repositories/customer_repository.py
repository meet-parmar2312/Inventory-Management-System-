from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.execute(select(Customer).where(Customer.id == customer_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.execute(select(Customer).where(func.lower(Customer.email) == email.strip().lower())).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20) -> List[Customer]:
        stmt = select(Customer).order_by(Customer.id.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count(Customer.id))).scalar() or 0

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.flush()
        return customer

    def update(self, customer: Customer) -> Customer:
        self.db.flush()
        return customer
