# 1. PRODUCTS 

products = {
    "P001": {"name": "Laptop", "price": 1200, "stock": 10},
    "P002": {"name": "Mouse", "price": 25, "stock": 50},
    "P003": {"name": "Keyboard", "price": 75, "stock": 20},
    "P004": {"name": "Monitor", "price": 300, "stock": 15}
}

# 2. CUSTOMERS ORDERS 

orders = [
    {
        "order_id": "ORD001", "customer": "Ali",
        "items": [{"product_id": "P001", "quantity": 1}, {"product_id": "P002", "quantity": 2}],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD002", "customer": "Ahmed",
        "items": [{"product_id": "P003", "quantity": 2}, {"product_id": "P004", "quantity": 1}],
        "payment_status": "paid"
    },
    {
        "order_id": "ORD003", "customer": "Ali",
        "items": [{"product_id": "P002", "quantity": 5}],
        "payment_status": "pending"
    }
]

# Function to calculate the subtotal:
def get_bill(order, products):
    total = 0
    for item in order['items']:
        pro_id = item['product_id']
        qty = item['quantity']
        price = products[pro_id]['price']
        total += qty * price
    return total

# Function to calculate discount:
def get_discount(bill):
    if bill >= 1000:
        return bill * 0.15  # 15% discount
    elif bill >= 500:
        return bill * 0.10  # 10% discount
    elif bill >= 200:
        return bill * 0.05  # 5% discount
    else:
        return 0.0

# Function shipping cost:
def get_shipping(bill):
    if bill >= 500:
        return 0.0
    else:
        return 20.0

# Function to Check stock availability:
def order_is_valid(order, products):
    if len(order['items']) == 0:
        return False
    for item in order['items']:
        pro_id = item['product_id']
        qty = item['quantity']
        
# Reject if product doesn't exist:
    if pro_id not in products:
        return False
    if qty <= 0:
        return False
    if qty > products[pro_id]['stock']:
        return False
    return True

# Function to process order, deduct stock, and return summary
def process_order(order, products):
# Reject invalid orders immediately
    if not order_is_valid(order, products):
        return {"status": "rejected", "revenue": 0, "discount": 0, "shipping": 0}
        
    subtotal = get_bill(order, products)
    discount = get_discount(subtotal)
    shipping = get_shipping(subtotal)
    
# Process paid orders and update in stock:
    if order['payment_status'] == 'paid':
        for item in order['items']:
            pro_id = item["product_id"]
            qty = item["quantity"]
            products[pro_id]["stock"] -= qty
        
        final_paid = subtotal - discount + shipping
        return {
            "status": "paid",
            "revenue": final_paid,
            "discount": discount,
            "shipping": shipping
        }
    else:
# Return pending status without updating stock or revenue
        return {
            "status": "pending",
            "revenue": 0,
            "discount": 0,
            "shipping": 0
        }

paid_count = 0
pending_count = 0
rejected_count = 0

total_revenue = 0
total_discount = 0
total_shipping = 0

cust_spending = {}  # total spend per customer
pro_sales_qty = {}  # total units sold per product

# Process all orders one by one
for order in orders:
    result = process_order(order, products)
    
    if result["status"] == "paid":
        paid_count += 1
        total_revenue += result["revenue"]
        total_discount += result["discount"]
        total_shipping += result["shipping"]
        
# Track customer spending
        cust_name = order["customer"]
        if cust_name not in cust_spending:
            cust_spending[cust_name] = 0
        cust_spending[cust_name] += result["revenue"]
        
# Track product sales quantities
        for item in order["items"]:
            p_id = item["product_id"]
            qty = item["quantity"]
            if p_id not in pro_sales_qty:
                pro_sales_qty[p_id] = 0
            pro_sales_qty[p_id] += qty
            
    elif result["status"] == "pending":
        pending_count += 1
    else:
        rejected_count += 1

# 4. REPORT

# Find top spending customer
top_customer = "N/A"
max_spent = 0
for cust, spent in cust_spending.items():
    if spent > max_spent:
        max_spent = spent
        top_customer = cust

# Find most sold product by quantity
top_product = "N/A"
max_qty = 0
for p_id, qty in pro_sales_qty.items():
    if qty > max_qty:
        max_qty = qty
        top_product = products[p_id]["name"]

# Identify low stock items (Stock <= 10)
low_stock_list = []
for p_id in products:
    if products[p_id]["stock"] <= 10:
        low_stock_list.append(products[p_id]["name"])
        
# 5.SALES REPORT
print(f"""======= SALES REPORT =======
Total Orders: {len(orders)}
Paid Orders: {paid_count}
Pending Orders: {pending_count}
Rejected Orders: {rejected_count}
Total Revenue: ${total_revenue:.2f}
Total Discount: ${total_discount:.2f}
Total Shipping: ${total_shipping:.2f}
Top Customer: {top_customer}
Top Selling Product: {top_product}
Low Stock Products:""")
if len(low_stock_list) > 0:
    for prod_name in low_stock_list:
        print("=>", prod_name)
else:
    print("=> None")