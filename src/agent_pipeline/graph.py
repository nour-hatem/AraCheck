"""
graph.py
--------
LangGraph agent workflow definition for AraCheck medical QA.
"""
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.agent_pipeline.tools.rag_tool import get_medical_context
from src.agent_pipeline.tools.web_search import format_web_context, web_search

from src.agent_pipeline.llm_stub import generate_answer as _stub_generate

try:
    from src.llm_finetuning.inference import generate_answer as _inference_generate
    _has_inference = True
except ImportError:
    _has_inference = False


def generate_answer(query, history=None, context=None, system_prompt=None, max_tokens=1024):
    """Primary LLM dispatcher with fallback handler."""
    if _has_inference:
        try:
            result = _inference_generate(
                query, history=history, context=context,
                system_prompt=system_prompt, max_tokens=max_tokens
            )
            if result.get("answer"):
                return result
        except Exception:
            pass
    return _stub_generate(
        query, history=history, context=context,
        system_prompt=system_prompt, max_tokens=max_tokens
    )


try:
    from src.agent_pipeline.prompts import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = (
        "You are AraDoc, a medical AI assistant. Answer clearly and cite "
        "sources as [1], [2] when context is provided."
    )


class AgentState(TypedDict):
    query: str
    history: Optional[list]
    answer: Optional[str]
    source: Optional[str]
    context: Optional[str]
    max_tokens: Optional[int]


def llm_node(state: AgentState) -> AgentState:
    max_tok = state.get("max_tokens") or 1024
    history = state.get("history")
    result = generate_answer(
        state["query"],
        history=history,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=max_tok
    )

    if result.get("confident"):
        state["answer"] = result["answer"]
        state["source"] = "llm"
        state["context"] = None

    return state


def route_after_llm(state: AgentState) -> str:
    return END if state.get("answer") else "rag_node"


def _find_medical_topic(history: list) -> Optional[str]:
    if not history:
        return None
    from src.agent_pipeline.llm_stub import _is_greeting
    for m in history:
        if m.get("role") == "user" or m.get("sender") == "user":
            content = (m.get("content") or m.get("text") or "").strip()
            if content and not _is_greeting(content):
                return content
    return None


def rag_node(state: AgentState) -> AgentState:
    history = state.get("history")
    query = state["query"]
    effective_query = query

    # Contextual query expansion: attach main initial medical topic from history for follow-up questions
    if history and len(query.split()) < 8:
        main_topic = _find_medical_topic(history)
        if main_topic:
            effective_query = f"بالنسبة لموضوع ({main_topic}): {query}"

    context = get_medical_context(effective_query)
    max_tok = state.get("max_tokens") or 1024

    if context:
        result = generate_answer(
            effective_query,
            history=history,
            context=context,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=max_tok
        )
        state["answer"] = result["answer"]
        state["source"] = "rag"
        state["context"] = context

    return state


def route_after_rag(state: AgentState) -> str:
    return END if state.get("answer") else "web_node"


def web_node(state: AgentState) -> AgentState:
    history = state.get("history")
    query = state["query"]
    effective_query = query

    if history and len(query.split()) < 8:
        main_topic = _find_medical_topic(history)
        if main_topic:
            effective_query = f"بالنسبة لموضوع ({main_topic}): {query}"

    results = web_search(effective_query)
    context = format_web_context(results)
    max_tok = state.get("max_tokens") or 1024
    result = generate_answer(
        effective_query,
        history=history,
        context=context,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=max_tok
    )

    state["answer"] = result["answer"] or "No reliable answer could be found."
    state["source"] = "web"
    state["context"] = context

    return state


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("llm_node", llm_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("web_node", web_node)

    graph.set_entry_point("llm_node")

    graph.add_conditional_edges("llm_node", route_after_llm, {
        END: END,
        "rag_node": "rag_node",
    })

    graph.add_conditional_edges("rag_node", route_after_rag, {
        END: END,
        "web_node": "web_node",
    })

    graph.add_edge("web_node", END)

    return graph.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_graph()
    return _agent


def ask(query: str, history: list = None, max_tokens: int = 1024) -> AgentState:
    agent = get_agent()
    initial_state: AgentState = {
        "query": query,
        "history": history or [],
        "answer": None,
        "source": None,
        "context": None,
        "max_tokens": max_tokens,
    }
    return agent.invoke(initial_state)


if __name__ == "__main__":
    result = ask("What are the symptoms of type 2 diabetes?")
    print("Source:", result["source"])
    print("Answer:", result["answer"])
