# E-Commerce Order Processing System

products = {
    "P001": {"name": "Laptop",   "price": 1200, "category": "Electronics", "stock": 10},
    "P002": {"name": "Mouse",    "price": 25,   "category": "Accessories",  "stock": 50},
    "P003": {"name": "Keyboard", "price": 75,   "category": "Accessories",  "stock": 20},
    "P004": {"name": "Monitor",  "price": 300,  "category": "Electronics",  "stock": 15},
}

orders = [
    {
        "order_id": "ORD001", "customer": "Ali",
        "items": [{"product_id": "P001", "quantity": 1}, {"product_id": "P002", "quantity": 2}],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD002", "customer": "Ahmed",
        "items": [{"product_id": "P003", "quantity": 2}, {"product_id": "P004", "quantity": 1}],
        "payment_status": "paid",
    },
    {
        "order_id": "ORD003", "customer": "Ali",
        "items": [{"product_id": "P002", "quantity": 5}],
        "payment_status": "pending",
    },
]

LOW_STOCK_THRESHOLD    = 5
VALID_PAYMENT_STATUSES = {"paid", "pending"}
DISCOUNT_TIERS         = [(1000, 0.15), (500, 0.10), (200, 0.05)]
SHIPPING_THRESHOLD     = 500
SHIPPING_FEE           = 20.0


def get_bill(order, products):
    total = 0
    for item in order.get("items", []):
        pid = item.get("product_id")
        if pid in products:
            total += products[pid]["price"] * item.get("quantity", 0)
    return total


def get_discount(subtotal):
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal >= threshold:
            return round(subtotal * rate, 2)
    return 0.0


def get_shipping(subtotal):
    return 0.0 if subtotal >= SHIPPING_THRESHOLD else SHIPPING_FEE


def order_is_valid(order, products):
    oid = order.get("order_id", "UNKNOWN")

    if not products:
        return False, f"[{oid}] Product catalogue is empty."

    items = order.get("items", [])
    if not items:
        return False, f"[{oid}] Order has no items."

    payment = order.get("payment_status", "")
    if payment not in VALID_PAYMENT_STATUSES:
        return False, f"[{oid}] Invalid payment status: '{payment}'."

    for item in items:
        pid = item.get("product_id")
        qty = item.get("quantity", 0)

        if pid not in products:
            return False, f"[{oid}] Unknown product ID: '{pid}'."

        if isinstance(qty, bool) or not isinstance(qty, (int, float)) or qty <= 0:
            return False, f"[{oid}] Quantity for '{pid}' must be a positive number (got {qty})."

        if qty > products[pid]["stock"]:
            return False, (f"[{oid}] Insufficient stock for '{products[pid]['name']}'. "
                           f"Requested: {qty}, Available: {products[pid]['stock']}.")

    return True, ""


def update_inventory(order, products):
    for item in order["items"]:
        pid = item.get("product_id")
        qty = item.get("quantity", 0)
        if pid in products and qty > 0:
            products[pid]["stock"] -= qty


def process_order(order, products, **options):
    apply_discount   = options.get("apply_discount",   True)
    include_shipping = options.get("include_shipping", True)

    oid      = order.get("order_id", "UNKNOWN")
    customer = order.get("customer", "Unknown")
    payment  = order.get("payment_status", "")

    is_valid, reason = order_is_valid(order, products)
    if not is_valid:
        print(f"  [REJECTED]  {oid} ({customer}): {reason}")
        return {"order_id": oid, "customer": customer, "status": "rejected",
                "subtotal": 0, "discount": 0, "shipping": 0, "total": 0,
                "items": order.get("items", [])}

    subtotal = get_bill(order, products)
    discount = get_discount(subtotal) if apply_discount   else 0.0
    shipping = get_shipping(subtotal) if include_shipping else 0.0
    total    = round(subtotal - discount + shipping, 2)

    if payment == "paid":
        update_inventory(order, products)
        status = "completed"
        print(f"  [COMPLETED] {oid} ({customer}) | Subtotal: ${subtotal:.2f}  "
              f"Discount: ${discount:.2f}  Shipping: ${shipping:.2f}  Total: ${total:.2f}")
    else:
        status = "pending"
        print(f"  [PENDING]   {oid} ({customer}) | Subtotal: ${subtotal:.2f}  Total: ${total:.2f}")

    return {"order_id": oid, "customer": customer, "status": status,
            "subtotal": subtotal, "discount": discount, "shipping": shipping,
            "total": total, "items": order["items"]}


def build_customer_totals(processed_orders):
    # only customers who have at least one completed order
    paying_customers = {o["customer"] for o in processed_orders if o["status"] == "completed"}
    totals = {}
    for cust in paying_customers:
        totals[cust] = sum(o["total"] for o in processed_orders
                           if o["customer"] == cust and o["status"] == "completed")
    return totals


def build_product_totals(processed_orders, products):
    sales = {pid: 0 for pid in products}
    for order in processed_orders:
        if order["status"] == "completed":
            for item in order["items"]:
                pid = item["product_id"]
                if pid in sales:
                    sales[pid] += item["quantity"]
    return sales


def find_top(data_dict, name_map=None):
    if not data_dict:
        return "N/A"

    max_val = max(data_dict.values())
    if max_val == 0:
        return "N/A"

    winners = [k for k, v in data_dict.items() if v == max_val]

    if name_map:
        winners = [name_map.get(k, k) for k in winners]

    if len(winners) == 1:
        return winners[0]
    return " & ".join(winners) + " (tied)"


def generate_sales_report(processed_orders, products):
    completed = [o for o in processed_orders if o["status"] == "completed"]
    pending   = [o for o in processed_orders if o["status"] == "pending"]
    rejected  = [o for o in processed_orders if o["status"] == "rejected"]

    total_revenue  = sum(o["total"]    for o in completed)
    total_discount = sum(o["discount"] for o in completed)
    total_shipping = sum(o["shipping"] for o in completed)

    top_customer = find_top(build_customer_totals(processed_orders))

    product_names = {pid: products[pid]["name"] for pid in products}
    top_product   = find_top(build_product_totals(processed_orders, products), name_map=product_names)

    low_stock = [(products[pid]["name"], products[pid]["stock"])
                 for pid in products if products[pid]["stock"] <= LOW_STOCK_THRESHOLD]
    low_stock.sort(key=lambda x: x[1])

    print()
    print("=" * 36)
    print("        SALES REPORT")
    print("=" * 36)
    print(f"""Total Orders:     {len(processed_orders)}
Paid Orders:      {len(completed)}
Pending Orders:   {len(pending)}
Rejected Orders:  {len(rejected)}
Total Revenue:    ${total_revenue:.2f}
Total Discount:   ${total_discount:.2f}
Total Shipping:   ${total_shipping:.2f}
Top Customer:     {top_customer}
Top Selling:      {top_product}
Low Stock Products:""")
    if low_stock:
        for name, stock in low_stock:
            print(f"  - {name} ({stock} left)")
    else:
        print("  - None")
    print("=" * 36)


def main():
    print("Processing Orders...")

    processed = []
    for order in orders:
        result = process_order(order, products)
        processed.append(result)

    generate_sales_report(processed, products)


if __name__ == "__main__":
    main()
