import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.core import constants as core_const


@dataclass
class AutoFillRule:
    item_id: str
    target_count: int
    trigger: str
    enabled: bool = True


def _get_db_path() -> Path:
    db_path = core_const.DB_PATH
    assert db_path is not None
    return db_path


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(str(_get_db_path()))


def _init_db():
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS auto_fill_rules ("
        "item_id TEXT PRIMARY KEY, "
        "target_count INTEGER NOT NULL, "
        "trigger TEXT NOT NULL, "
        "enabled INTEGER NOT NULL DEFAULT 1)"
    )
    con.commit()
    con.close()


def load_rules() -> list[AutoFillRule]:
    """依新增順序回傳所有規則（列表顯示的編號即為這個順序的 1..n）。"""
    _init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "SELECT item_id, target_count, trigger, enabled "
        "FROM auto_fill_rules ORDER BY rowid"
    )
    rows = cur.fetchall()
    con.close()

    rules: list[AutoFillRule] = []
    for item_id, target_count, trigger, enabled in rows:
        try:
            count = int(target_count)
        except (TypeError, ValueError):
            continue
        rules.append(AutoFillRule(
            item_id=item_id,
            target_count=count,
            trigger=trigger,
            enabled=bool(enabled),
        ))
    return rules


def save_rule(rule: AutoFillRule):
    _init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE auto_fill_rules SET target_count = ?, trigger = ?, enabled = ? "
        "WHERE item_id = ?",
        (rule.target_count, rule.trigger, 1 if rule.enabled else 0, rule.item_id),
    )
    if cur.rowcount == 0:
        cur.execute(
            "INSERT INTO auto_fill_rules (item_id, target_count, trigger, enabled) "
            "VALUES (?, ?, ?, ?)",
            (rule.item_id, rule.target_count, rule.trigger, 1 if rule.enabled else 0),
        )
    con.commit()
    con.close()


def delete_rule(item_id: str) -> bool:
    _init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute("DELETE FROM auto_fill_rules WHERE item_id = ?", (item_id,))
    removed = cur.rowcount > 0
    con.commit()
    con.close()
    return removed


def set_rule_enabled(item_id: str, enabled: bool) -> bool:
    _init_db()
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE auto_fill_rules SET enabled = ? WHERE item_id = ?",
        (1 if enabled else 0, item_id),
    )
    updated = cur.rowcount > 0
    con.commit()
    con.close()
    return updated
