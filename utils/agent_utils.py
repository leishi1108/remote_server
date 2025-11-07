import asyncio
import json
from typing import Optional, Callable, Any, List
from langgraph.graph import MessagesState
from utils.graph_utils import ensure_message_format
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage, ToolMessage, FunctionMessage


class SimpleAgentRunner:
    def __init__(self, agent):
        self.agent = agent

    def __run__(self, state: MessagesState):
        agent_name = state.get("current_agent")

        # 消息格式化
        messages = ensure_message_format(state.get("messages", []))
        if not messages:
            return {}
        client_token = None

        try:
            print(f"=== 调用 Agent ===")
            print(f"传入消息数量: {len(messages)}")

            # 构建输入
            agent_input = {"messages": messages}
            print(f"Agent 输入: {agent_input}")

            # 使用异步调用，因为 MCP 工具需要异步
            print("调用 Agent (异步)...")
            try:
                response = asyncio.run(self.agent.ainvoke(agent_input))
                print("异步调用成功")
            except Exception as async_error:
                print(f"异步调用失败: {async_error}")
                print("尝试同步调用...")
                response = self.agent.invoke(agent_input)
                print("同步调用成功")

            print(f"Agent 响应类型: {type(response)}")
            print(f"Agent 响应内容: {response}")

            # 检查响应中是否包含工具调用信息，前端打印
            if isinstance(response, dict):
                print(f"响应键: {list(response.keys())}")
                if "intermediate_steps" in response:
                    print(f"中间步骤: {response['intermediate_steps']}")
                    # 检查中间步骤中的工具调用
                    for step in response.get('intermediate_steps', []):
                        if len(step) >= 2:
                            action = step[0]
                            observation = step[1]
                            print(f"  动作: {action}")
                            print(f"  观察: {observation}")
                if "output" in response:
                    print(f"输出: {response['output']}")
                if "messages" in response:
                    print(f"消息数量: {len(response['messages'])}")
                    # 检查消息中是否包含工具调用
                    for i, msg in enumerate(response['messages']):
                        if hasattr(msg, 'content'):
                            content = msg.content
                            if isinstance(content, str) and 'tool' in content.lower():
                                print(f"  消息 {i + 1} 包含工具调用: {content[:100]}...")
                            if isinstance(content, str) and 'access_token' in content.lower() and state.get(
                                    "client_token") is None:
                                content_json = json.loads(content.lower())
                                access_token_from_data = content_json["data"]["access_token"]
                                if access_token_from_data:
                                    client_token = access_token_from_data

            # 检查是否有工具调用相关的响应，前端打印
            if isinstance(response, dict) and "intermediate_steps" in response:
                print("=== 工具调用调试 ===")
                steps = response["intermediate_steps"]
                print(f"中间步骤数量: {len(steps)}")
                for i, step in enumerate(steps):
                    print(f"步骤 {i + 1}: {step}")
                print("=== 工具调用调试结束 ===")

            # 构造返回信息
            if isinstance(response, dict) and "messages" in response and response["messages"]:
                returned_messages = ensure_message_format(response["messages"])
                print(f"返回消息数量: {len(returned_messages)}")

                # 计算增量：仅返回新内容
                existing_contents = set()
                for m in messages:
                    c = getattr(m, "content", str(m))
                    existing_contents.add(c if isinstance(c, str) else str(c))

                delta: List[BaseMessage] = []
                for m in returned_messages:
                    c = getattr(m, "content", str(m))
                    c_str = c if isinstance(c, str) else str(c)
                    if c_str and c_str not in existing_contents:
                        delta.append(m)
                        existing_contents.add(c_str)

                print(f"增量消息数量: {len(delta)}")
                result = {}
                if delta:
                    result["messages"] = delta
                if client_token:
                    result["client_token"] = client_token

                return result if result else {}
            else:
                print("Agent 没有返回消息")
                return {"messages": [AIMessage(content="正在处理您的请求...")]}

        except Exception as e:
            print(f"=== Agent 调用异常 ===")
            print(f"异常类型: {type(e)}")
            print(f"异常信息: {str(e)}")
            import traceback
            traceback.print_exc()

            return {"messages": [AIMessage(content=f"处理请求时出现错误: {str(e)}")]}
