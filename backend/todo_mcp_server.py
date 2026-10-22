# backend/todo_mcp_server.py
import sqlite3
import json
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Todo Manager")

# 数据库放在 backend 目录下，用绝对路径避免 stdio 子进程工作目录不确定
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            completed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


init_db()


@mcp.tool()
def create_todo(title: str, description: str = "") -> str:
    """创建一条新的待办事项。
    :param title: 待办标题，必填
    :param description: 详细描述，可选
    """
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO todos (title, description) VALUES (?, ?)",
        (title, description),
    )
    conn.commit()
    todo_id = cur.lastrowid
    conn.close()
    return json.dumps({"id": todo_id, "title": title, "status": "created"}, ensure_ascii=False)


@mcp.tool()
def list_todos(filter: str = "all") -> str:
    """列出待办事项。
    :param filter: 筛选条件，可选值：all（全部）、pending（未完成）、completed（已完成）
    """
    conn = get_db()
    if filter == "pending":
        rows = conn.execute("SELECT * FROM todos WHERE completed = 0 ORDER BY id DESC").fetchall()
    elif filter == "completed":
        rows = conn.execute("SELECT * FROM todos WHERE completed = 1 ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM todos ORDER BY id DESC").fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], ensure_ascii=False)


@mcp.tool()
def update_todo(todo_id: int, title: str = None, completed: bool = None) -> str:
    """更新待办事项的标题或完成状态。
    :param todo_id: 待办 ID，必填
    :param title: 新的标题，可选
    :param completed: 是否已完成，可选
    """
    conn = get_db()
    fields, values = [], []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if completed is not None:
        fields.append("completed = ?")
        values.append(1 if completed else 0)
    if not fields:
        conn.close()
        return json.dumps({"error": "没有提供要更新的字段"}, ensure_ascii=False)
    values.append(todo_id)
    conn.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return json.dumps({"id": todo_id, "status": "updated"}, ensure_ascii=False)


@mcp.tool()
def delete_todo(todo_id: int) -> str:
    """删除指定 ID 的待办事项。
    :param todo_id: 待办 ID，必填
    """
    conn = get_db()
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    return json.dumps({"id": todo_id, "status": "deleted"}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")