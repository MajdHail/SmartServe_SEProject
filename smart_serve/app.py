from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3, datetime

app = Flask(__name__)
app.secret_key = "smartserve_secret"
DB = "smartserve.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'waiter'
            );
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'available',
                note TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL DEFAULT 'Main',
                available INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                waiter TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                sent_at TEXT,
                paid_at TEXT,
                total REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                qty INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS order_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                performed_by TEXT NOT NULL,
                detail TEXT,
                timestamp TEXT NOT NULL
            );

            INSERT OR IGNORE INTO users (username, password, role) VALUES
                ('waiter1','pass123','waiter'),
                ('waiter2','pass123','waiter'),
                ('chef','pass123','chef'),
                ('manager','pass123','manager');

            INSERT OR IGNORE INTO tables (id, status, note) VALUES
                (1,'available',''),(2,'available',''),(3,'available',''),
                (4,'available',''),(5,'available',''),(6,'available','');

            INSERT OR IGNORE INTO menu_items (name, price, category) VALUES
                ('Grilled Chicken',12.99,'Main'),
                ('Beef Burger',10.99,'Main'),
                ('Margherita Pizza',11.99,'Main'),
                ('Pasta Carbonara',13.99,'Main'),
                ('Fish & Chips',14.99,'Main'),
                ('Veggie Wrap',8.99,'Main'),
                ('Caesar Salad',7.99,'Starter'),
                ('Tomato Soup',5.99,'Starter'),
                ('Cheesecake',5.99,'Dessert'),
                ('Chocolate Brownie',4.99,'Dessert'),
                ('Soft Drink',2.99,'Drink'),
                ('Fresh Juice',3.99,'Drink'),
                ('Water',1.49,'Drink');
        """)

def recalc_total(db, order_id):
    t = db.execute(
        "SELECT SUM(price*qty) as t FROM order_items WHERE order_id=?", (order_id,)
    ).fetchone()["t"] or 0
    db.execute("UPDATE orders SET total=? WHERE id=?", (t, order_id))
    return t

def log_action(db, order_id, action, performed_by, detail=None):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO order_log (order_id, action, performed_by, detail, timestamp) VALUES (?,?,?,?,?)",
        (order_id, action, performed_by, detail, now)
    )

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()
        if user:
            session["user"] = username
            session["role"] = user["role"]
            if user["role"] == "chef":
                return redirect(url_for("chef_view"))
            if user["role"] == "manager":
                return redirect(url_for("manager_dashboard"))
            return redirect(url_for("floor_plan"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/floor")
@login_required
def floor_plan():
    with get_db() as db:
        tables = db.execute("SELECT * FROM tables ORDER BY id").fetchall()
        active_orders = db.execute(
            "SELECT table_id, created_at, sent_at, status FROM orders "
            "WHERE status IN ('pending','sent','preparing','ready')"
        ).fetchall()
    timers = {}
    for o in active_orders:
        if o["status"] in ("sent", "preparing") and o["sent_at"]:
            sent = datetime.datetime.strptime(o["sent_at"], "%Y-%m-%d %H:%M:%S")
            elapsed = int((datetime.datetime.now() - sent).total_seconds() / 60)
            timers[o["table_id"]] = elapsed
    return render_template("floor.html", tables=tables, timers=timers, user=session["user"])

@app.route("/table/<int:tid>/note", methods=["POST"])
@login_required
def set_table_note(tid):
    note = request.form.get("note", "")
    with get_db() as db:
        db.execute("UPDATE tables SET note=? WHERE id=?", (note, tid))
    return redirect(url_for("manage_order", tid=tid))


@app.route("/table/<int:tid>/order", methods=["GET", "POST"])
@login_required
def manage_order(tid):
    with get_db() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE table_id=? AND status IN ('pending','sent','preparing','ready')",
            (tid,)
        ).fetchone()

        if request.method == "POST":
            action = request.form.get("action")

            if action == "new_order":
                cur = db.execute(
                    "INSERT INTO orders (table_id, waiter, status, created_at) VALUES (?,?,?,?)",
                    (tid, session["user"], "pending", now())
                )
                db.execute("UPDATE tables SET status='occupied' WHERE id=?", (tid,))
                log_action(db, cur.lastrowid, "Order created", session["user"], f"Table {tid}")
                return redirect(url_for("manage_order", tid=tid))

            elif action == "add_item" and order:
                item_name = request.form["item_name"]
                qty = int(request.form.get("qty", 1))
                menu_item = db.execute("SELECT price FROM menu_items WHERE name=?", (item_name,)).fetchone()
                price = menu_item["price"] if menu_item else 0
                db.execute(
                    "INSERT INTO order_items (order_id, item_name, price, qty) VALUES (?,?,?,?)",
                    (order["id"], item_name, price, qty)
                )
                new_total = recalc_total(db, order["id"])
                log_action(db, order["id"], "Item added", session["user"],
                           f"{qty}x {item_name} — total ${new_total:.2f}")
                return redirect(url_for("manage_order", tid=tid))

            elif action == "remove_item":
                item_id = request.form["item_id"]
                order_id = int(request.form["order_id"])
                item = db.execute("SELECT * FROM order_items WHERE id=?", (item_id,)).fetchone()
                db.execute("DELETE FROM order_items WHERE id=?", (item_id,))
                new_total = recalc_total(db, order_id)
                if item:
                    log_action(db, order_id, "Item removed", session["user"],
                               f"{item['qty']}x {item['item_name']} — total ${new_total:.2f}")
                return redirect(url_for("manage_order", tid=tid))

            elif action == "send_to_kitchen" and order:
                db.execute("UPDATE orders SET status='sent', sent_at=? WHERE id=?", (now(), order["id"]))
                log_action(db, order["id"], "Sent to kitchen", session["user"])
                return redirect(url_for("floor_plan"))

            elif action == "recall_order" and order:
                db.execute("UPDATE orders SET status='pending', sent_at=NULL WHERE id=?", (order["id"],))
                log_action(db, order["id"], "Recalled for editing", session["user"])
                return redirect(url_for("manage_order", tid=tid))

            elif action == "cancel_order" and order:
                db.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order["id"],))
                db.execute("UPDATE tables SET status='available' WHERE id=?", (tid,))
                log_action(db, order["id"], "Order cancelled", session["user"])
                return redirect(url_for("floor_plan"))

        order = db.execute(
            "SELECT * FROM orders WHERE table_id=? AND status IN ('pending','sent','preparing','ready')",
            (tid,)
        ).fetchone()
        items = []
        if order:
            items = db.execute(
                "SELECT * FROM order_items WHERE order_id=?", (order["id"],)
            ).fetchall()
        table = db.execute("SELECT * FROM tables WHERE id=?", (tid,)).fetchone()
        menu_rows = db.execute(
            "SELECT * FROM menu_items WHERE available=1 ORDER BY category, name"
        ).fetchall()
        categories = {}
        for m in menu_rows:
            categories.setdefault(m["category"], []).append(m)

        kitchen_elapsed = None
        if order and order["status"] in ("sent", "preparing") and order["sent_at"]:
            sent = datetime.datetime.strptime(order["sent_at"], "%Y-%m-%d %H:%M:%S")
            kitchen_elapsed = int((datetime.datetime.now() - sent).total_seconds() / 60)

    return render_template("order.html", tid=tid, order=order, items=items,
                           categories=categories, table=table,
                           kitchen_elapsed=kitchen_elapsed, user=session["user"])


@app.route("/chef")
@login_required
def chef_view():
    if session.get("role") != "chef":
        return redirect(url_for("floor_plan"))
    with get_db() as db:
        orders = db.execute(
            "SELECT o.*, GROUP_CONCAT(oi.qty||'x '||oi.item_name, ', ') as items_str "
            "FROM orders o LEFT JOIN order_items oi ON oi.order_id=o.id "
            "WHERE o.status IN ('sent','preparing') "
            "GROUP BY o.id ORDER BY o.sent_at"
        ).fetchall()
    enriched = []
    for o in orders:
        elapsed = None
        if o["sent_at"]:
            sent = datetime.datetime.strptime(o["sent_at"], "%Y-%m-%d %H:%M:%S")
            elapsed = int((datetime.datetime.now() - sent).total_seconds() / 60)
        enriched.append({"order": o, "elapsed": elapsed})
    return render_template("chef.html", enriched=enriched, user=session["user"])

@app.route("/chef/order/<int:oid>/status", methods=["POST"])
@login_required
def update_order_status(oid):
    status = request.form["status"]
    if status not in ("preparing", "ready"):
        return redirect(url_for("chef_view"))
    with get_db() as db:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        if status == "ready":
            tid = db.execute("SELECT table_id FROM orders WHERE id=?", (oid,)).fetchone()["table_id"]
            db.execute("UPDATE tables SET status='ready' WHERE id=?", (tid,))
        log_action(db, oid, f"Status → {status}", session["user"])
    return redirect(url_for("chef_view"))


@app.route("/table/<int:tid>/bill", methods=["GET", "POST"])
@login_required
def bill(tid):
    with get_db() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE table_id=? AND status IN ('sent','preparing','ready')",
            (tid,)
        ).fetchone()
        if not order:
            return redirect(url_for("floor_plan"))
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id=?", (order["id"],)
        ).fetchall()
        if request.method == "POST":
            paid_at = now()
            db.execute("UPDATE orders SET status='paid', paid_at=? WHERE id=?",
                       (paid_at, order["id"]))
            db.execute("UPDATE tables SET status='available', note='' WHERE id=?", (tid,))
            log_action(db, order["id"], "Payment confirmed", session["user"],
                       f"Total ${order['total']*1.1:.2f}")
            return render_template("receipt.html", order=order, items=items,
                                   tid=tid, user=session["user"], paid_at=paid_at)
    return render_template("bill.html", order=order, items=items, tid=tid, user=session["user"])


@app.route("/manager")
@login_required
def manager_dashboard():
    if session.get("role") != "manager":
        return redirect(url_for("floor_plan"))
    with get_db() as db:
        stats = db.execute("""
            SELECT
                COUNT(*) as total_orders,
                SUM(CASE WHEN status='paid' THEN total*1.1 ELSE 0 END) as revenue,
                SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid
            FROM orders
        """).fetchone()
        daily = db.execute("""
            SELECT substr(paid_at,1,10) as day, SUM(total*1.1) as revenue, COUNT(*) as count
            FROM orders WHERE status='paid' AND paid_at IS NOT NULL
            GROUP BY day ORDER BY day DESC LIMIT 14
        """).fetchall()
        users = db.execute("SELECT * FROM users ORDER BY role, username").fetchall()
    return render_template("manager.html", stats=stats, daily=daily,
                           users=users, user=session["user"])

@app.route("/manager/orders")
@login_required
def manager_orders():
    if session.get("role") != "manager":
        return redirect(url_for("floor_plan"))
    filter_status = request.args.get("status", "all")
    date_from     = request.args.get("date_from", "")
    date_to       = request.args.get("date_to", "")
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    if filter_status != "all":
        query += " AND status=?"
        params.append(filter_status)
    if date_from:
        query += " AND created_at >= ?"
        params.append(date_from)
    if date_to:
        query += " AND created_at <= ?"
        params.append(date_to + " 23:59:59")
    query += " ORDER BY created_at DESC"
    with get_db() as db:
        orders = db.execute(query, params).fetchall()
        enriched = []
        for o in orders:
            oi = db.execute("SELECT * FROM order_items WHERE order_id=?", (o["id"],)).fetchall()
            logs = db.execute(
                "SELECT * FROM order_log WHERE order_id=? ORDER BY timestamp", (o["id"],)
            ).fetchall()
            enriched.append({"order": o, "order_items": oi, "logs": logs})
    return render_template("manager_orders.html", enriched=enriched,
                           filter_status=filter_status, date_from=date_from,
                           date_to=date_to, user=session["user"])

@app.route("/manager/menu", methods=["GET", "POST"])
@login_required
def manager_menu():
    if session.get("role") != "manager":
        return redirect(url_for("floor_plan"))
    with get_db() as db:
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add":
                name     = request.form["name"].strip()
                price    = float(request.form["price"])
                category = request.form["category"]
                db.execute(
                    "INSERT OR IGNORE INTO menu_items (name, price, category) VALUES (?,?,?)",
                    (name, price, category)
                )
            elif action == "toggle":
                item_id = request.form["item_id"]
                db.execute(
                    "UPDATE menu_items SET available = 1 - available WHERE id=?", (item_id,)
                )
            elif action == "delete":
                item_id = request.form["item_id"]
                db.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
            elif action == "edit_price":
                item_id = request.form["item_id"]
                price   = float(request.form["price"])
                db.execute("UPDATE menu_items SET price=? WHERE id=?", (price, item_id))
            return redirect(url_for("manager_menu"))
        items = db.execute("SELECT * FROM menu_items ORDER BY category, name").fetchall()
    categories = {}
    for m in items:
        categories.setdefault(m["category"], []).append(m)
    return render_template("manager_menu.html", categories=categories, user=session["user"])

@app.route("/manager/staff", methods=["GET", "POST"])
@login_required
def manager_staff():
    if session.get("role") != "manager":
        return redirect(url_for("floor_plan"))
    with get_db() as db:
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add":
                username = request.form["username"].strip()
                password = request.form["password"].strip()
                role     = request.form["role"]
                try:
                    db.execute(
                        "INSERT INTO users (username, password, role) VALUES (?,?,?)",
                        (username, password, role)
                    )
                except Exception:
                    pass
            elif action == "delete":
                user_id = request.form["user_id"]
                db.execute("DELETE FROM users WHERE id=? AND username != 'manager'", (user_id,))
            return redirect(url_for("manager_staff"))
        users = db.execute(
            "SELECT * FROM users ORDER BY role, username"
        ).fetchall()
    return render_template("manager_staff.html", users=users, user=session["user"])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
