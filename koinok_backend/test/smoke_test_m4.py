"""
test/smoke_test_m4.py
----------------------
Milestone 4 verification script using standard library `urllib`.

Verifies:
  1. Authentication & test item setup (3 items with color/season/is_oversize).
  2. GET /clothes/search?color=... — parameter isolation.
  3. GET /clothes/search?category=...&color=...&is_oversize=... — AND combination.
  4. GET /clothes/search with no matches — empty list, 200.
  5. Multi-tenancy — a second user's search never returns the first user's items.
  6. Soft-deletion exclusion — deleted items drop out of search results.
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def request(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            res = r.read()
            return r.status, json.loads(res) if res else None
    except urllib.error.HTTPError as e:
        res = e.read()
        return e.code, json.loads(res) if res else None


def run_tests():
    results = []

    # ── Setup: Register & Login (User 1) ─────────────────────────────────────
    request("/auth/register", "POST", {"name": "M4 User", "email": "m4_user@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "m4_user@koinok.dev", "password": "secret123"})
    token = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token else 'FAIL'}] Login User 1 (status={code})")
    if not token:
        print("\n--- MILESTONE 4 RESULTS ---")
        for r in results:
            print(r)
        return False

    # ── Create 3 items with color/season/is_oversize ─────────────────────────
    items = [
        ("Black Pants", "bottom", "black", "winter", True),
        ("Black Tee", "top", "black", "summer", False),
        ("White Tee", "top", "white", "summer", False),
    ]
    ids = {}
    for name, category, color, season, oversize in items:
        code, body = request(
            "/clothes/", "POST",
            {"name": name, "category": category, "color": color, "season": season, "is_oversize": oversize},
            token=token,
        )
        ids[name] = body.get("id") if code == 201 else None
        ok = code == 201 and ids[name] is not None
        results.append(f"[{'PASS' if ok else 'FAIL'}] Create {name} (status={code}, id={ids[name]})")

    # ── Test 1: Parameter isolation — color=black ─────────────────────────────
    code, body = request("/clothes/search?color=black", "GET", token=token)
    found = {c["name"] for c in body} if code == 200 else set()
    ok = code == 200 and found == {"Black Pants", "Black Tee"}
    results.append(f"[{'PASS' if ok else 'FAIL'}] GET /clothes/search?color=black (status={code}, found={sorted(found)})")

    # ── Test 2: AND combination — category=top & color=black ─────────────────
    code, body = request("/clothes/search?category=top&color=black", "GET", token=token)
    found = {c["name"] for c in body} if code == 200 else set()
    ok = code == 200 and found == {"Black Tee"}
    results.append(f"[{'PASS' if ok else 'FAIL'}] GET /clothes/search?category=top&color=black (found={sorted(found)})")

    # ── Test 3: is_oversize filter ─────────────────────────────────────────────
    code, body = request("/clothes/search?is_oversize=true", "GET", token=token)
    found = {c["name"] for c in body} if code == 200 else set()
    ok = code == 200 and found == {"Black Pants"}
    results.append(f"[{'PASS' if ok else 'FAIL'}] GET /clothes/search?is_oversize=true (found={sorted(found)})")

    # ── Test 4: Empty result handling ──────────────────────────────────────────
    code, body = request("/clothes/search?color=purple", "GET", token=token)
    ok = code == 200 and body == []
    results.append(f"[{'PASS' if ok else 'FAIL'}] GET /clothes/search?color=purple returns [] (status={code}, body={body})")

    # ── Test 5: Multi-tenancy — User 2 sees nothing from User 1 ──────────────
    request("/auth/register", "POST", {"name": "M4 User 2", "email": "m4_user2@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "m4_user2@koinok.dev", "password": "secret123"})
    token2 = body.get("access_token") if code == 200 else None
    code, body = request("/clothes/search?color=black", "GET", token=token2)
    ok = code == 200 and body == []
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 2 search color=black returns [] (status={code}, body={body})")

    # ── Test 6: Soft-deletion exclusion ────────────────────────────────────────
    request(f"/clothes/{ids['Black Tee']}", "DELETE", token=token)
    code, body = request("/clothes/search?color=black", "GET", token=token)
    found = {c["name"] for c in body} if code == 200 else set()
    ok = code == 200 and found == {"Black Pants"}
    results.append(f"[{'PASS' if ok else 'FAIL'}] After soft-delete, Black Tee excluded (found={sorted(found)})")

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n--- MILESTONE 4 VERIFICATION RESULTS ---")
    for r in results:
        print(r)

    all_pass = all(r.startswith("[PASS]") for r in results)
    print("\nALL TESTS PASSED" if all_pass else "\nSOME TESTS FAILED")
    return all_pass


if __name__ == "__main__":
    run_tests()
