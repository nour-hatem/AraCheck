"""Owner: Member 5.
Medical image understanding helpers built on HuggingFace InferenceClient.
The model is used only to extract visible text and objective visual cues.
It must never infer a diagnosis or a final medical conclusion.
"""
from __future__ import annotations
import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

VISION_LANGUAGE_MODEL: str = "zai-org/GLM-4.5V"
load_dotenv()


def _image_to_data_url(image_path: Path) -> str:
    """Read an image file and convert it to a data URL for multimodal chat."""
    image_bytes = image_path.read_bytes()
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_image}"
def _extract_json_object(raw_text: str) -> dict[str, str] | None:
    """Parse the first JSON object from model output if the response is noisy."""
    candidate_text = raw_text.strip()
    # Strip markdown code fences if present (```json ... ```)
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate_text, flags=re.DOTALL)
    if fence_match:
        candidate_text = fence_match.group(1)

    def _try_parse(text: str) -> dict | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    parsed = _try_parse(candidate_text)
    if parsed is None:
        # Model sometimes emits raw (unescaped) newlines inside string
        # values, which breaks strict JSON parsing. Escape newlines that
        # appear inside quoted string spans before retrying.
        def _escape_newlines_in_strings(text: str) -> str:
            result_chars: list[str] = []
            inside_string = False
            i = 0
            while i < len(text):
                char = text[i]
                if char == '"' and (i == 0 or text[i - 1] != "\\"):
                    inside_string = not inside_string
                    result_chars.append(char)
                elif inside_string and char == "\n":
                    result_chars.append("\\n")
                else:
                    result_chars.append(char)
                i += 1
            return "".join(result_chars)

        parsed = _try_parse(_escape_newlines_in_strings(candidate_text))

    if parsed is None:
        match = re.search(r"\{.*\}", candidate_text, flags=re.DOTALL)
        if not match:
            return None
        parsed = _try_parse(match.group(0))

    if not isinstance(parsed, dict):
        return None

    extracted_text = parsed.get("extracted_text", "")
    visual_description = parsed.get("visual_description", "")

    return {
        "extracted_text": str(extracted_text).strip(),
        "visual_description": str(visual_description).strip(),
    }
def _extract_message_text(response: object) -> str:
    """Extract assistant text from a HuggingFace chat completion response."""
    choices = getattr(response, "choices", None)
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            collected_parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    collected_parts.append(str(part["text"]))
            if collected_parts:
                return "".join(collected_parts)
        if content is not None:
            return str(content)

    return str(response)
def analyze_medical_image(image_path: str, max_tokens: int = 2048) -> dict[str, str | None]:
    """Analyze a medical image and return text and visual description only.

    The function extracts any visible written text and a neutral visual
    description, then returns an error message instead of raising if the
    image is invalid or the HuggingFace request fails.
    """
    result: dict[str, str | None] = {
        "extracted_text": "",
        "visual_description": "",
        "error": None,
    }
    image_file = Path(image_path)
    if not image_file.exists():
        result["error"] = f"Image file not found: {image_path}"
        return result
    try:
        image_data_url = _image_to_data_url(image_file)
    except OSError as exc:
        result["error"] = f"Could not read image file: {exc}"
        return result
    hf_token = os.getenv("HF_TOKEN")
    client = InferenceClient(model=VISION_LANGUAGE_MODEL, token=hf_token, timeout=60.0)

    prompt = (
        "Analyze the attached medical image and return ONLY valid JSON with the "
        "following keys: extracted_text, visual_description.\n\n"
        "Rules:\n"
        "- Extract any clearly legible text from the image exactly as written when possible.\n"
        "- Provide a neutral visual description of visible elements only.\n"
        "- Do not diagnose, infer disease, or draw any final medical conclusion.\n"
        "- If text is unreadable, return an empty string for extracted_text.\n"
        "- If no meaningful visual findings are visible, keep visual_description concise.\n"
    )
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "You are a careful medical image assistant. "
                        "You extract visible text and describe appearance objectively. "
                        "You never provide diagnosis or medical interpretation."
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        },
    ]

    try:
        response = client.chat_completion(messages=messages, max_tokens=max_tokens, temperature=0.0)
    except Exception as exc:
        result["error"] = f"HuggingFace image analysis failed: {exc}"
        return result

    raw_text = _extract_message_text(response)

    parsed = _extract_json_object(raw_text)
    if parsed is None:
        result["error"] = "Model response was not valid JSON."
        return result
    result["extracted_text"] = parsed["extracted_text"]
    result["visual_description"] = parsed["visual_description"]
    return result