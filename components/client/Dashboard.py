"""
Dashboard.py / iot_dashboard.py

Small Python library for controlling the PHP IoT Panel database.

Main features:
- Card class creates a card database record.
- Card.sync() reloads the card from MySQL.
- Card.save() writes local property changes to MySQL.
- Card properties can be accessed/modified directly, e.g. card.title = "New Title".
- Card destructor removes the card from the database.
- clear() truncates the iot_cards table.
- Database and table are created automatically if they do not exist.

Validation note:
- This library intentionally does NOT validate card types or colors.
- The frontend/dashboard is expected to handle unsupported or invalid records.
- This makes it easier to add new card types without changing the Python library.

Dependency:
    pip install mysql-connector-python
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, Optional, Union

try:
    import mysql.connector
except ImportError as exc:
    raise ImportError(
        "mysql-connector-python is required. Install it with: "
        "pip install mysql-connector-python"
    ) from exc


# ---------------------------------------------------------------------
# Default database configuration
# ---------------------------------------------------------------------
# You can either edit these values or call configure(...).
# These should match config.php in the PHP panel.

_DB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "user": "codynick",
    "password": "codynick",
    "database": "codynick",
    "port": 3306,
}

_TABLE_NAME = "iot_cards"
_LOCK = threading.RLock()


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

def configure(
    host: str = "localhost",
    user: str = "root",
    password: str = "",
    database: str = "iot_dashboard",
    port: int = 3306,
) -> None:
    """
    Configure the MySQL connection used by this library.

    Example:
        import Dashboard

        Dashboard.configure(
            host="localhost",
            user="iot_user",
            password="iot_pass",
            database="iot_dashboard"
        )
    """
    with _LOCK:
        _DB_CONFIG.update({
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
        })


def _connect(include_database: bool = True):
    """
    Connect to MySQL.

    If include_database=False, connect to the MySQL server without selecting
    a database. This is required before CREATE DATABASE can run safely.
    """
    cfg = dict(_DB_CONFIG)

    if not include_database:
        cfg.pop("database", None)

    return mysql.connector.connect(**cfg)


def ensure_database() -> None:
    """
    Create the configured database if it does not exist.

    This fixes:
        mysql.connector.errors.ProgrammingError: 1046 (3D000): No database selected
    """
    db_name = _DB_CONFIG.get("database")

    if not db_name:
        raise RuntimeError("No database name configured. Call configure(database='...') first.")

    with _LOCK:
        conn = _connect(include_database=False)
        try:
            cur = conn.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
        finally:
            conn.close()


def ensure_table() -> None:
    """
    Create the database and iot_cards table if they do not exist.

    This mirrors the table expected by the PHP dashboard.
    It also tries to add missing columns for older installations.
    """
    with _LOCK:
        ensure_database()

        conn = _connect(include_database=True)
        try:
            cur = conn.cursor()

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS `{_TABLE_NAME}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    color VARCHAR(20) DEFAULT 'blue',
                    min_value FLOAT DEFAULT NULL,
                    max_value FLOAT DEFAULT NULL,
                    value TEXT DEFAULT NULL,
                    description TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)

            # Lightweight migration for older versions of the panel.
            existing = _get_columns(cur)

            migrations = {
                "min_value": f"ALTER TABLE `{_TABLE_NAME}` ADD COLUMN min_value FLOAT DEFAULT NULL AFTER color",
                "max_value": f"ALTER TABLE `{_TABLE_NAME}` ADD COLUMN max_value FLOAT DEFAULT NULL AFTER min_value",
                "value": f"ALTER TABLE `{_TABLE_NAME}` ADD COLUMN value TEXT DEFAULT NULL AFTER max_value",
                "description": f"ALTER TABLE `{_TABLE_NAME}` ADD COLUMN description TEXT DEFAULT NULL AFTER value",
                "created_at": f"ALTER TABLE `{_TABLE_NAME}` ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }

            for column, sql in migrations.items():
                if column not in existing:
                    cur.execute(sql)

            conn.commit()
        finally:
            conn.close()


def _get_columns(cur) -> set:
    cur.execute(f"SHOW COLUMNS FROM `{_TABLE_NAME}`")
    return {row[0] for row in cur.fetchall()}


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def clear() -> None:
    """
    Truncate all dashboard cards.

    Example:
        import Dashboard
        Dashboard.clear()
    """
    ensure_table()

    with _LOCK:
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(f"TRUNCATE TABLE `{_TABLE_NAME}`")
            conn.commit()
        finally:
            conn.close()


def _normalize_type(card_type: Any) -> str:
    """
    Normalize card type lightly, without validation.

    Keeps unknown card types, so the frontend can decide how to display them.
    """
    card_type = str(card_type).strip().lower()

    # Accept common misspelling as a convenience, but do not validate.
    if card_type == "guage":
        return "gauge"

    return card_type


def _normalize_color(color: Any) -> str:
    """
    Normalize color lightly, without validation.

    Keeps unknown colors, so the frontend can decide how to display them.
    """
    return str(color).strip().lower()


def _encode_value(value: Any) -> Optional[str]:
    """
    Convert Python values to DB strings.

    Dict/list values are JSON-encoded, which is useful for graph/table cards.
    Booleans become 'true'/'false'.
    None remains NULL.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _decode_value(value: Optional[str]) -> Optional[str]:
    """
    Keep DB values as strings by default.

    The PHP dashboard expects strings/JSON text.
    If you want parsed JSON, use Card.value_json().
    """
    return value


