"""
test/smoke_test_m2.py
---------------------
Milestone 2 validation script using standard library `urllib`.

Verifies:
  1. User authentication & token extraction.
  2. POST /clothes/ (Item creation).
  3. GET /clothes/ (Active items listing).
  4. User isolation (User 2 cannot access or delete User 1's items -> 404).
  5. DELETE /clothes/{id} (Soft deletion -> is_deleted=True).
  6. GET /clothes/ (Verification that soft-deleted item is excluded).
  7. POST /clothes/{id}/restore (Restoration -> is_deleted=False).
  8. GET /clothes/ (Verification that restored item is listed again).
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def request(path, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as r:
            res_body = r.read()
            return r.status, json.loads(res_body) if res_body else None
    except urllib.error.HTTPError as e:
        res_body = e.read()
        return e.code, json.loads(res_body) if res_body else None


def run_tests():
    results = []

    # 1. Register & Login User 1
    request("/auth/register", "POST", {"name": "User 1", "email": "user1_m2@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "user1_m2@koinok.dev", "password": "secret123"})
    token1 = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token1 else 'FAIL'}] User 1 Login (status={code})")

    # 2. Register & Login User 2
    request("/auth/register", "POST", {"name": "User 2", "email": "user2_m2@koinok.dev", "password": "secret123"})
    code, body = request("/auth/login", "POST", {"email": "user2_m2@koinok.dev", "password": "secret123"})
    token2 = body.get("access_token") if code == 200 else None
    results.append(f"[{'PASS' if token2 else 'FAIL'}] User 2 Login (status={code})")

    if not token1 or not token2:
        print("Failed to authenticate test users.")
        return False

    # 3. User 1 creates cloth
    code, body = request(
        "/clothes/",
        "POST",
        {"name": "Leather Jacket", "category": "outerwear"},
        token=token1,
    )
    cloth_id = body.get("id") if body else None
    ok = code == 201 and body and body.get("name") == "Leather Jacket" and not body.get("is_deleted")
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 POST /clothes/ (status={code}, id={cloth_id})")

    # 4. User 1 gets active clothes
    code, body = request("/clothes/", "GET", token=token1)
    found = any(c["id"] == cloth_id for c in body) if isinstance(body, list) else False
    ok = code == 200 and found
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 GET /clothes/ (status={code}, item_found={found})")

    # 5. User 2 attempts to fetch User 1's cloth (Isolation test)
    code, body = request(f"/clothes/{cloth_id}", "GET", token=token2)
    ok = code == 404
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 2 GET /clothes/{cloth_id} isolation check (status={code}, expected=404)")

    # 6. User 2 attempts to soft-delete User 1's cloth (Isolation test)
    code, body = request(f"/clothes/{cloth_id}", "DELETE", token=token2)
    ok = code == 404
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 2 DELETE /clothes/{cloth_id} isolation check (status={code}, expected=404)")

    # 7. User 1 soft deletes cloth
    code, body = request(f"/clothes/{cloth_id}", "DELETE", token=token1)
    ok = code == 200 and body and body.get("is_deleted") is True
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 DELETE /clothes/{cloth_id} (status={code}, is_deleted={body.get('is_deleted') if body else None})")

    # 8. User 1 gets active clothes (Should exclude deleted item)
    code, body = request("/clothes/", "GET", token=token1)
    deleted_present = any(c["id"] == cloth_id for c in body) if isinstance(body, list) else True
    ok = code == 200 and not deleted_present
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 GET /clothes/ post-delete (status={code}, excluded={not deleted_present})")

    # 9. User 1 restores cloth
    code, body = request(f"/clothes/{cloth_id}/restore", "POST", token=token1)
    ok = code == 200 and body and body.get("is_deleted") is False
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 POST /clothes/{cloth_id}/restore (status={code}, is_deleted={body.get('is_deleted') if body else None})")

    # 10. User 1 gets active clothes (Should include restored item again)
    code, body = request("/clothes/", "GET", token=token1)
    restored_present = any(c["id"] == cloth_id for c in body) if isinstance(body, list) else False
    ok = code == 200 and restored_present
    results.append(f"[{'PASS' if ok else 'FAIL'}] User 1 GET /clothes/ post-restore (status={code}, restored_visible={restored_present})")

    print("\n--- MILESTONE 2 VERIFICATION RESULTS ---")
    for r in results:
        print(r)

    all_pass = all(r.startswith("[PASS]") for r in results)
    print("\nALL TESTS PASSED" if all_pass else "\nSOME TESTS FAILED")
    return all_pass


if __name__ == "__main__":
    run_tests()
