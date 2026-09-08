from flask import Flask, flash, render_template, request, session, redirect, url_for, get_flashed_messages
import mysql.connector
from config import Config

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )

app.secret_key = "shopease-secret-key"


@app.route("/")
def home():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("home.html", products=products)


@app.route("/product/<int:id>")
def product(id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM products WHERE id = %s",
        (id,)
    )

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template("product.html", product=product)


@app.route("/add-to-cart/<int:id>")
def add_to_cart(id):

    cart = session.get("cart", [])

    cart.append(id)

    session["cart"] = cart

    return redirect(url_for("cart"))


@app.route("/cart")
def cart():

    cart = session.get("cart", [])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    cart_products = []

    for product in products:

        quantity = cart.count(product["id"])

        if quantity > 0:

            cart_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": product["price"] * quantity
            })

    total = sum(product["subtotal"] for product in cart_products)

    return render_template(
        "cart.html",
        cart_products=cart_products,
        total=total
    )

@app.route("/checkout")
def checkout():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", [])

    # If cart is empty
    if not cart:
        return redirect(url_for("cart"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    cart_products = []

    for product in products:

        quantity = cart.count(product["id"])

        if quantity > 0:

            cart_products.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "subtotal": product["price"] * quantity
            })

    total = sum(product["subtotal"] for product in cart_products)

    return render_template(
        "checkout.html",
        cart_products=cart_products,
        total=total
    )


@app.route("/place-order", methods=["post"])
def place_order():

    # Check if user is logged in
     if "user_id" not in session:
        return redirect(url_for("login"))

     user_id = session["user_id"]

    # Get customer details from checkout for

    # Get customer details from checkout form
     name = request.form["name"]
     email = request.form["email"]
     phone = request.form["phone"]
     address = request.form["address"]
     city = request.form["city"]
     state = request.form["state"]
     pincode = request.form["pincode"]

    # Get cart from session
     cart = session.get("cart", [])

    # If cart is empty, go back to cart
     if not cart:
        return redirect(url_for("cart"))

    # Connect to database
     conn = get_db_connection()
     cursor = conn.cursor()

    # Calculate total
     total = 0

     for product_id in cart:

        cursor.execute(
            "SELECT id, name, price FROM products WHERE id = %s",
            (product_id,)
        )

        product = cursor.fetchone()

        if product:
            total += product[2]

    # Insert order into orders table
     cursor.execute(
    """
    INSERT INTO orders
    (user_id, customer_name, email, phone, address, city, state, pincode, total)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """,
    (user_id, name, email, phone, address, city, state, pincode, total)
)

    # Get newly created order ID
     order_id = cursor.lastrowid

    # Find each different product in the cart
     product_ids = set(cart)

     for product_id in product_ids:

        quantity = cart.count(product_id)

        cursor.execute(
            "SELECT price FROM products WHERE id = %s",
            (product_id,)
        )

        product = cursor.fetchone()

        if product:
            price = product[0]
            subtotal = price * quantity

            cursor.execute(
                """
                INSERT INTO order_items
                (order_id, product_id, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, product_id, quantity, price, subtotal)
            )

    # Save everything to MySQL
     conn.commit()

     cursor.close()
     conn.close()

    # Empty the cart after successful order
     session["cart"] = []

    # Show order confirmation
     return render_template(
        "order_confirmation.html",
        order_id=order_id,
        total=total
    )

@app.route("/order/<int:order_id>")
def order_details(order_id):

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user_role = session.get("user_role")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get order
    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE id = %s
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    # Order does not exist
    if order is None:
        cursor.close()
        conn.close()
        return "Order not found", 404

    # Normal user can only see their own order
    # Admin can see any order
    if user_role != "admin" and order["user_id"] != user_id:
        cursor.close()
        conn.close()
        return "Access denied", 403

    # Get products in the order
    cursor.execute(
        """
        SELECT
            order_items.product_id,
            products.name,
            order_items.quantity,
            order_items.price,
            order_items.subtotal
        FROM order_items
        JOIN products
            ON order_items.product_id = products.id
        WHERE order_items.order_id = %s
        """,
        (order_id,)
    )

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "order_details.html",
        order=order,
        items=items
    )

@app.route("/my-orders")
def my_orders():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get only logged-in user's orders
    cursor.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )


 
@app.route("/register", methods=["GET", "POST"])
def register():

 if request.method == "POST":

    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if email already exists
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()

        return "Email already registered. Please login instead."

    # Create new user
    cursor.execute(
        """
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
        """,
        (name, email, password)
    )

    

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("login"))

 return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s AND password = %s
            """,
            (email, password)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        # User found
        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]

            # Admin user
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            # Normal user
            return redirect(url_for("profile"))

        # User not found
        return render_template(
            "login.html",
            error="Invalid email or password"
        )

    # GET request
    return render_template("login.html")
