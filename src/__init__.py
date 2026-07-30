"""
src/__init__.py
---------------
AraCheck source package.

This package contains all backend application modules:
  - src.main          FastAPI application entry point
  - src.settings      Application settings and feature flags
  - src.api           API route definitions
  - src.core          Core logic (context management, validation)
  - src.schemas       Pydantic request/response models
  - src.services      LLM, RAG, Qdrant, and Voice service wrappers
  - src.agent_pipeline   LangGraph agent pipeline
  - src.rag_ingestion    PDF ingestion pipeline
  - src.rag_retrieval    Vector retrieval and reranking
  - src.stt_pipeline     Speech-to-text pipeline
  - src.data_pipeline    Dataset building utilities
  - src.llm_finetuning   LLM fine-tuning utilities
"""
