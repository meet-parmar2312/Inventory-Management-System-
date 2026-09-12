from decimal import Decimal
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import Category
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User
from app.models.warehouse import Warehouse
from app.utils.enums import UserRole

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_users(db: Session):
    admin = User(
        username="test_admin",
        email="admin@test.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    manager = User(
        username="test_manager",
        email="manager@test.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.MANAGER,
        is_active=True,
    )
    staff = User(
        username="test_staff",
        email="staff@test.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.STAFF,
        is_active=True,
    )
    inactive_user = User(
        username="inactive_user",
        email="inactive@test.com",
        password_hash=get_password_hash("Password123!"),
        role=UserRole.STAFF,
        is_active=False,
    )
    db.add_all([admin, manager, staff, inactive_user])
    db.commit()
    db.refresh(admin)
    db.refresh(manager)
    db.refresh(staff)
    return {"admin": admin, "manager": manager, "staff": staff, "inactive": inactive_user}


@pytest.fixture
def admin_headers(test_users):
    token = create_access_token(subject=test_users["admin"].id, role=UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(test_users):
    token = create_access_token(subject=test_users["manager"].id, role=UserRole.MANAGER.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def staff_headers(test_users):
    token = create_access_token(subject=test_users["staff"].id, role=UserRole.STAFF.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_data(db: Session):
    category = Category(name="Electronics", description="Gadgets and computers")
    supplier = Supplier(name="Apex Tech", email="sales@apex.com", phone="123456789")
    db.add_all([category, supplier])
    db.flush()

    warehouse_a = Warehouse(name="Warehouse A", location="Central", is_active=True)
    warehouse_b = Warehouse(name="Warehouse B", location="East", is_active=True)
    db.add_all([warehouse_a, warehouse_b])
    db.flush()

    product = Product(
        sku="SKU-PROD-001",
        name="Mechanical Keyboard",
        description="High-end tactile keyboard",
        category_id=category.id,
        supplier_id=supplier.id,
        unit_price=Decimal("100.00"),
        reorder_level=10,
        is_active=True,
    )
    db.add(product)
    db.flush()

    customer = Customer(
        name="John Doe",
        email="john@example.com",
        phone="555-0100",
        address="123 Elm St",
    )
    db.add(customer)
    db.flush()

    inventory_a = Inventory(
        product_id=product.id,
        warehouse_id=warehouse_a.id,
        quantity=50,
        reserved_quantity=0,
    )
    inventory_b = Inventory(
        product_id=product.id,
        warehouse_id=warehouse_b.id,
        quantity=20,
        reserved_quantity=0,
    )
    db.add_all([inventory_a, inventory_b])
    db.commit()

    return {
        "category": category,
        "supplier": supplier,
        "warehouse_a": warehouse_a,
        "warehouse_b": warehouse_b,
        "product": product,
        "customer": customer,
        "inventory_a": inventory_a,
        "inventory_b": inventory_b,
    }
