"""
test/smoke_test_m5.py
----------------------
Milestone 5 verification script using standard library `urllib`.

Verifies:
  1. Bidirectional matchmaking symmetry — linking A → B makes B show A back.
  2. Self-linking is rejected (400).
  3. Cross-user matching is rejected (404).
  4. Duplicate match links don't create duplicate entries.
  5. Look creation bundles items and is returned with nested ClothResponse items.
  6. Cross-user Look creation is rejected (400).
  7. GET /looks/ lists only the authenticated user's Looks.
  8. Soft-deleted items are excluded from matches and Look payloads.
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
    request("/auth/register", "POST", {"name": "M5 User", "email": "m5_user@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "m5_user@koinok.dev", "password": "secret123"})
    token = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token else 'FAIL'}] Login User 1 (status={code})")

    request("/auth/register", "POST", {"name": "M5 User 2", "email": "m5_user2@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "m5_user2@koinok.dev", "password": "secret123"})
    token2 = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token2 else 'FAIL'}] Login User 2 (status={code})")

    if not token or not token2:
        print("\n--- MILESTONE 5 RESULTS ---")
        for r in results:
            print(r)
        return False

    # ── Create items for User 1 ───────────────────────────────────────────────
    ids = {}
    for name, category in [("Denim Jacket", "outerwear"), ("White Tee", "top"), ("Black Jeans", "bottom"), ("Deleted Item", "top")]:
        code, body = request("/clothes/", "POST", {"name": name, "category": category}, token=token)
        ids[name] = body.get("id") if code == 201 else None

    # Item for User 2
    code, body = request("/clothes/", "POST", {"name": "User2 Shirt", "category": "top"}, token=token2)
    user2_item_id = body.get("id") if code == 201 else None

    # ── Test 1: Bidirectional symmetry ────────────────────────────────────────
    code, body = request(
        f"/clothes/{ids['Denim Jacket']}/match", "POST",
        {"matched_cloth_ids": [ids["White Tee"]]}, token=token,
    )
    ok = code == 200 and any(m["id"] == ids["White Tee"] for m in body.get("matching_clothes", []))
    results.append(f"[{'PASS' if ok else 'FAIL'}] Link Denim Jacket -> White Tee (status={code})")

    code, body = request(f"/clothes/{ids['White Tee']}", "GET", token=token)
    ok = code == 200 and any(m["id"] == ids["Denim Jacket"] for m in body.get("matching_clothes", []))
    results.append(f"[{'PASS' if ok else 'FAIL'}] White Tee shows reciprocal match to Denim Jacket (status={code})")

    # ── Test 2: Self-linking rejected ─────────────────────────────────────────
    code, body = request(
        f"/clothes/{ids['Denim Jacket']}/match", "POST",
        {"matched_cloth_ids": [ids["Denim Jacket"]]}, token=token,
    )
    ok = code == 400
    results.append(f"[{'PASS' if ok else 'FAIL'}] Self-link rejected (status={code})")

    # ── Test 3: Cross-user linking rejected ───────────────────────────────────
    code, body = request(
        f"/clothes/{ids['Denim Jacket']}/match", "POST",
        {"matched_cloth_ids": [user2_item_id]}, token=token,
    )
    ok = code == 404
    results.append(f"[{'PASS' if ok else 'FAIL'}] Cross-user link rejected (status={code})")

    # ── Test 4: Duplicate link doesn't duplicate entries ──────────────────────
    request(f"/clothes/{ids['Denim Jacket']}/match", "POST", {"matched_cloth_ids": [ids["White Tee"]]}, token=token)
    code, body = request(f"/clothes/{ids['Denim Jacket']}", "GET", token=token)
    match_ids = [m["id"] for m in body.get("matching_clothes", [])]
    ok = code == 200 and match_ids.count(ids["White Tee"]) == 1
    results.append(f"[{'PASS' if ok else 'FAIL'}] No duplicate match entries (matches={match_ids})")

    # ── Test 5: Look creation ─────────────────────────────────────────────────
    code, body = request(
        "/looks/", "POST",
        {"name": "Casual Fit", "cloth_ids": [ids["Denim Jacket"], ids["White Tee"], ids["Black Jeans"]]},
        token=token,
    )
    look_names = {c["name"] for c in body.get("clothes", [])} if code == 201 else set()
    ok = code == 201 and look_names == {"Denim Jacket", "White Tee", "Black Jeans"}
    results.append(f"[{'PASS' if ok else 'FAIL'}] Create Look 'Casual Fit' (status={code}, items={sorted(look_names)})")
    look_id = body.get("id") if code == 201 else None

    # ── Test 6: Cross-user Look creation rejected ─────────────────────────────
    code, body = request(
        "/looks/", "POST",
        {"name": "Bad Look", "cloth_ids": [user2_item_id]}, token=token,
    )
    ok = code == 400
    results.append(f"[{'PASS' if ok else 'FAIL'}] Look with another user's item rejected (status={code})")

    # ── Test 7: GET /looks/ isolation ─────────────────────────────────────────
    code, body = request("/looks/", "GET", token=token)
    ok = code == 200 and any(l["id"] == look_id for l in body)
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 sees own Look (status={code})")

    code, body = request("/looks/", "GET", token=token2)
    ok = code == 200 and body == []
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 2 sees no Looks (status={code}, body={body})")

    # ── Test 8: Soft-delete resilience ────────────────────────────────────────
    request(
        f"/clothes/{ids['Denim Jacket']}/match", "POST",
        {"matched_cloth_ids": [ids["Deleted Item"]]}, token=token,
    )
    request(f"/clothes/{ids['Deleted Item']}", "DELETE", token=token)

    code, body = request(f"/clothes/{ids['Denim Jacket']}", "GET", token=token)
    match_ids = [m["id"] for m in body.get("matching_clothes", [])]
    ok = code == 200 and ids["Deleted Item"] not in match_ids
    results.append(f"[{'PASS' if ok else 'FAIL'}] Soft-deleted item excluded from matches (matches={match_ids})")

    code, body = request(
        "/looks/", "POST",
        {"name": "With Deleted", "cloth_ids": [ids["White Tee"], ids["Deleted Item"]]}, token=token,
    )
    ok = code == 400
    results.append(f"[{'PASS' if ok else 'FAIL'}] Look creation with soft-deleted item rejected (status={code})")

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n--- MILESTONE 5 VERIFICATION RESULTS ---")
    for r in results:
        print(r)

    all_pass = all(r.startswith("[PASS]") for r in results)
    print("\nALL TESTS PASSED" if all_pass else "\nSOME TESTS FAILED")
    return all_pass


if __name__ == "__main__":
    run_tests()
