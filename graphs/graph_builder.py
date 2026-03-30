"""
Builder pattern applied to constructing LangGraph StateGraphs.
This satisfies the assignment requirement:
'Teams are required to apply the builder pattern to design and implement these.'
"""

from abc import ABC, abstractmethod
from langgraph.graph import StateGraph, END


class TradingGraphBuilder(ABC):
    """Abstract builder interface for trading state graphs."""

    @abstractmethod
    def set_research_node(self, node_fn) -> "TradingGraphBuilder":
        ...

    @abstractmethod
    def set_trade_node(self, node_fn) -> "TradingGraphBuilder":
        ...

    @abstractmethod
    def set_conditional_edges(self) -> "TradingGraphBuilder":
        ...

    @abstractmethod
    def build(self):
        ...


class ConventionalGraphBuilder(TradingGraphBuilder):
    """Builds the conventional (one-shot) trading graph.
    START -> research -> should_trade? -> trade -> update -> END
    """

    def __init__(self, state_schema):
        self.graph = StateGraph(state_schema)
        self._research_fn = None
        self._trade_fn = None
        self._update_fn = None
        self._should_trade_fn = None

    def set_research_node(self, node_fn) -> "ConventionalGraphBuilder":
        self._research_fn = node_fn
        self.graph.add_node("research", node_fn)
        return self

    def set_trade_node(self, node_fn) -> "ConventionalGraphBuilder":
        self._trade_fn = node_fn
        self.graph.add_node("trade", node_fn)
        return self

    def set_update_node(self, node_fn) -> "ConventionalGraphBuilder":
        self._update_fn = node_fn
        self.graph.add_node("update_portfolio", node_fn)
        return self

    def set_conditional_edges(self, should_trade_fn=None) -> "ConventionalGraphBuilder":
        self._should_trade_fn = should_trade_fn
        # START -> research
        self.graph.set_entry_point("research")
        # research -> conditional -> trade or END
        self.graph.add_conditional_edges(
            "research",
            should_trade_fn,
            {"trade": "trade", "end": END},
        )
        # trade -> update_portfolio
        self.graph.add_edge("trade", "update_portfolio")
        # update_portfolio -> END
        self.graph.add_edge("update_portfolio", END)
        return self

    def build(self):
        return self.graph.compile()


class IncrementalGraphBuilder(TradingGraphBuilder):
    """Builds the iterative incremental trading graph with loop.
    START -> research -> should_trade? -> incremental_trade -> assess -> should_continue? -> loop or END
    """

    def __init__(self, state_schema):
        self.graph = StateGraph(state_schema)
        self._research_fn = None
        self._trade_fn = None
        self._assess_fn = None

    def set_research_node(self, node_fn) -> "IncrementalGraphBuilder":
        self._research_fn = node_fn
        self.graph.add_node("research", node_fn)
        return self

    def set_trade_node(self, node_fn) -> "IncrementalGraphBuilder":
        self._trade_fn = node_fn
        self.graph.add_node("incremental_trade", node_fn)
        return self

    def set_assess_node(self, node_fn) -> "IncrementalGraphBuilder":
        self._assess_fn = node_fn
        self.graph.add_node("assess", node_fn)
        return self

    def set_conditional_edges(self, should_trade_fn=None, should_continue_fn=None) -> "IncrementalGraphBuilder":
        # START -> research
        self.graph.set_entry_point("research")
        # research -> conditional -> incremental_trade or END
        self.graph.add_conditional_edges(
            "research",
            should_trade_fn,
            {"trade": "incremental_trade", "end": END},
        )
        # incremental_trade -> assess
        self.graph.add_edge("incremental_trade", "assess")
        # assess -> conditional -> loop back or END
        self.graph.add_conditional_edges(
            "assess",
            should_continue_fn,
            {"continue": "incremental_trade", "end": END},
        )
        return self

    def build(self):
        return self.graph.compile()


class GraphDirector:
    """Director that uses a builder to construct the graph."""

    def __init__(self, builder: TradingGraphBuilder):
        self.builder = builder
