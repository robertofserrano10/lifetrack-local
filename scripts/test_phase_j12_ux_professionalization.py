# scripts/test_phase_j12_ux_professionalization.py
# FASE J12 — UX Professionalization

from app.main import app


def main():
    with app.test_client() as client:
        # Login with admin user from bootstrap
        resp = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        assert resp.status_code == 200, f"Login failed: {resp.status_code}"

        # Access UX dashboard
        resp2 = client.get("/admin/ux-dashboard")
        body = resp2.get_data(as_text=True)

        assert resp2.status_code == 200, f"UX dashboard not reachable {resp2.status_code}"
        assert "UX Professionalization" in body

    print("TEST PASSED: J12 UX dashboard accessible y contenido presente")


if __name__ == "__main__":
    main()