@app.route("/logout")
def logout():

 session.pop("user_id", None)
 session.pop("user_name", None)
 session.pop("user_email", None)

 return redirect(url_for("home"))

@app.route("/profile")
def profile():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user is None:
        return "User not found", 404

    return render_template(
        "profile.html",
        user=user
    )

@app.route("/edit-profile", methods=["GET", "POST"])
def edit_profile():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # When user submits the form
    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]

        # Update user in MySQL
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s
            WHERE id = %s
            """,
            (name, email, user_id)
        )

        conn.commit()

        # Update session values
        session["user_name"] = name
        session["user_email"] = email

        cursor.close()
        conn.close()

        # Go back to profile
        return redirect(url_for("profile"))

    # When user opens Edit Profile
    cursor.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user is None:
        return "User not found", 404

    return render_template(
        "edit_profile.html",
        user=user
    )

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            cursor.close()
            conn.close()

            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user or user["password"] != current_password:
            cursor.close()
            conn.close()

            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (new_password, user_id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Password changed successfully!", "success")

        return redirect(url_for("profile"))

    # GET request → show Change Password page
    cursor.close()
    conn.close()

    return render_template("change_password.html")

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("user_role") != "admin":
        return "Access denied", 403

    return render_template("admin.html")

@app.route("/admin/products")
def admin_products():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all products
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin-products.html",
        products=products
    )

@app.route("/admin/products/add", methods=["GET", "POST"])
def add_product():


    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("user_role") != "admin":
        return "Access denied", 403

    if request.method == "POST":

       name = request.form["name"]
       price = request.form["price"]
       image = request.form["image"]

       conn = get_db_connection()
       cursor = conn.cursor()

       cursor.execute(
        """
        INSERT INTO products (name, price, image)
        VALUES (%s, %s, %s)
        """,
        (name, price, image)
    )

       conn.commit()
       cursor.close()
       conn.close()

       return redirect(url_for("admin_products"))

    return render_template("add-product.html")

@app.route("/admin/products/delete/<int:id>", methods=["POST"])
def delete_product(id):

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id = %s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Product deleted successfully!", "success")

    return redirect(url_for("admin_products"))

@app.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Update product
    if request.method == "POST":

        name = request.form["name"]
        price = request.form["price"]
        image = request.form["image"]

        cursor.execute(
            """
            UPDATE products
            SET name = %s, price = %s, image = %s
            WHERE id = %s
            """,
            (name, price, image, id)
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Product updated successfully!", "success")

        return redirect(url_for("admin_products"))

    # Get existing product
    cursor.execute(
        "SELECT * FROM products WHERE id = %s",
        (id,)
    )

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product is None:
        return "Product not found", 404

    return render_template(
        "edit_prodcuts.html",
        product=product
    )
@app.route("/admin/categories")
def admin_categories():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM categories ORDER BY id DESC"
    )

    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin-categories.html",
        categories=categories
    )

@app.route("/admin/orders")
def admin_orders():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all orders
    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """)

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin-orders.html",
        orders=orders
    )


@app.route("/admin/orders/update-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check if user is admin
    if session.get("user_role") != "admin":
        return "Access denied", 403

    status = request.form["status"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = %s
        WHERE id = %s
        """,
        (status, order_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Order status updated successfully!", "success")

    return redirect(url_for("admin_orders"))
@app.route("/cancel-order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):

    # Check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Cancel only this user's Pending order
    cursor.execute(
        """
        UPDATE orders
        SET status = 'Cancelled'
        WHERE id = %s
        AND user_id = %s
        AND status = 'Pending'
        """,
        (order_id, user_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Order cancelled successfully!", "success")

    return redirect(url_for("my_orders"))

    







@app.route("/clear-cart")
def clear_cart():

    session.pop("cart", None)

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)