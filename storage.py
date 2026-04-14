"""SQLite persistence layer for scored repository records."""

import logging
import sqlite3
from datetime import date
from pathlib import Path

from models import ScoredRepo

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("research_agent.db")


def _get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create the ``scored_repos`` table if it does not already exist.

    Args:
        db_path: Path to the SQLite database file.
    """
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scored_repos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date      TEXT    NOT NULL,
                name             TEXT    NOT NULL,
                url              TEXT    NOT NULL,
                relevance_score  INTEGER NOT NULL,
                summary          TEXT    NOT NULL,
                reason           TEXT    NOT NULL,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    logger.debug("Database initialised at %s.", db_path)


def save_repos(
    repos: list[ScoredRepo],
    report_date: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """Persist a list of scored repositories for *report_date*.

    Args:
        repos:       Scored repositories to store.
        report_date: ISO-8601 date string (defaults to today).
        db_path:     Path to the SQLite database file.
    """
    if report_date is None:
        report_date = date.today().isoformat()

    init_db(db_path)
    rows = [
        (
            report_date,
            r.name,
            r.url,
            r.relevance_score,
            r.summary,
            r.reason,
        )
        for r in repos
    ]
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            DELETE FROM scored_repos
            WHERE report_date = ?
            """,
            (report_date,),
        )
        if rows:
            conn.executemany(
                """
                INSERT INTO scored_repos
                    (report_date, name, url, relevance_score, summary, reason)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        conn.commit()
    logger.info("Saved %d repo(s) for date %s.", len(repos), report_date)


def load_repos(
    report_date: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[ScoredRepo]:
    """Load scored repositories from the database for *report_date*.

    Args:
        report_date: ISO-8601 date string (defaults to today).
        db_path:     Path to the SQLite database file.

    Returns:
        List of :class:`ScoredRepo` objects ordered by relevance_score
        descending.
    """
    if report_date is None:
        report_date = date.today().isoformat()

    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT name, url, relevance_score, summary, reason
            FROM   scored_repos
            WHERE  report_date = ?
            ORDER  BY relevance_score DESC
            """,
            (report_date,),
        )
        rows = cursor.fetchall()

    repos = [
        ScoredRepo(
            name=row["name"],
            url=row["url"],
            relevance_score=row["relevance_score"],
            summary=row["summary"],
            reason=row["reason"],
        )
        for row in rows
    ]
    logger.info(
        "Loaded %d repo(s) for date %s from %s.",
        len(repos),
        report_date,
        db_path,
    )
    return repos
