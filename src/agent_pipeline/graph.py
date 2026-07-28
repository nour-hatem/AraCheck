"""
graph.py
--------
Owner: Member 4 (Agent & Web Search & Voice)
"""
from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from src.agent_pipeline.tools.rag_tool import format_rag_context, is_confident, rag_search
from src.agent_pipeline.tools.web_search import format_web_context, web_search

try:
    from src.llm_finetuning.inference import generate_answer
except ImportError:
    from src.agent_pipeline.llm_stub import generate_answer

try:
    from src.agent_pipeline.prompts import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = (
        "You are AraDoc, a medical AI assistant. Answer clearly and cite "
        "sources as [1], [2] when context is provided."
    )


class AgentState(TypedDict):
    query: str
    answer: Optional[str]
    source: Optional[str]
    context: Optional[str]


def llm_node(state: AgentState) -> AgentState:
    result = generate_answer(state["query"])

    if result.get("confident"):
        state["answer"] = result["answer"]
        state["source"] = "llm"
        state["context"] = None

    return state


def route_after_llm(state: AgentState) -> str:
    return END if state.get("answer") else "rag_node"


def rag_node(state: AgentState) -> AgentState:
    hits = rag_search(state["query"])

    if is_confident(hits):
        context = format_rag_context(hits)
        result = generate_answer(state["query"], context=context)
        state["answer"] = result["answer"]
        state["source"] = "rag"
        state["context"] = context

    return state


def route_after_rag(state: AgentState) -> str:
    return END if state.get("answer") else "web_node"


def web_node(state: AgentState) -> AgentState:
    results = web_search(state["query"])
    context = format_web_context(results)
    result = generate_answer(state["query"], context=context)

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


def ask(query: str) -> AgentState:
    agent = get_agent()
    initial_state: AgentState = {
        "query": query,
        "answer": None,
        "source": None,
        "context": None,
    }
    return agent.invoke(initial_state)


if __name__ == "__main__":
    result = ask("What are the symptoms of type 2 diabetes?")
    print("Source:", result["source"])
    print("Answer:", result["answer"])
