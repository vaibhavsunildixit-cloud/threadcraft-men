import os
import socket
from flask import Flask, render_template, request, session, redirect, url_for, jsonify

app = Flask(__name__)
# Same key on every pod so the cart session works across replicas
app.secret_key = os.getenv("SECRET_KEY", "threadcraft-demo-key")

PRODUCTS = [
    {"id": 1, "name": "Classic Oxford Shirt", "category": "Shirts", "price": 1799, "emoji": "👔"},
    {"id": 2, "name": "Linen Casual Shirt", "category": "Shirts", "price": 1499, "emoji": "👕"},
    {"id": 3, "name": "Slim Fit Chinos", "category": "Trousers", "price": 1999, "emoji": "👖"},
    {"id": 4, "name": "Stretch Denim Jeans", "category": "Trousers", "price": 2499, "emoji": "👖"},
    {"id": 5, "name": "Leather Derby Shoes", "category": "Footwear", "price": 3999, "emoji": "👞"},
    {"id": 6, "name": "White Sneakers", "category": "Footwear", "price": 2999, "emoji": "👟"},
    {"id": 7, "name": "Wool Blend Blazer", "category": "Outerwear", "price": 5999, "emoji": "🧥"},
    {"id": 8, "name": "Bomber Jacket", "category": "Outerwear", "price": 4499, "emoji": "🧥"},
    {"id": 9, "name": "Leather Belt", "category": "Accessories", "price": 899, "emoji": "🪢"},
    {"id": 10, "name": "Aviator Sunglasses", "category": "Accessories", "price": 1299, "emoji": "🕶️"},
    {"id": 11, "name": "Silk Tie", "category": "Accessories", "price": 799, "emoji": "👔"},
    {"id": 12, "name": "Analog Watch", "category": "Accessories", "price": 3499, "emoji": "⌚"},
]
BY_ID = {p["id"]: p for p in PRODUCTS}
CATEGORIES = ["Shirts", "Trousers", "Footwear", "Outerwear", "Accessories"]


@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {
        "cart_count": sum(cart.values()),
        "pod_name": socket.gethostname(),
        "categories": CATEGORIES,
    }


@app.route("/")
def home():
    cat = request.args.get("category")
    items = [p for p in PRODUCTS if not cat or p["category"] == cat]
    return render_template("index.html", products=items, active=cat)


@app.route("/add/<int:pid>", methods=["POST"])
def add(pid):
    if pid in BY_ID:
        cart = session.get("cart", {})
        cart[str(pid)] = cart.get(str(pid), 0) + 1
        session["cart"] = cart
    return redirect(request.referrer or url_for("home"))


@app.route("/remove/<int:pid>", methods=["POST"])
def remove(pid):
    cart = session.get("cart", {})
    cart.pop(str(pid), None)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart")
def cart():
    lines = []
    for pid, qty in session.get("cart", {}).items():
        p = BY_ID[int(pid)]
        lines.append({**p, "qty": qty, "subtotal": p["price"] * qty})
    total = sum(l["subtotal"] for l in lines)
    return render_template("cart.html", lines=lines, total=total)


@app.route("/checkout", methods=["POST"])
def checkout():
    session.pop("cart", None)
    return render_template("cart.html", lines=[], total=0, placed=True)


@app.route("/api/products")
def api_products():
    return jsonify(PRODUCTS)


@app.route("/health")
def health():
    return jsonify(status="healthy"), 200


@app.route("/aws-info")
def aws_info():
    return jsonify(
        pod_name=socket.gethostname(),
        aws_region=os.getenv("AWS_REGION", "ap-south-1"),
        image_source="Amazon ECR",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
