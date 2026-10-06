import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # izinkan frontend (domain lain) memanggil API ini

# Alamat database online, diisi lewat Environment Variable (bukan ditulis di kode)
DATABASE_URL = os.environ["DATABASE_URL"]


def query(sql, params=(), fetch=None):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return cur.rowcount
    finally:
        conn.close()


# Buat tabel otomatis jika belum ada
query(
    """CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
    )"""
)


@app.get("/")
def home():
    return jsonify({"message": "API To-Do berjalan"})


# GET /api/tasks -> ambil semua tugas
@app.get("/api/tasks")
def list_tasks():
    return jsonify(query("SELECT * FROM tasks ORDER BY id DESC", fetch="all"))


# POST /api/tasks -> tambah tugas
@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Judul tugas wajib diisi"}), 400
    row = query("INSERT INTO tasks (title) VALUES (%s) RETURNING *", (title,), fetch="one")
    return jsonify(row), 201


# PUT /api/tasks/<id> -> ubah judul / status selesai
@app.put("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or None
    done = int(data["done"]) if "done" in data else None
    row = query(
        "UPDATE tasks SET title = COALESCE(%s, title), done = COALESCE(%s, done) "
        "WHERE id = %s RETURNING *",
        (title, done, task_id),
        fetch="one",
    )
    if row is None:
        return jsonify({"error": "Tugas tidak ditemukan"}), 404
    return jsonify(row)


# DELETE /api/tasks/<id> -> hapus tugas
@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    if query("DELETE FROM tasks WHERE id = %s", (task_id,)) == 0:
        return jsonify({"error": "Tugas tidak ditemukan"}), 404
    return jsonify({"message": "Tugas dihapus"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