# ---------------------------------------------------------------------
# Card class
# ---------------------------------------------------------------------

class Card:
    """
    Represents one dashboard card.

    Creating a Card immediately inserts a database record.

    This class intentionally does not validate card types or colors. Unknown
    types/colors are saved as-is, so the frontend can handle them.

    Example:
        import Dashboard

        Dashboard.configure(user="root", password="", database="iot_dashboard")
        Dashboard.clear()

        led = Dashboard.Card("led", "LED0", color="red", value=False)
        led.value = True
        led.save()

        custom = Dashboard.Card("my_custom_card", "Custom", color="purple", value="Hello")
    """

    def __init__(
        self,
        card_type: str,
        title: str,
        color: str = "blue",
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        value: Any = None,
        description: Optional[str] = None,
        *,
        auto_delete: bool = True,
    ) -> None:
        ensure_table()

        self.id: Optional[int] = None
        self.type = _normalize_type(card_type)
        self.title = str(title)
        self.color = _normalize_color(color)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.description = description
        self.auto_delete = auto_delete

        self._insert()

    def _insert(self) -> None:
        with _LOCK:
            conn = _connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    f"""
                    INSERT INTO `{_TABLE_NAME}`
                        (type, title, color, min_value, max_value, value, description)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.type,
                        self.title,
                        self.color,
                        self.min_value,
                        self.max_value,
                        _encode_value(self.value),
                        self.description,
                    ),
                )
                conn.commit()
                self.id = cur.lastrowid
            finally:
                conn.close()

    def sync(self) -> bool:
        """
        Reload this card from the database.

        Returns:
            True if the card still exists.
            False if the card was not found.
        """
        if self.id is None:
            return False

        ensure_table()

        with _LOCK:
            conn = _connect()
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute(
                    f"""
                    SELECT id, type, title, color, min_value, max_value, value, description
                    FROM `{_TABLE_NAME}`
                    WHERE id = %s
                    LIMIT 1
                    """,
                    (self.id,),
                )
                row = cur.fetchone()

                if not row:
                    return False

                self.type = row["type"]
                self.title = row["title"]
                self.color = row["color"]
                self.min_value = row["min_value"]
                self.max_value = row["max_value"]
                self.value = _decode_value(row["value"])
                self.description = row["description"]

                return True
            finally:
                conn.close()

    def save(self) -> None:
        """
        Save the current object properties to the database.

        Example:
            card.title = "New Title"
            card.color = "yellow"
            card.type = "custom_type"
            card.value = 75
            card.save()
        """
        if self.id is None:
            raise RuntimeError("Cannot save a deleted card.")

        self.type = _normalize_type(self.type)
        self.color = _normalize_color(self.color)

        ensure_table()

        with _LOCK:
            conn = _connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    f"""
                    UPDATE `{_TABLE_NAME}`
                    SET
                        type = %s,
                        title = %s,
                        color = %s,
                        min_value = %s,
                        max_value = %s,
                        value = %s,
                        description = %s
                    WHERE id = %s
                    """,
                    (
                        self.type,
                        self.title,
                        self.color,
                        self.min_value,
                        self.max_value,
                        _encode_value(self.value),
                        self.description,
                        self.id,
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def delete(self) -> None:
        """
        Delete this card from the database.
        """
        if self.id is None:
            return

        ensure_table()

        with _LOCK:
            conn = _connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    f"DELETE FROM `{_TABLE_NAME}` WHERE id = %s",
                    (self.id,),
                )
                conn.commit()
                self.id = None
            finally:
                conn.close()

    def value_json(self) -> Any:
        """
        Parse this card's value as JSON.

        Useful for graph/table cards after sync().
        """
        if self.value is None:
            return None

        if isinstance(self.value, (dict, list)):
            return self.value

        return json.loads(str(self.value))

    def set(self, value: Any, *, save: bool = True) -> None:
        """
        Convenience method for changing value.

        Example:
            led.set(True)
            temp.set(25.6)
        """
        self.value = value

        if save:
            self.save()

    def __enter__(self) -> "Card":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.delete()

    def __del__(self) -> None:
        """
        Destructor removes the card from the database by default.

        Note:
            Python destructors are not guaranteed to run at interpreter shutdown
            in all circumstances. For critical cleanup, use card.delete(),
            Dashboard.clear(), or a context manager.
        """
        try:
            if getattr(self, "auto_delete", False):
                self.delete()
        except Exception:
            # Never raise from a destructor.
            pass

    def __repr__(self) -> str:
        return (
            f"Card(id={self.id!r}, type={self.type!r}, title={self.title!r}, "
            f"color={self.color!r}, value={self.value!r})"
        )


# Optional lowercase alias if preferred.
card = Card
