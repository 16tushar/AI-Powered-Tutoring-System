from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load the question dataset
questions_df = pd.read_csv("dataset.csv")
k12_df = pd.read_csv("k12.csv")  # Contains column 'IQ'

# Create SQLite table
with sqlite3.connect("database.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        subject TEXT,
        score INTEGER,
        total_questions INTEGER,
        recommendation TEXT,           
        iq_score INTEGER
    )
    """)
    conn.commit()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_test():
    name = request.form.get("name")
    subject = request.form.get("subject")

    if not name or not subject:
        return "Please enter all details.", 400

    session["name"] = name
    session["subject"] = subject

    return redirect(url_for("test"))


@app.route("/test", methods=["GET"])
def test():
    subject = session.get("subject", "")
    name = session.get("name", "")

    filtered = questions_df[questions_df["subject"].str.lower() == subject.lower()]
    selected = filtered.sample(n=min(5, len(filtered)))

    questions = selected.to_dict(orient="records")
    session["questions"] = questions

    return render_template("test.html", questions=questions)


def calculate_iq(user_score, total_questions):
    user_accuracy = user_score / total_questions
    avg_iq = k12_df["IQ"].mean()

    if user_accuracy >= 0.9:
        return int(avg_iq + 15)
    elif user_accuracy >= 0.7:
        return int(avg_iq)
    elif user_accuracy >= 0.5:
        return int(avg_iq - 10)
    else:
        return int(avg_iq - 20)

@app.route("/submit", methods=["POST"])
def submit():
    questions = session.get("questions", [])
    name = session.get("name", "Unknown")
    subject = session.get("subject", "Unknown")
    score = 0
    correct_answers = {}

    for q in questions:
        q_id = q["question"]
        user_answer = request.form.get(q_id, "").strip().lower()
        correct_answer = str(q["answer"]).strip().lower()

        correct_answers[q_id] = correct_answer
        if user_answer == correct_answer:
            score += 1

    total_questions = len(questions)
    iq_score = calculate_iq(score, total_questions)

    # Save to DB
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO results (name, subject, score, total_questions, iq_score)
            VALUES (?, ?, ?, ?, ?)
        """, (name, subject, score, total_questions, iq_score))
        conn.commit()

    # Store for session
    session["score"] = score
    session["total_questions"] = total_questions
    session["iq_score"] = iq_score
    session["correct_answers"] = correct_answers

    return redirect(url_for("results"))

@app.route("/results")
def results():
    name = session.get("name")
    subject = session.get("subject")
    score = session.get("score")
    total_questions = session.get("total_questions")
    iq_score = session.get("iq_score")
    correct_answers = session.get("correct_answers")

    # Get user's average score from past attempts
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT AVG(score) FROM results WHERE name=? AND subject=?", (name, subject))
        avg_score = cursor.fetchone()[0] or 0

    # 💡 Generate recommendation based on average score
    # Recommendation based on average performance
    if score == total_questions:
        recommendation = "Excellent! You got everything right!"
    elif avg_score >= 4:
        recommendation = "Try harder questions next time."
    elif avg_score >= 2:
        recommendation = "You're doing well, keep practicing."
    else:
        recommendation = "Focus on basics and improve gradually."


    # ✅ Insert full data with recommendation
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO results (name, subject, score, total_questions, iq_score, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, subject, score, total_questions, iq_score, recommendation))

        conn.commit()

    return render_template("results.html",
        iq_score=iq_score,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers,
        recommendation=recommendation
    )


@app.route("/history")
def history():
    name = session.get("name")
    if not name:
        return redirect(url_for("home"))

    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, total_questions, iq_score 
            FROM results 
            WHERE name=?
        """, (name,))
        past_attempts = cursor.fetchall()

    return render_template("history.html", past_attempts=past_attempts)

if __name__ == "__main__":
    app.run(debug=True)
