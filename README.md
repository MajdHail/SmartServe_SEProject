# Smart Serve System

A web-based restaurant management system built with Python (Flask) and SQLite. Designed for restaurant staff to manage table availability, customer orders, kitchen workflow, and billing — replacing paper-based ordering with a real-time digital system.

**Course:** CS342 Software Engineering
**Student:** Majd Yasin
**University:** German Jordanian University

---

## Features

- **Waiter** — view floor plan, manage table notes, create and send orders to the kitchen, recall and edit orders, generate bills and receipts
- **Chef** — receive incoming orders in real time, mark orders as preparing or ready, see elapsed kitchen timers
- **Manager** — full dashboard with revenue stats, daily sales chart, complete order log with activity history, menu management, and staff account management

---

## Project Structure

```
smart_serve/
├── app.py                     # All routes and business logic
├── requirements.txt           # Python dependencies
├── smartserve.db              # SQLite database (auto-created on first run)
├── static/
│   └── css/
│       └── style.css          # Full stylesheet
└── templates/
    ├── base.html              # Shared navbar layout
    ├── login.html             # Process 1 — Authentication
    ├── floor.html             # Process 2 — Table management
    ├── order.html             # Process 3 — Order management
    ├── chef.html              # Kitchen view
    ├── bill.html              # Process 4 — Billing
    ├── receipt.html           # Payment receipt
    ├── manager.html           # Manager dashboard
    ├── manager_orders.html    # Orders log with filters
    ├── manager_menu.html      # Menu management
    └── manager_staff.html     # Staff account management
```

---

## Requirements

- Python 3.8 or higher
- pip

---

## How to Run

### Step 1 — Download and unzip the project

Unzip `smart_serve_MajdYasin.zip` to any folder on your computer.

### Step 2 — Open a terminal inside the project folder

**On Mac:**
Right-click the `smart_serve` folder → Open Terminal at Folder

Or using Terminal:
```bash
cd path/to/smart_serve
```

**On Windows:**
Open the `smart_serve` folder in File Explorer, click the address bar, type `cmd`, and press Enter.

### Step 3 — Install Flask

```bash
pip3 install flask
```

> If `pip3` is not found, try `pip install flask`

### Step 4 — Run the app

```bash
python3 app.py
```

> If `python3` is not found, try `python app.py`

### Step 5 — Open in your browser

```
http://127.0.0.1:5000
```

The database file `smartserve.db` is created automatically on first run. No setup required.

### Step 6 — Stop the app

Press `Ctrl + C` in the terminal.

---

## Demo Accounts

| Role    | Username  | Password  |
|---------|-----------|-----------|
| Waiter  | waiter1   | pass123   |
| Chef    | chef1     | pass123   |
| Manager | manager   | pass123   |

---

## Demo Walkthrough

The following steps demonstrate all four DFD processes:

1. Log in as `waiter1` — demonstrates **Process 1: Authentication**
2. View the floor plan with 6 tables — demonstrates **Process 2: Table Management**
3. Click a table → add menu items → click **Send to Kitchen** — demonstrates **Process 3: Order Management**
4. Open a new browser tab and log in as `chef1`
5. See the order appear → click **Start Preparing** → click **Mark Ready**
6. Back in the waiter tab, the table turns blue (Ready)
7. Click **Bill** → confirm payment → view the printed receipt — demonstrates **Process 4: Billing**
8. Log out and log in as `manager` to view the full order log, revenue chart, and manage menu items and staff

---

## Database Tables

| Table         | Description                              |
|---------------|------------------------------------------|
| `users`       | Staff accounts with role-based access    |
| `tables`      | The 6 restaurant tables and their status |
| `menu_items`  | All available dishes with prices         |
| `orders`      | Every order and its lifecycle status     |
| `order_items` | Individual items within each order       |
| `order_log`   | Full audit trail of all order actions    |

---

## Technologies Used

| Technology | Purpose                        |
|------------|--------------------------------|
| Python 3   | Backend language               |
| Flask      | Web framework                  |
| SQLite     | Database (zero configuration)  |
| Jinja2     | HTML templating (built into Flask) |
| HTML / CSS | Frontend interface             |

---

## Troubleshooting

**`command not found: python`**
Use `python3` instead of `python`.

**`No module named flask`**
Your system has multiple Python versions. Install Flask for the correct one:
```bash
python3 -m pip install flask
```
Then run with the same version:
```bash
python3 app.py
```

**Port already in use**
Another process is using port 5000. Either stop that process or run Flask on a different port:
```bash
python3 app.py --port 5001
```
Then open `http://127.0.0.1:5001`

**Database errors after updating the code**
Delete `smartserve.db` and restart the app — it will be recreated fresh.
```bash
rm smartserve.db
python3 app.py
```
