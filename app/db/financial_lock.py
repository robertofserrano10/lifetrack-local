from app.db.connection import get_connection


def is_claim_locked(claim_id: int) -> bool:
    """
    Retorna True si el claim ya tiene snapshot CMS-1500.
    Eso implica congelación financiera.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM cms1500_snapshots
            WHERE claim_id = ?
            LIMIT 1
            """,
            (claim_id,),
        )
        return cur.fetchone() is not None
