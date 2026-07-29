from src.agent_pipeline.prompts import build_system_prompt
from src.agent_pipeline.context_builder import build_context
from src.agent_pipeline.image_understanding import analyze_medical_image

print("=== Test 1: Prompts ===")
print(build_system_prompt(is_confident=True))

print("\n=== Test 2: Context Builder ===")
result = build_context(
    query="عندي صداع من يومين",
    chat_history=[{"role": "user", "content": "مرحبا"}],
    rag_context="[1] Headache causes (PMID: 12345)\nHeadaches can result from...",
)
print(result)

print("\n=== Test 3: Image Understanding - Handwritten Prescription ===")
result = analyze_medical_image("images/img.png")
print(result)

print("\n=== Test 4: Image Understanding - Medication Label ===")
result = analyze_medical_image("images/img_1.png")
print(result)

print("\n=== Test 5: Image Understanding - Chest X-ray ===")
result = analyze_medical_image("images/img_2.png")
print(result)