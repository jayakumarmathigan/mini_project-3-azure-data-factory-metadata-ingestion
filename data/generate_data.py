"""Generate synthetic CSV source files. Usage: python data/generate_data.py"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(11)
OUT = Path(__file__).parent / "sample"


def write(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name}: {len(rows)} rows")


write("customers.csv", [{"customer_id": f"C{i:03d}", "customer_name": f"Customer {i}",
                         "city": random.choice(["Bengaluru", "Hyderabad", "Chennai", "Pune"])}
                        for i in range(1, 51)])
write("products.csv", [{"product_id": f"P{i:03d}", "product_name": f"Product {i}",
                        "unit_price": random.randint(100, 5000)} for i in range(1, 21)])
write("orders.csv", [{"order_id": f"O{i:05d}", "customer_id": f"C{random.randint(1, 50):03d}",
                      "product_id": f"P{random.randint(1, 20):03d}",
                      "quantity": random.randint(1, 5),
                      "order_date": str(date(2026, 10, 1) + timedelta(random.randrange(30)))}
                     for i in range(1, 501)])
