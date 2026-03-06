from datetime import datetime
from flask import jsonify
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Create database and table
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
         CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        deadline TEXT,
        status TEXT DEFAULT 'Pending',
        priority TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def splash():
    return render_template("splash.html")
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    now = datetime.now()

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    # Auto update overdue
    for task in tasks:
        task_id = task[0]
        deadline = task[3]
        status = task[4]

        if deadline and status != "Done":
            deadline_time = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")

            if deadline_time < now:
                cursor.execute(
                    "UPDATE tasks SET status=? WHERE id=?",
                    ("Overdue", task_id)
                )

    conn.commit()

    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()

    total_tasks = len(tasks)
    pending_tasks = len([t for t in tasks if t[4] == "Pending"])
    done_tasks = len([t for t in tasks if t[4] == "Done"])
    overdue_tasks = len([t for t in tasks if t[4] == "Overdue"])

    conn.close()

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        done_tasks=done_tasks,
        overdue_tasks=overdue_tasks
    )
    

@app.route("/add", methods=["POST"])
def add_task():
    title = request.form["title"]
    description = request.form["description"]
    deadline = request.form["deadline"]

    priority = "Low"

    if deadline:
        deadline_time = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")
        now = datetime.now()
        difference = (deadline_time - now).total_seconds() / 3600  # hours

        if difference <= 24:
            priority = "High"
        elif difference <= 72:
            priority = "Medium"
        else:
            priority = "Low"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, description, deadline, priority) VALUES (?, ?, ?, ?)",
                   (title, description, deadline, priority))
    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/delete/<int:id>")
def delete_task(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")
@app.route("/complete/<int:id>")
def complete_task(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status='Done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

from datetime import datetime

@app.route("/update_date", methods=["POST"])
def update_date():
    data = request.get_json()

    task_id = data.get("id")
    new_date = data.get("new_date")

    print("Update route called:", task_id, new_date)

    # Convert string to datetime
    deadline_time = datetime.strptime(new_date, "%Y-%m-%dT%H:%M")
    now = datetime.now()

    diff_hours = (deadline_time - now).total_seconds() / 3600

    # Priority logic
    if diff_hours <= 24:
        priority = "High"
    elif diff_hours <= 72:
        priority = "Medium"
    else:
        priority = "Low"

    # Status auto change logic
    if deadline_time < now:
        status = "Overdue"
    else:
        status = "Pending"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE tasks SET deadline=?, priority=?, status=? WHERE id=?",
        (new_date, priority, status, task_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})
@app.route("/add-task")
def add_task_page():
    return render_template("add_task.html")


@app.route("/tasks")
def tasks_page():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()

    return render_template("tasks.html", tasks=tasks)


@app.route("/calendar")
def calendar_page():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()

    return render_template("calendar.html", tasks=tasks)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)