import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.stock_movement import StockMovement
from app.models.customer import Customer
from app.utils.enums import UserRole, StockMovementType


def seed():
    db = SessionLocal()
    try:
        print("🌱 Starting database seeding...")

        users_data = [
            {
                "username": "admin",
                "email": "admin@inventory.io",
                "password": "AdminPassword123!",
                "role": UserRole.ADMIN,
            },
            {
                "username": "manager",
                "email": "manager@inventory.io",
                "password": "ManagerPassword123!",
                "role": UserRole.MANAGER,
            },
            {
                "username": "staff",
                "email": "staff@inventory.io",
                "password": "StaffPassword123!",
                "role": UserRole.STAFF,
            },
        ]

        created_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    password_hash=get_password_hash(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
                db.flush()
                created_users[u["username"]] = user
                print(f"  ✓ Created user: {u['username']} ({u['role'].value})")
            else:
                created_users[u["username"]] = existing
                print(f"  • User exists: {u['username']}")

        admin_id = created_users["admin"].id

        categories_data = [
            {"name": "Electronics", "description": "Electronic equipment, gadgets, and components"},
            {"name": "Computer Peripherals", "description": "Keyboards, mice, webcams, and monitors"},
            {"name": "Office Furniture", "description": "Desks, ergonomic chairs, and office organizers"},
            {"name": "Cables & Adapters", "description": "High-speed HDMI, USB-C, and Ethernet cabling"},
        ]
        created_categories = {}
        for c in categories_data:
            existing = db.query(Category).filter(Category.name == c["name"]).first()
            if not existing:
                cat = Category(name=c["name"], description=c["description"])
                db.add(cat)
                db.flush()
                created_categories[c["name"]] = cat
                print(f"  ✓ Created category: {c['name']}")
            else:
                created_categories[c["name"]] = existing

        suppliers_data = [
            {
                "name": "Apex Tech Distribution",
                "contact_name": "Sarah Connor",
                "email": "sarah@apextech.com",
                "phone": "+1-555-0199",
                "address": "100 Innovation Way, San Jose, CA",
            },
            {
                "name": "Global Office Solutions",
                "contact_name": "Michael Scott",
                "email": "m.scott@globaloffice.com",
                "phone": "+1-555-0144",
                "address": "1725 Slough Ave, Scranton, PA",
            },
            {
                "name": "Silicon Wholesale Ltd",
                "contact_name": "Linus Torvalds",
                "email": "orders@siliconwholesale.com",
                "phone": "+1-555-0188",
                "address": "450 Technology Blvd, Austin, TX",
            },
        ]
        created_suppliers = {}
        for s in suppliers_data:
            existing = db.query(Supplier).filter(Supplier.name == s["name"]).first()
            if not existing:
                sup = Supplier(**s)
                db.add(sup)
                db.flush()
                created_suppliers[s["name"]] = sup
                print(f"  ✓ Created supplier: {s['name']}")
            else:
                created_suppliers[s["name"]] = existing

        warehouses_data = [
            {"name": "Warehouse A - Central Distribution", "location": "Dallas, TX", "is_active": True},
            {"name": "Warehouse B - West Coast Hub", "location": "Reno, NV", "is_active": True},
            {"name": "Warehouse C - East Coast Express", "location": "Allentown, PA", "is_active": True},
        ]
        created_warehouses = {}
        for w in warehouses_data:
            existing = db.query(Warehouse).filter(Warehouse.name == w["name"]).first()
            if not existing:
                wh = Warehouse(**w)
                db.add(wh)
                db.flush()
                created_warehouses[w["name"]] = wh
                print(f"  ✓ Created warehouse: {w['name']}")
            else:
                created_warehouses[w["name"]] = existing

        wh_a = created_warehouses["Warehouse A - Central Distribution"]
        wh_b = created_warehouses["Warehouse B - West Coast Hub"]
        wh_c = created_warehouses["Warehouse C - East Coast Express"]

        products_data = [
            {
                "sku": "KB-MECH-RGB",
                "name": "Mechanical Gaming Keyboard RGB",
                "description": "Tactile mechanical switches with per-key customizable RGB lighting",
                "category": "Computer Peripherals",
                "supplier": "Apex Tech Distribution",
                "unit_price": Decimal("89.99"),
                "reorder_level": 15,
            },
            {
                "sku": "MS-WIRELESS-PRO",
                "name": "Ergonomic Wireless Mouse",
                "description": "Dual-mode Bluetooth and 2.4GHz rechargeable wireless mouse",
                "category": "Computer Peripherals",
                "supplier": "Apex Tech Distribution",
                "unit_price": Decimal("49.50"),
                "reorder_level": 20,
            },
            {
                "sku": "MON-4K-27",
                "name": "27-inch 4K UHD IPS Monitor",
                "description": "Professional color-accurate monitor with 99% sRGB and USB-C PD",
                "category": "Electronics",
                "supplier": "Silicon Wholesale Ltd",
                "unit_price": Decimal("349.00"),
                "reorder_level": 10,
            },
            {
                "sku": "DK-STAND-ELEC",
                "name": "Motorized Standing Desk 60x30",
                "description": "Dual-motor electric height-adjustable desk with memory presets",
                "category": "Office Furniture",
                "supplier": "Global Office Solutions",
                "unit_price": Decimal("429.99"),
                "reorder_level": 8,
            },
            {
                "sku": "CH-ERGO-MESH",
                "name": "High-Back Ergonomic Mesh Chair",
                "description": "Breathable mesh back with adjustable lumbar support and 3D armrests",
                "category": "Office Furniture",
                "supplier": "Global Office Solutions",
                "unit_price": Decimal("220.00"),
                "reorder_level": 12,
            },
            {
                "sku": "CBL-USBC-TB4",
                "name": "Thunderbolt 4 USB-C Cable (2M)",
                "description": "40Gbps 100W Power Delivery certified braided cable",
                "category": "Cables & Adapters",
                "supplier": "Silicon Wholesale Ltd",
                "unit_price": Decimal("24.99"),
                "reorder_level": 30,
            },
        ]

        created_products = {}
        for p in products_data:
            existing = db.query(Product).filter(Product.sku == p["sku"]).first()
            if not existing:
                prod = Product(
                    sku=p["sku"],
                    name=p["name"],
                    description=p["description"],
                    category_id=created_categories[p["category"]].id,
                    supplier_id=created_suppliers[p["supplier"]].id,
                    unit_price=p["unit_price"],
                    reorder_level=p["reorder_level"],
                    is_active=True,
                )
                db.add(prod)
                db.flush()
                created_products[p["sku"]] = prod
                print(f"  ✓ Created product: {p['name']} (SKU: {p['sku']})")
            else:
                created_products[p["sku"]] = existing

        initial_stocks = [
            (created_products["KB-MECH-RGB"].id, wh_a.id, 100),
            (created_products["KB-MECH-RGB"].id, wh_b.id, 45),
            (created_products["KB-MECH-RGB"].id, wh_c.id, 8),
            (created_products["MS-WIRELESS-PRO"].id, wh_a.id, 80),
            (created_products["MS-WIRELESS-PRO"].id, wh_b.id, 12),
            (created_products["MON-4K-27"].id, wh_a.id, 30),
            (created_products["MON-4K-27"].id, wh_b.id, 5),
            (created_products["DK-STAND-ELEC"].id, wh_a.id, 25),
            (created_products["CH-ERGO-MESH"].id, wh_a.id, 40),
            (created_products["CBL-USBC-TB4"].id, wh_a.id, 200),
            (created_products["CBL-USBC-TB4"].id, wh_b.id, 15),
        ]

        for prod_id, wh_id, qty in initial_stocks:
            inv = db.query(Inventory).filter(
                Inventory.product_id == prod_id,
                Inventory.warehouse_id == wh_id,
            ).first()
            if not inv:
                inv = Inventory(
                    product_id=prod_id,
                    warehouse_id=wh_id,
                    quantity=qty,
                    reserved_quantity=0,
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(inv)
                sm = StockMovement(
                    product_id=prod_id,
                    warehouse_id=wh_id,
                    movement_type=StockMovementType.PURCHASE,
                    quantity=qty,
                    reference_id="INITIAL_SEED",
                    reason="Initial warehouse stock seed",
                    created_by=admin_id,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(sm)
        db.flush()
        print("  ✓ Seeded inventory levels and initial purchase audit movements")

        customers_data = [
            {
                "name": "Acme Logistics Corp",
                "email": "purchasing@acme.com",
                "phone": "+1-800-555-0101",
                "address": "742 Evergreen Terrace, Springfield, OR",
            },
            {
                "name": "Initech Innovations",
                "email": "peter.gibbons@initech.com",
                "phone": "+1-800-555-0102",
                "address": "4120 Freidrich Ln, Austin, TX",
            },
            {
                "name": "Wayne Enterprises Tech",
                "email": "bruce@wayne-enterprises.com",
                "phone": "+1-800-555-0103",
                "address": "1007 Mountain Drive, Gotham City, NJ",
            },
        ]

        for c in customers_data:
            existing = db.query(Customer).filter(Customer.email == c["email"]).first()
            if not existing:
                cust = Customer(**c)
                db.add(cust)
                print(f"  ✓ Created customer: {c['name']}")

        db.commit()
        print("✅ Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
