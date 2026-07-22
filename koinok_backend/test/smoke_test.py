import urllib.request, json, urllib.error

BASE = 'http://127.0.0.1:8000'

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f'{BASE}{path}', data=data,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def get(path):
    with urllib.request.urlopen(f'{BASE}{path}') as r:
        return r.status, json.loads(r.read())

results = []

# 1. Health check
code, body = get('/health')
ok = code == 200 and body.get('status') == 'ok'
results.append(f"[{'PASS' if ok else 'FAIL'}] GET /health = {code} {body}")

# 2. Register
code, body = post('/auth/register', {'name': 'Test User', 'email': 'test@koinok.dev', 'password': 'secret123'})
ok = code == 201
results.append(f"[{'PASS' if ok else 'FAIL'}] POST /auth/register = {code} keys={list(body.keys())}")

# 3. Duplicate -> 400
code, body = post('/auth/register', {'name': 'Test User', 'email': 'test@koinok.dev', 'password': 'secret123'})
detail = body.get('detail', '')
ok = code == 400 and 'already registered' in detail
results.append(f"[{'PASS' if ok else 'FAIL'}] POST /auth/register (dup) = {code} detail={detail}")

# 4. Login
code, body = post('/auth/login', {'email': 'test@koinok.dev', 'password': 'secret123'})
ok = code == 200 and 'access_token' in body
results.append(f"[{'PASS' if ok else 'FAIL'}] POST /auth/login = {code} has_token={'access_token' in body}")

# 5. Wrong password -> 401
code, body = post('/auth/login', {'email': 'test@koinok.dev', 'password': 'wrong'})
ok = code == 401
results.append(f"[{'PASS' if ok else 'FAIL'}] POST /auth/login (bad pw) = {code}")

for r in results:
    print(r)

all_pass = all(r.startswith('[PASS]') for r in results)
print()
print('ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED')
