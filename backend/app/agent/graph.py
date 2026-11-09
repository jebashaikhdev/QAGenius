from langgraph.graph import StateGraph, START, END

from app.agent.state import QAState
from app.agent.nodes import (
    analyze_node,
    generate_node,
    review_node,
    decide_node,
    improve_node
)

def route_after_decision(state: QAState):
    if state["status"] == "approved":
        return "complete"
    
    if state["iteration"] < 2:
        return "improve"
    
    return "max_iterations_reached"

# Create the graph
builder = StateGraph(QAState)

# Register nodes
builder.add_node("analyze", analyze_node)
builder.add_node("generate", generate_node)
builder.add_node("review", review_node)
builder.add_node("decide", decide_node)
builder.add_node("improve", improve_node)

# Define workflow sequence
builder.add_edge(START, "analyze")
builder.add_edge("analyze", "generate")
builder.add_edge("generate", "review")
builder.add_edge("review","decide")

builder.add_conditional_edges(
    "decide",
    route_after_decision,
    {
        "complete": END,
        "improve": "improve",
        "max_iterations_reached": END
    }
)

# After improvement, review the test cases again
builder.add_edge("improve", "review")

# Compile the graph
qa_workflow = builder.compile()

def run_qa_workflow(requirement: str):
    initial_state = {
        "requirement": requirement,
        "analysis": "",
        "test_cases": "",
        "review": "",
        "iteration": 0,
        "status": "in_progress"
    } 
    
    return qa_workflow.invoke(initial_state)
