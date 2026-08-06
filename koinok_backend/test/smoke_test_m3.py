"""
test/smoke_test_m3.py
---------------------
Milestone 3 verification script using standard library `urllib`.

Verifies:
  1. Authentication & test item setup (3 items: A, B, C).
  2. POST /calendar/log-day — batch log Item A + B for today (201).
  3. POST /calendar/log-day — log Item A on a date >14 days ago (201).
  4. GET /calendar — today's entry contains Item A and Item B.
  5. GET /clothes/suggested — Item C appears in hidden_gems (never worn).
  6. GET /clothes/suggested — Item A's old-date-only log appears in forgotten_favorites
     (only after we delete today's fresh log and re-check — see note below).
  7. Soft-delete Item C, verify it no longer appears in suggestions.

Note on test design:
  - We log Item A on BOTH today AND >14 days ago in step 2 & 3.
  - That means Item A will be recently worn and NOT in forgotten_favorites.
  - To test forgotten_favorites correctly, we use a 4th fresh item (Item D) that
    is logged ONLY on a date older than 14 days.
"""

import json
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE = "http://127.0.0.1:8000"
TODAY = date.today().isoformat()
OLD_DATE = (date.today() - timedelta(days=20)).isoformat()


def request(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
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

    # ── Setup: Register & Login ──────────────────────────────────────────────
    request("/auth/register", "POST", {"name": "M3 User", "email": "m3_user@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "m3_user@koinok.dev", "password": "secret123"})
    token = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token else 'FAIL'}] Login (status={code})")
    if not token:
        print("\n--- MILESTONE 3 RESULTS ---")
        for r in results:
            print(r)
        return False

    # ── Create 4 items: A, B, C (hidden_gems), D (forgotten_favorites) ──────
    ids = {}
    for name, category in [("Item A", "top"), ("Item B", "bottom"), ("Item C", "outerwear"), ("Item D", "footwear")]:
        code, body = request("/clothes/", "POST", {"name": name, "category": category}, token=token)
        ids[name] = body.get("id") if code == 201 else None
        ok = code == 201 and ids[name] is not None
        results.append(f"[{'PASS' if ok else 'FAIL'}] Create {name} (status={code}, id={ids[name]})")

    # ── Test 1: Batch log Item A + B for TODAY ───────────────────────────────
    code, body = request(
        "/calendar/log-day", "POST",
        {"cloth_ids": [ids["Item A"], ids["Item B"]], "worn_date": TODAY},
        token=token,
    )
    ok = code == 201 and "logs" in body and len(body["logs"]) == 2
    results.append(f"[{'PASS' if ok else 'FAIL'}] POST /calendar/log-day (today, A+B) status={code} logged={len(body.get('logs', []))}")

    # ── Test 2: Log Item D on OLD date (>14 days ago) ────────────────────────
    code, body = request(
        "/calendar/log-day", "POST",
        {"cloth_ids": [ids["Item D"]], "worn_date": OLD_DATE},
        token=token,
    )
    ok = code == 201 and "logs" in body and len(body["logs"]) == 1
    results.append(f"[{'PASS' if ok else 'FAIL'}] POST /calendar/log-day (old date, D) status={code}")

    # ── Test 3: Calendar retrieval — today's entry has A and B ───────────────
    code, body = request("/calendar", "GET", token=token)
    today_entry = next((day for day in body if day["date"] == TODAY), None)
    today_ids = {item["id"] for item in today_entry["items"]} if today_entry else set()
    ok = code == 200 and ids["Item A"] in today_ids and ids["Item B"] in today_ids
    results.append(f"[{'PASS' if ok else 'FAIL'}] GET /calendar today has A+B (status={code}, found_ids={sorted(today_ids)})")

    # ── Test 4: Suggestions — Item C in hidden_gems ──────────────────────────
    code, body = request("/clothes/suggested", "GET", token=token)
    hidden_gem_ids = {item["id"] for item in body.get("hidden_gems", [])}
    forgotten_ids = {item["id"] for item in body.get("forgotten_favorites", [])}

    c_in_gems = ids["Item C"] in hidden_gem_ids
    results.append(f"[{'PASS' if c_in_gems else 'FAIL'}] GET /clothes/suggested — Item C in hidden_gems (status={code}, hidden_gem_ids={sorted(hidden_gem_ids)})")

    # ── Test 5: Suggestions — Item D in forgotten_favorites ──────────────────
    d_in_forgotten = ids["Item D"] in forgotten_ids
    results.append(f"[{'PASS' if d_in_forgotten else 'FAIL'}] GET /clothes/suggested — Item D in forgotten_favorites (forgotten_ids={sorted(forgotten_ids)})")

    # ── Test 6: Items logged within 14 days NOT in suggestions ───────────────
    a_not_suggested = ids["Item A"] not in hidden_gem_ids and ids["Item A"] not in forgotten_ids
    b_not_suggested = ids["Item B"] not in hidden_gem_ids and ids["Item B"] not in forgotten_ids
    ok = a_not_suggested and b_not_suggested
    results.append(f"[{'PASS' if ok else 'FAIL'}] Items A+B (worn today) NOT in suggestions (A_excluded={a_not_suggested}, B_excluded={b_not_suggested})")

    # ── Test 7: Soft-delete Item C, verify excluded from suggestions ──────────
    request(f"/clothes/{ids['Item C']}", "DELETE", token=token)
    code, body = request("/clothes/suggested", "GET", token=token)
    hidden_gem_ids_after = {item["id"] for item in body.get("hidden_gems", [])}
    forgotten_ids_after = {item["id"] for item in body.get("forgotten_favorites", [])}
    c_absent = ids["Item C"] not in hidden_gem_ids_after and ids["Item C"] not in forgotten_ids_after
    results.append(f"[{'PASS' if c_absent else 'FAIL'}] After soft-delete, Item C absent from suggestions (status={code})")

    # ── Print results ─────────────────────────────────────────────────────────
    print("\n--- MILESTONE 3 VERIFICATION RESULTS ---")
    for r in results:
        print(r)

    all_pass = all(r.startswith("[PASS]") for r in results)
    print("\nALL TESTS PASSED" if all_pass else "\nSOME TESTS FAILED")
    return all_pass


if __name__ == "__main__":
    run_tests()
