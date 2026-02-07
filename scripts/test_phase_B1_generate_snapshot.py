import sqlite3
from app.db.cms1500_snapshot import generate_cms1500_snapshot

DB_PATH = "storage/lifetrack.db"


def main():
    r = generate_cms1500_snapshot(1)
    print("✅ snapshot generado")
    print("HASH:", r["snapshot_hash"])

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cms1500_snapshots WHERE claim_id = 1")
    n = cur.fetchone()[0]
    conn.close()
    print("snapshots para claim 1 =", n)


if __name__ == "__main__":
    main()
