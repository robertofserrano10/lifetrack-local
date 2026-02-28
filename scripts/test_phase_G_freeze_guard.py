from app.db.connection import get_connection
from app.db.claims import update_claim_operational_status

def main():
    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Detectar un claim que tenga snapshot (o el más reciente)
        # Ajusta el nombre de tabla/columna si en tu schema el snapshot se llama distinto.
        cur.execute("""
            SELECT s.id AS snapshot_id, s.claim_id AS claim_id
            FROM cms1500_snapshots s
            ORDER BY s.id DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        if not row:
            raise SystemExit("No hay snapshots en la DB. Corre scripts.test_phase_B1_generate_snapshot primero.")

        snapshot_id = row["snapshot_id"]
        claim_id = row["claim_id"]

        # 2) Leer status actual del claim (operacional)
        cur.execute("SELECT status FROM claims WHERE id = ?", (claim_id,))
        claim = cur.fetchone()
        if not claim:
            raise SystemExit(f"Claim {claim_id} no existe.")

        current_status = claim["status"]

        print(f"Usando snapshot_id={snapshot_id} claim_id={claim_id} current_status={current_status}")

        # 3) Intentar una transición (debe BLOQUEARSE por freeze)
        attempted_new_status = "READY" if current_status != "READY" else "SUBMITTED"

        try:
            update_claim_operational_status(claim_id, attempted_new_status)
            raise SystemExit("ERROR: La transición NO se bloqueó. Se esperaba ValueError por freeze.")
        except ValueError as e:
            msg = str(e)
            print("OK: ValueError recibido:", msg)
            if "transición bloqueada" not in msg:
                raise SystemExit("ERROR: Mensaje de error inesperado (no parece freeze).")

        # 4) Verificar auditoría en event_ledger (último evento del claim)
        cur.execute("""
            SELECT id, event_type, event_data, created_at
            FROM event_ledger
            WHERE entity_type='claim' AND entity_id=?
            ORDER BY id DESC
            LIMIT 1
        """, (claim_id,))
        ev = cur.fetchone()
        if not ev:
            raise SystemExit("ERROR: No se registró ningún evento en event_ledger.")

        print("Último evento:", dict(ev))
        if ev["event_type"] != "freeze_blocked_transition":
            raise SystemExit(f"ERROR: event_type esperado freeze_blocked_transition, recibido {ev['event_type']}")

        if f"\"attempted_new_status\": \"{attempted_new_status}\"" not in ev["event_data"]:
            raise SystemExit("ERROR: event_data no contiene attempted_new_status esperado.")

        print("✅ PASS: freeze guard bloquea transición y audita en event_ledger.")

if __name__ == "__main__":
    main()