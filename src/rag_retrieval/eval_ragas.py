"""
eval_ragas.py

M3 Retrieval Evaluation Suite for AraDoc RAG pipeline.
Evaluates vector retrieval + cross-encoder reranking over an expanded 12-question
medical test set covering symptom, cause/mechanism, treatment, and complication categories.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running script directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.rag_retrieval.retriever import search


TEST_SET = [
    # Symptom Questions
    {
        "question": "What are the symptoms of type 2 diabetes?",
        "keywords": ["symptom", "polydipsia", "thirst", "glucose", "polyuria"],
    },
    {
        "question": "How does diabetic ketoacidosis present in children?",
        "keywords": ["ketoacidosis", "child", "children", "abdomen", "acidosis"],
    },
    {
        "question": "What are the early signs of hypoglycemia in diabetics?",
        "keywords": ["hypoglycaemia", "hypoglycemia", "sweating", "tremor", "glucose"],
    },
    # Cause / Mechanism Questions
    {
        "question": "What causes type 1 diabetes?",
        "keywords": ["autoimmune", "insulin", "hla", "antibody", "autoimmunity"],
    },
    {
        "question": "What is the physiological cause of diabetic gastroparesis?",
        "keywords": ["gastric", "emptying", "vagus", "neuropathy", "gastroparesis"],
    },
    {
        "question": "How does insulin resistance develop in human adipocytes?",
        "keywords": ["adipose", "adipocyte", "insulin", "receptor", "glucose"],
    },
    # Treatment Questions
    {
        "question": "What is the efficacy of continuous insulin infusion?",
        "keywords": ["infusion", "pump", "injection", "glycemic", "control"],
    },
    {
        "question": "How is diabetic ketoacidosis managed with fluid therapy?",
        "keywords": ["saline", "potassium", "electrolyte", "infusion", "therapy"],
    },
    {
        "question": "What are the effects of chlorpropamide on blood glucose?",
        "keywords": ["chlorpropamide", "hypoglycemic", "sulfonylurea", "secretion"],
    },
    # Complication Questions
    {
        "question": "What are the signs of diabetic foot retinopathy?",
        "keywords": ["foot", "retinopathy", "lesion", "eye", "retina"],
    },
    {
        "question": "What is diabetic osteoarthropathy?",
        "keywords": ["osteoarthropathy", "bone", "joint", "roentgen", "arthropathy"],
    },
    {
        "question": "What structural changes occur in diabetic nephropathy?",
        "keywords": ["glomerular", "basement", "membrane", "kidney", "nephropathy"],
    },
]


def evaluate_retrieval():
    total_questions = len(TEST_SET)
    total_precision = 0.0
    total_rerank_score = 0.0

    print("=" * 70)
    print("AraDoc RAG Retrieval Evaluation Suite (M3) - 12 Question Baseline")
    print("=" * 70)

    for idx, item in enumerate(TEST_SET, start=1):
        q = item["question"]
        keywords = [k.lower() for k in item["keywords"]]
        hits = search(q)

        print(f"\n[{idx}] Question: '{q}'")
        print(f"    Expected Keywords : {item['keywords']}")

        hits_with_keyword = 0
        rerank_scores = []

        for rank, hit in enumerate(hits, start=1):
            text_lower = hit.get("text", "").lower()
            matched = [kw for kw in keywords if kw in text_lower]
            if matched:
                hits_with_keyword += 1
            rerank_scores.append(hit.get("rerank_score", 0.0))

            matched_str = f"matched: {matched}" if matched else "matched: none"
            title = hit.get("title", "(no title)")
            vec_score = hit.get("score", 0.0)
            rerank_score = hit.get("rerank_score", 0.0)
            print(
                f"    Hit {rank}: {title} | rerank={rerank_score:.4f} | vec={vec_score:.4f} | {matched_str}"
            )

        precision = hits_with_keyword / len(hits) if hits else 0.0
        avg_rerank = sum(rerank_scores) / len(rerank_scores) if rerank_scores else 0.0

        total_precision += precision
        total_rerank_score += avg_rerank

        print(f"    Keyword Precision : {hits_with_keyword}/{len(hits)} ({precision * 100:.1f}%)")
        print(f"    Avg Rerank Score  : {avg_rerank:.4f}")

    overall_avg_precision = total_precision / total_questions
    overall_avg_rerank = total_rerank_score / total_questions

    print("\n" + "=" * 70)
    print("OVERALL EVALUATION SUMMARY (12-Question Baseline)")
    print("=" * 70)
    print(f"Average Keyword Precision : {overall_avg_precision * 100:.1f}%")
    print(f"Average Rerank Score      : {overall_avg_rerank:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    evaluate_retrieval()

