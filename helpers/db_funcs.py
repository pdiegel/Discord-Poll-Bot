import sqlite3
from constants import DATABASE


def init_db() -> None:
    conn = sqlite3.connect(DATABASE)
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
    c.execute(
        """CREATE TABLE IF NOT EXISTS poll_servers
                 (poll_id INTEGER PRIMARY KEY, server_id INTEGER)"""
    )
    conn.commit()
    conn.close()


def add_poll(
    question: str,
    options: list[str],
    server_id: int,
) -> int | None:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO polls (question) VALUES (?)", (question,))

    poll_id = c.lastrowid
    c.execute(
        "INSERT INTO poll_servers (poll_id, server_id) VALUES (?, ?)",
        (poll_id, server_id),
    )

    for option in options:
        c.execute(
            "INSERT INTO options (poll_id, option, votes) VALUES (?, ?, 0)",
            (poll_id, option),
        )
    conn.commit()
    conn.close()
    return poll_id


def get_poll(poll_id: int) -> tuple[str, list[tuple[int, str, int]]] | None:
    conn = sqlite3.connect(DATABASE)
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


def record_vote(
    poll_id: int,
    user_id: int,
    option_id: int,
    remove_if_exists: bool = False,
) -> None:
    """Record a vote for a user on a poll option.

    Args:
        poll_id (int): The ID of the poll.
        user_id (int): The ID of the user.
        option_id (int): The ID of the option.
        remove_if_exists (bool): If True, remove the user's vote if it exists.
    """
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM votes WHERE poll_id = ? AND user_id = ? AND \
option_id = ?",
        (poll_id, user_id, option_id),
    )

    user_has_voted = c.fetchone() is not None

    if user_has_voted and remove_if_exists:
        c.execute(
            "DELETE FROM votes WHERE poll_id = ? AND user_id = ? AND \
option_id = ?",
            (poll_id, user_id, option_id),
        )
        c.execute(
            "UPDATE options SET votes = votes - 1 WHERE option_id = ?",
            (option_id,),
        )
    elif not user_has_voted:
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


def delete_poll(poll_id: int, server_id: int) -> None:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # If the poll isn't in the server, do nothing
    c.execute(
        "SELECT * FROM poll_servers WHERE poll_id = ? AND server_id = ?",
        (poll_id, server_id),
    )
    if c.fetchone() is None:
        conn.close()
        raise ValueError(f"Poll ID {poll_id} not found in server")

    c.execute("DELETE FROM poll_servers WHERE poll_id = ?", (poll_id,))
    c.execute("DELETE FROM votes WHERE poll_id = ?", (poll_id,))
    c.execute("DELETE FROM options WHERE poll_id = ?", (poll_id,))
    c.execute("DELETE FROM polls WHERE poll_id = ?", (poll_id,))
    conn.commit()
    conn.close()


def get_user_votes(
    poll_id: int,
    user_id: int,
) -> list[int]:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        "SELECT option_id FROM votes WHERE poll_id = ? AND user_id = ?",
        (poll_id, user_id),
    )
    votes = c.fetchall()
    conn.close()
    return [vote[0] for vote in votes]


def load_poll_data(
    poll_id: int,
) -> tuple[int, list[dict[str, str | int]]] | None:
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
        SELECT poll_id, option, votes
        FROM optionS
        WHERE poll_id = $1
    """,
        (poll_id,),
    )
    poll_data = c.fetchall()
    conn.close()

    if poll_data:
        return parse_poll_data(poll_data)

    return None


def parse_poll_data(
    poll_data: list[tuple[int, str, int]]
) -> tuple[int, list[dict[str, str | int]]]:

    poll_id = poll_data[0][0]
    options: list[dict[str, str | int]] = []

    for poll in poll_data:
        option = poll[1]
        votes = poll[2]
        options.append(
            {
                "option": option,
                "votes": votes,
            }
        )
    return poll_id, options
