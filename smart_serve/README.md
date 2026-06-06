# Smart Serve System
### CS342 Software Engineering — Majd Yasin

A restaurant management web app built with Python (Flask) + SQLite.

---

## How to Run

### Step 1 — Install Python
Make sure Python 3 is installed: https://www.python.org/downloads/

### Step 2 — Open a terminal in this folder
- On Mac: right-click the folder → "New Terminal at Folder"
- On Windows: open the folder, type `cmd` in the address bar

### Step 3 — Install Flask (one time only)
```
pip install flask
```

### Step 4 — Run the app
```
python app.py
```

### Step 5 — Open in browser
Go to: http://127.0.0.1:5000

---

## Demo Accounts

| Role   | Username | Password |
|--------|----------|----------|
| Waiter | waiter1  | pass123  |
| Chef   | chef1    | pass123  |

---

## How to Demo (for professor)

1. Log in as **waiter1**
2. Click a table → "New Order"
3. Select menu items and add them
4. Click "Send to Kitchen"
5. Open a **new browser tab**, log in as **chef1**
6. See the order appear — click "Start Preparing" then "Mark Ready"
7. Back in the waiter tab, the table turns blue ("Ready")
8. Click "Bill" → confirm payment → receipt prints

---

## Project Structure

```
smart_serve/
├── app.py              ← Main Flask app (all 4 DFD processes)
├── requirements.txt    ← Just: flask
├── smartserve.db       ← Auto-created on first run (SQLite)
├── static/css/
│   └── style.css
└── templates/
    ├── base.html
    ├── login.html      ← Process 1: Authentication
    ├── floor.html      ← Process 2: Table Management
    ├── order.html      ← Process 3: Order Management
    ├── chef.html       ← Chef kitchen view
    ├── bill.html       ← Process 4: Billing
    └── receipt.html    ← Receipt after payment
```
