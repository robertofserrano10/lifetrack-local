from app.db.cms1500_snapshot import list_snapshots_admin

def main():
    print("=== TEST G29: SNAPSHOT INDEX ===")

    rows = list_snapshots_admin()

    if not isinstance(rows, list):
        raise ValueError("FAIL: resultado no es lista")

    print(f"OK: snapshots listados = {len(rows)}")

    if rows:
        sample = rows[0]
        required = {
            "snapshot_id",
            "claim_id",
            "snapshot_hash",
            "created_at",
            "claim_status",
            "locked",
        }

        if not required.issubset(sample.keys()):
            raise ValueError("FAIL: estructura incorrecta")

    print("SNAPSHOT INDEX PASSED ✅")


if __name__ == "__main__":
    main()
