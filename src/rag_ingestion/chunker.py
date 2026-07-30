"""
chunker.py
----------

Owner: Member 2 (RAG Ingestion)

ملاحظة مهمة:
- الـ dataset الحالي (MedRAG/pubmed) عبارة عن abstracts علمية قصيرة، أصلًا
  مقسمة ومنضفة من المصدر، فمش محتاجة تقسيم إضافي. الدالة chunk_text تحت
  دلوقتي بترجع النص زي ما هو (pass-through).
- الدالة موجودة وجاهزة عشان لو الفريق قرر يضيف كتب PDF كاملة بعدين
  (زي المطلوب أصلًا في الخطة)، هنستخدمها فعليًا من غير ما نغير باقي الكود.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000      
CHUNK_OVERLAP = 150   


def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_text(text: str) -> list[str]:
   
    if len(text) <= CHUNK_SIZE:
        return [text]

    splitter = get_splitter()
    return splitter.split_text(text)


def chunk_pdf_book(raw_text: str, source_name: str) -> list[dict]:
   
    chunks = chunk_text(raw_text)
    return [{"text": c, "source": source_name} for c in chunks]
