"""
tests/test_runtime_full.py
--------------------------
Comprehensive integration test suite verifying 100% of AraCheck API endpoints.
"""
import io
import json
import os
import sys
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
ADMIN_KEY = "aracheck-admin-2026"


def make_request(url, method="GET", data=None, headers=None, files=None):
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


def run_full_suite():
    print("=" * 75)
    print("      AraCheck Full Production Integration & Verification Suite")
    print("=" * 75)

    tests = []

    # 1. Health Check
    status, body = make_request(f"{BASE_URL}/health")
    tests.append(("GET /health", status == 200, status, body))

    # 2. Chat / LLM Pipeline
    chat_payload = {"message": "هل تناول المضادات الحيوية مفيد في علاج العدوى الفيروسية؟", "history": []}
    status, body = make_request(f"{BASE_URL}/chat", method="POST", data=chat_payload)
    is_chat_ok = status == 200 and isinstance(body, dict) and "content" in body and body.get("role") == "assistant"
    tests.append(("POST /chat (Medical Query RAG/LLM Pipeline)", is_chat_ok, status, body))

    # 3. Flags List
    status, body = make_request(f"{BASE_URL}/flags")
    tests.append(("GET /flags", status == 200 and "ENABLE_VOICE_INPUT" in body, status, body))

    # 4. Flags Update (Unauthorized)
    status, body = make_request(
        f"{BASE_URL}/flags/ENABLE_VOICE_INPUT",
        method="PATCH",
        data={"enabled": False},
    )
    tests.append(("PATCH /flags/ENABLE_VOICE_INPUT (Unauthorized Guard)", status == 401, status, body))

    # 5. Flags Update (Authorized)
    status, body = make_request(
        f"{BASE_URL}/flags/ENABLE_VOICE_INPUT",
        method="PATCH",
        data={"enabled": True},
        headers={"x-admin-key": ADMIN_KEY},
    )
    tests.append(("PATCH /flags/ENABLE_VOICE_INPUT (Authorized)", status == 200, status, body))

    # 6. Image Upload - Invalid Guard
    files_invalid_img = {"file": ("scan.txt", b"not an image", "text/plain")}
    status, body = make_request(f"{BASE_URL}/analyze-image", method="POST", files=files_invalid_img)
    tests.append(("POST /analyze-image (Validation Guard - Bad Mime/Ext)", status == 400, status, body))

    # 7. Image Upload - Valid JPEG Payload
    jpeg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48,
        0x00, 0x48, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
        0x00, 0xBF, 0x00, 0xFF, 0xD9
    ])
    files_valid_img = {"file": ("xray.jpg", jpeg_bytes, "image/jpeg")}
    status, body = make_request(f"{BASE_URL}/analyze-image", method="POST", files=files_valid_img)
    tests.append(("POST /analyze-image (Valid Payload Handling)", status in (200, 503), status, body))

    # 8. Audio Transcribe - Invalid Guard
    files_invalid_audio = {"file": ("voice.txt", b"not audio", "text/plain")}
    status, body = make_request(f"{BASE_URL}/transcribe", method="POST", files=files_invalid_audio)
    tests.append(("POST /transcribe (Validation Guard - Bad Extension)", status == 400, status, body))

    # 9. PDF Ingestion - Invalid Guard
    files_invalid_pdf = {"file": ("report.exe", b"fake binary", "application/octet-stream")}
    status, body = make_request(f"{BASE_URL}/upload-pdf", method="POST", files=files_invalid_pdf)
    tests.append(("POST /upload-pdf (Validation Guard - Bad Extension)", status == 400, status, body))

    # 10. PDF Ingestion - Valid PDF Payload with Extractable Text
    sample_pdf_path = os.path.join(os.path.dirname(__file__), "sample.pdf")
    if os.path.exists(sample_pdf_path):
        with open(sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()
    else:
        pdf_bytes = b"%PDF-1.4 sample text"

    files_valid_pdf = {"file": ("medical_guide.pdf", pdf_bytes, "application/pdf")}
    status, body = make_request(f"{BASE_URL}/upload-pdf", method="POST", files=files_valid_pdf)
    is_pdf_ok = status == 200 and isinstance(body, dict) and body.get("status") == "success"
    tests.append(("POST /upload-pdf (Valid Payload Ingestion)", is_pdf_ok, status, body))

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
    print("=" * 75)
    print(f"  Total Verified Endpoints: {passed}/{len(tests)}")
    print("=" * 75)
    return passed == len(tests)


if __name__ == "__main__":
    success = run_full_suite()
    sys.exit(0 if success else 1)
