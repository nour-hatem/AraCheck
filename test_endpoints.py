# -*- coding: utf-8 -*-
"""
test_endpoints.py
Quick smoke tests for all AraCheck backend endpoints.
"""
import urllib.request
import json
import sys
import io

# Force UTF-8 output to handle Arabic text in API responses
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = "http://127.0.0.1:8001"
results = []


def test(name, endpoint, method="GET", body=None, headers=None, expect_status=200):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)

    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(endpoint, data=data, headers=h, method=method)

    try:
        res = urllib.request.urlopen(req)
        got_status = res.status
        resp_body = json.loads(res.read())
    except urllib.error.HTTPError as e:
        got_status = e.code
        try:
            resp_body = json.loads(e.read())
        except Exception:
            resp_body = {}
    except Exception as e:
        results.append((name, "FAIL", f"Connection error: {e}", None, None))
        return

    ok = got_status == expect_status
    results.append((name, "PASS" if ok else "FAIL", resp_body, expect_status, got_status))


# ── Tests ────────────────────────────────────────────────────────────────────

test("GET  /health", f"{BASE}/health", expect_status=200)

test("GET  /flags", f"{BASE}/flags", expect_status=200)

test("POST /chat  - empty message (expect 422)",
     f"{BASE}/chat", method="POST",
     body={"message": ""},
     expect_status=422)

test("POST /chat  - too long message (expect 422)",
     f"{BASE}/chat", method="POST",
     body={"message": "x" * 5000},
     expect_status=422)

test("PATCH /flags - no admin key (expect 401)",
     f"{BASE}/flags/ENABLE_VOICE_INPUT", method="PATCH",
     body={"enabled": False},
     expect_status=401)

test("PATCH /flags - correct key, disable voice",
     f"{BASE}/flags/ENABLE_VOICE_INPUT", method="PATCH",
     body={"enabled": False},
     headers={"x-admin-key": "aracheck-admin-2026"},
     expect_status=200)

test("PATCH /flags - correct key, re-enable voice",
     f"{BASE}/flags/ENABLE_VOICE_INPUT", method="PATCH",
     body={"enabled": True},
     headers={"x-admin-key": "aracheck-admin-2026"},
     expect_status=200)

test("PATCH /flags - nonexistent flag (expect 404)",
     f"{BASE}/flags/NONEXISTENT_FLAG", method="PATCH",
     body={"enabled": True},
     headers={"x-admin-key": "aracheck-admin-2026"},
     expect_status=404)

# ── Report ───────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("  AraCheck Backend -- Endpoint Test Results")
print("=" * 70)

passed = 0
for row in results:
    name = row[0]
    status = row[1]
    detail = row[2]
    exp = row[3]
    got = row[4]

    icon = "[PASS]" if status == "PASS" else "[FAIL]"
    if status == "PASS":
        passed += 1

    print(f"  {icon}  {name}")
    if status == "FAIL":
        print(f"         Expected: {exp}  |  Got: {got}")
        print(f"         Response: {str(detail)[:120]}")
    else:
        # Show short snippet of response
        snippet = str(detail)[:80]
        print(f"         -> {snippet}")
    print()

total = len(results)
print(f"  Result: {passed}/{total} tests passed")
print("=" * 70)

sys.exit(0 if passed == total else 1)
