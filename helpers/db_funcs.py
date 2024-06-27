import sqlite3


def init_db():
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS polls
                 (poll_id INTEGER PRIMARY KEY, question TEXT)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS options
                 (option_id INTEGER PRIMARY KEY, poll_id INTEGER, \
option TEXT, votes INTEGER)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS votes
                 (vote_id INTEGER PRIMARY KEY, poll_id INTEGER, \
user_id INTEGER, option_id INTEGER)"""
    )
    conn.commit()
    conn.close()


def add_poll(question: str, options: list[str]) -> int | None:
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute("INSERT INTO polls (question) VALUES (?)", (question,))
    poll_id = c.lastrowid
    for option in options:
        c.execute(
            "INSERT INTO options (poll_id, option, votes) VALUES (?, ?, 0)",
            (poll_id, option),
        )
    conn.commit()
    conn.close()
    return poll_id


def get_poll(poll_id: int):
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute("SELECT question FROM polls WHERE poll_id = ?", (poll_id,))
    question = c.fetchone()[0]
    c.execute(
        "SELECT option_id, option, votes FROM options WHERE poll_id = ?",
        (poll_id,),
    )
    options = c.fetchall()
    conn.close()
    return question, options


def record_vote(poll_id: int, user_id: int, option_id: int):
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute(
        "SELECT * FROM votes WHERE poll_id = ? AND user_id = ? AND \
option_id = ?",
        (poll_id, user_id, option_id),
    )
    if c.fetchone() is None:
        c.execute(
            "INSERT INTO votes (poll_id, user_id, option_id) VALUES (?, ?, ?)",
            (poll_id, user_id, option_id),
        )
        c.execute(
            "UPDATE options SET votes = votes + 1 WHERE option_id = ?",
            (option_id,),
        )
        conn.commit()
    conn.close()


def delete_poll(poll_id: int):
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute("DELETE FROM votes WHERE poll_id = ?", (poll_id,))
    c.execute("DELETE FROM options WHERE poll_id = ?", (poll_id,))
    c.execute("DELETE FROM polls WHERE poll_id = ?", (poll_id,))
    conn.commit()
    conn.close()


def get_user_votes(poll_id: int, user_id: int):
    conn = sqlite3.connect("polls.db")
    c = conn.cursor()
    c.execute(
        "SELECT option_id FROM votes WHERE poll_id = ? AND user_id = ?",
        (poll_id, user_id),
    )
    votes = c.fetchall()
    conn.close()
    return [vote[0] for vote in votes]
