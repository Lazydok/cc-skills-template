"""Order processing module with intentional issues for testing."""

import json
from datetime import datetime


def process_order(order_data):
    """Process an incoming order and calculate totals."""
    items = order_data["items"]
    total = 0

    for item in items:
        price = item["price"]
        quantity = item["quantity"]
        discount = item.get("discount", 0)

        # Bug: discount applied incorrectly (subtracts percentage as flat amount)
        item_total = price * quantity - discount
        total += item_total

    # Bug: no check for negative total
    order_data["total"] = total
    order_data["processed_at"] = str(datetime.now())

    # Bug: tax calculation uses hardcoded rate, no rounding
    tax = total * 0.1
    order_data["tax"] = tax
    order_data["grand_total"] = total + tax

    return order_data


def validate_email(email):
    """Validate email format."""
    # Bug: overly simplistic validation
    if "@" in email and "." in email:
        return True
    return False


def get_user_orders(user_id, db_connection):
    """Fetch orders for a user."""
    # SQL injection vulnerability
    query = f"SELECT * FROM orders WHERE user_id = '{user_id}'"
    return db_connection.execute(query)


class OrderCache:
    """Simple in-memory cache for orders."""

    def __init__(self, max_size=100):
        self._cache = {}
        self.max_size = max_size

    def get(self, order_id):
        return self._cache.get(order_id)

    def set(self, order_id, order):
        # Bug: no eviction when cache is full
        self._cache[order_id] = order

    def clear(self):
        self._cache = {}
