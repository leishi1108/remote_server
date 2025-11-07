from typing import Optional, Callable, Any, List

from langgraph.graph import StateGraph
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage, ToolMessage, FunctionMessage


class SimpleGraphBuilder:
    """LangGraph状态图构建器"""

    def __init__(self):
        self.messages = []
        self.builder = StateGraph(MessagesState)
        self._setup_nodes()
        self._setup_edges()
        self.graph = self.compile()

    def _setup_nodes(self):
        """设置图节点"""
        raise NotImplementedError

    def _setup_edges(self):
        """设置图边和条件路由"""
        raise NotImplementedError

    def compile(self):
        """编译图"""
        return self.builder.compile()



def fallback_node(state: MessagesState):
    """回退节点：当不需要特殊代理时使用"""
    state["messages"] =[]
    return {"messages": [AIMessage(content="我是通用助手，请问有什么可以帮助您的？")]}


def ensure_message_format(messages) -> List[BaseMessage]:
    """确保消息列表中的每个消息都是正确的消息对象格式"""
    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            msg_type = msg.get("type")
            content = msg.get("content", "")
            additional_kwargs = msg.get("additional_kwargs") or {}
            name = msg.get("name")
            tool_call_id = msg.get("tool_call_id")
            tool_calls = msg.get("tool_calls")

            if msg_type == "human":
                formatted_messages.append(HumanMessage(content=content, additional_kwargs=additional_kwargs))
            elif msg_type == "ai":
                # 尝试显式传入 tool_calls，以便代理识别到先前的工具调用上下文
                if tool_calls is not None:
                    formatted_messages.append(
                        AIMessage(content=content, additional_kwargs=additional_kwargs, tool_calls=tool_calls))
                else:
                    formatted_messages.append(AIMessage(content=content, additional_kwargs=additional_kwargs))
            elif msg_type == "system":
                formatted_messages.append(SystemMessage(content=content, additional_kwargs=additional_kwargs))
            elif msg_type == "tool":
                # 需要 tool_call_id 才能重建工具消息
                formatted_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=name,
                                                      additional_kwargs=additional_kwargs))
            elif msg_type == "function":
                # 旧版函数消息兼容
                formatted_messages.append(FunctionMessage(content=content, name=name))
            else:
                # 未识别类型，保底作为人类消息
                formatted_messages.append(HumanMessage(content=content, additional_kwargs=additional_kwargs))
        else:
            # 已经是消息对象，直接添加
            formatted_messages.append(msg)

    return formatted_messages