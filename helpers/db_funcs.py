import asyncpg  # type: ignore
from asyncpg import Record  # type: ignore
from constants import DATABASE_URL
from typing import Any, List, Tuple, Dict, Optional


async def connect_db() -> asyncpg.Connection:
    return await asyncpg.connect(DATABASE_URL)  # type: ignore


async def query_db(
    query: str,
    args: Tuple[Any] | Tuple[()] = (),
    one: bool = False,
    commit: bool = True,
    fetch: bool = True,
) -> Any:
    conn = await connect_db()
    try:
        if fetch:
            results: List[Any] = await conn.fetch(query, *args)  # type: ignore
            if one:
                return results[0] if results else None
            return results
        else:
            await conn.execute(query, *args)  # type: ignore
    finally:
        await conn.close()  # type: ignore


async def add_poll(
    question: str,
    options: List[str],
    server_id: int,
) -> Optional[int]:
    query = "INSERT INTO polls (question) VALUES ($1) RETURNING poll_id"
    result = await query_db(query, (question,), one=True)
    poll_id = result["poll_id"] if result else None

    if poll_id is None:
        return None

    await query_db(
        "INSERT INTO poll_servers (poll_id, server_id) VALUES ($1, $2)",
        (poll_id, server_id),  # type: ignore
        fetch=False,
    )

    for option in options:
        await query_db(
            "INSERT INTO options (poll_id, option, votes) VALUES ($1, $2, 0)",
            (poll_id, option),  # type: ignore
            fetch=False,
        )

    return poll_id


async def get_poll(
    poll_id: int,
) -> Optional[Tuple[str, List[Tuple[int, str, int]]]]:
    poll = await query_db(
        "SELECT question FROM polls WHERE poll_id = $1",
        (poll_id,),
        one=True,
        commit=False,
    )
    if poll is None:
        return None

    question = poll["question"]
    options = await query_db(
        "SELECT option_id, option, votes FROM options WHERE poll_id = $1",
        (poll_id,),
        commit=False,
    )
    options = sorted(options, key=lambda x: x["option_id"])
    return question, options


async def record_vote(
    poll_id: int,
    user_id: int,
    option_id: int,
    remove_if_exists: bool = False,
) -> None:
    user_has_voted = (
        await query_db(
            "SELECT * FROM votes WHERE poll_id = $1 AND user_id = $2 \
AND option_id = $3",
            (poll_id, user_id, option_id),  # type: ignore
            one=True,
            commit=False,
        )
        is not None
    )

    if user_has_voted and remove_if_exists:
        await query_db(
            "DELETE FROM votes WHERE poll_id = $1 AND user_id = $2 \
AND option_id = $3",
            (poll_id, user_id, option_id),  # type: ignore
            fetch=False,
        )

        await query_db(
            "UPDATE options SET votes = votes - 1 WHERE option_id = $1",
            (option_id,),
            fetch=False,
        )
    elif not user_has_voted:
        await query_db(
            "INSERT INTO votes (poll_id, user_id, option_id) \
VALUES ($1, $2, $3)",
            (poll_id, user_id, option_id),  # type: ignore
            fetch=False,
        )

        await query_db(
            "UPDATE options SET votes = votes + 1 WHERE option_id = $1",
            (option_id,),
            fetch=False,
        )


async def delete_poll(poll_id: int, server_id: int) -> None:
    poll = await query_db(
        "SELECT * FROM poll_servers WHERE poll_id = $1 AND server_id = $2",
        (poll_id, server_id),  # type: ignore
        one=True,
        commit=False,
    )
    if poll is None:
        raise ValueError(f"Poll ID {poll_id} not found in server")

    await query_db(
        "DELETE FROM poll_servers WHERE poll_id = $1", (poll_id,), fetch=False
    )
    await query_db(
        "DELETE FROM votes WHERE poll_id = $1", (poll_id,), fetch=False
    )
    await query_db(
        "DELETE FROM options WHERE poll_id = $1", (poll_id,), fetch=False
    )
    await query_db(
        "DELETE FROM polls WHERE poll_id = $1", (poll_id,), fetch=False
    )


async def get_user_votes(poll_id: int, user_id: int) -> List[int]:
    votes = await query_db(
        "SELECT option_id FROM votes WHERE poll_id = $1 AND user_id = $2",
        (poll_id, user_id),  # type: ignore
        commit=False,
    )
    return [vote["option_id"] for vote in votes]


async def load_poll_data(
    poll_id: int,
) -> Optional[Tuple[int, List[Dict[str, Any]]]]:
    poll_data = await query_db(
        "SELECT poll_id, option, votes FROM options WHERE poll_id = $1",
        (poll_id,),
        commit=False,
    )

    if poll_data:
        return parse_poll_data(poll_data)
    return None


def parse_poll_data(
    poll_data: List[Record],  # type: ignore
) -> Tuple[int, List[Dict[str, Any]]]:
    poll_id: int = poll_data[0]["poll_id"]  # type: ignore
    options: List[Dict[str, Any]] = []

    for poll in poll_data:  # type: ignore
        option = poll["option"]  # type: ignore
        votes = poll["votes"]  # type: ignore
        options.append(
            {
                "option": option,
                "votes": votes,
            }
        )
    return poll_id, options  # type: ignore
