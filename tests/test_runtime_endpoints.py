"""
tests/test_runtime_endpoints.py
--------------------------------
Integration test suite for AraCheck API endpoints.
Connects to the running FastAPI server on http://127.0.0.1:8000.
"""
import io
import json
import sys
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = "aracheck-admin-2026"


def make_request(url, method="GET", data=None, headers=None, files=None):
    """Utility helper for raw HTTP requests."""
    req_headers = headers or {}
    body_bytes = None

    if files:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        body_parts = []
        for field_name, (filename, content, mime_type) in files.items():
            body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8")
            )
            body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
            body_parts.append(content if isinstance(content, bytes) else content.encode("utf-8"))
            body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body_bytes = b"".join(body_parts)
    elif data is not None:
        req_headers["Content-Type"] = "application/json"
        body_bytes = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            response_text = resp.read().decode("utf-8")
            try:
                parsed_json = json.loads(response_text)
            except Exception:
                parsed_json = response_text
            return status_code, parsed_json
    except urllib.error.HTTPError as err:
        error_text = err.read().decode("utf-8")
        try:
            parsed_json = json.loads(error_text)
        except Exception:
            parsed_json = error_text
        return err.code, parsed_json
    except Exception as exc:
        return 500, str(exc)


def run_all_tests():
    print("=" * 70)
    print("           AraCheck Runtime Integration Test Suite")
    print("=" * 70)

    tests = []

    # 1. Health Check
    status, body = make_request(f"{BASE_URL}/health")
    tests.append(("GET /health", status == 200, status, body))

    # 2. Chat Endpoint
    chat_payload = {"message": "مرحبا، ما هي أعراض الصداع؟", "history": []}
    status, body = make_request(f"{BASE_URL}/chat", method="POST", data=chat_payload)
    is_chat_ok = status == 200 and isinstance(body, dict) and "content" in body
    tests.append(("POST /chat (valid query)", is_chat_ok, status, body))

    # 3. Chat Validation Error (empty message)
    status, body = make_request(f"{BASE_URL}/chat", method="POST", data={"message": ""})
    tests.append(("POST /chat (empty query -> 422)", status == 422, status, body))

    # 4. Flags List
    status, body = make_request(f"{BASE_URL}/flags")
    is_flags_ok = status == 200 and isinstance(body, dict) and "ENABLE_VOICE_INPUT" in body
    tests.append(("GET /flags", is_flags_ok, status, body))

    # 5. Flag Update Without Auth Key (401)
    status, body = make_request(
        f"{BASE_URL}/flags/ENABLE_VOICE_INPUT",
        method="PATCH",
        data={"enabled": False},
    )
    tests.append(("PATCH /flags (no admin key -> 401)", status == 401, status, body))

    # 6. Flag Update With Valid Admin Key
    status, body = make_request(
        f"{BASE_URL}/flags/ENABLE_VOICE_INPUT",
        method="PATCH",
        data={"enabled": True},
        headers={"x-admin-key": ADMIN_KEY},
    )
    tests.append(("PATCH /flags (with admin key -> 200)", status == 200, status, body))

    # 7. Audio Validation Error (invalid extension)
    files_invalid_audio = {
        "file": ("test.txt", b"invalid audio content", "text/plain")
    }
    status, body = make_request(f"{BASE_URL}/transcribe", method="POST", files=files_invalid_audio)
    tests.append(("POST /transcribe (invalid file extension -> 400)", status == 400, status, body))

    # 8. Image Validation Error (invalid file type)
    files_invalid_image = {
        "file": ("test.txt", b"not an image", "text/plain")
    }
    status, body = make_request(f"{BASE_URL}/analyze-image", method="POST", files=files_invalid_image)
    tests.append(("POST /analyze-image (invalid image format -> 400)", status == 400, status, body))

    # 9. PDF Validation Error (invalid extension)
    files_invalid_pdf = {
        "file": ("test.exe", b"not a pdf", "application/octet-stream")
    }
    status, body = make_request(f"{BASE_URL}/upload-pdf", method="POST", files=files_invalid_pdf)
    tests.append(("POST /upload-pdf (invalid pdf format -> 400)", status == 400, status, body))

    # Output Summary
    print()
    passed = 0
    for name, success, code, res in tests:
        mark = "[PASS]" if success else "[FAIL]"
        if success:
            passed += 1
        print(f"  {mark} {name} (Status: {code})")
        if not success:
            print(f"         Detail: {str(res)[:120]}")

    print()
    print("=" * 70)
    print(f"  Passed: {passed}/{len(tests)} tests")
    print("=" * 70)

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
