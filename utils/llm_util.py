import uuid
import time
import json
import requests
from random import choice
from hashlib import md5
from string import digits,ascii_letters
from typing import List, Optional, Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, ToolCall
from langchain_core.outputs import ChatResult, ChatGeneration

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import json
import re
from typing import Dict, List, Any, Optional


class AIMessageParser:
    """AIMessage内容解析器"""

    @staticmethod
    def parse_ai_message(ai_message,
                         content_key: str = 'content',
                         validate: bool = True) -> List[Dict[str, Any]]:
        """
        解析AIMessage对象中的JSON内容

        Args:
            ai_message: AIMessage对象或类似结构
            content_key: 内容字段的键名
            validate: 是否验证解析结果

        Returns:
            List[Dict[str, Any]]: 解析后的数据列表
        """
        try:
            # 获取内容
            if hasattr(ai_message, content_key):
                content = getattr(ai_message, content_key)
            elif isinstance(ai_message, dict) and content_key in ai_message:
                content = ai_message[content_key]
            else:
                raise ValueError(f"无法找到内容字段: {content_key}")

            # 提取JSON字符串
            json_str = AIMessageParser._extract_json_string(content)

            # 解析JSON
            parsed_data = json.loads(json_str)

            # 验证数据格式
            if validate:
                AIMessageParser._validate_parsed_data(parsed_data)

            return parsed_data

        except Exception as e:
            print(f"解析失败: {e}")
            return []

    @staticmethod
    def _extract_json_string(content: str) -> str:
        """从内容中提取JSON字符串"""
        # 方法1: 提取代码块中的JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # 方法2: 提取方括号内的内容
        bracket_match = re.search(r'(\[\s*\{.*?\}\s*\])', content, re.DOTALL)
        if bracket_match:
            return bracket_match.group(1).strip()

        # 方法3: 尝试直接解析整个内容
        try:
            # 检查内容本身是否是有效的JSON
            json.loads(content.strip())
            return content.strip()
        except:
            pass

        raise ValueError("无法从内容中提取有效的JSON数据")

    @staticmethod
    def _validate_parsed_data(data: Any) -> None:
        """验证解析后的数据格式"""
        if not isinstance(data, list):
            raise ValueError("解析的数据应该是列表类型")

        required_keys = {'text', 'source_id'}
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"第 {i} 个元素应该是字典类型")

            missing_keys = required_keys - set(item.keys())
            if missing_keys:
                raise ValueError(f"第 {i} 个元素缺少必要的键: {missing_keys}")

            if not isinstance(item['source_id'], list):
                raise ValueError(f"第 {i} 个元素的 source_id 应该是列表类型")

    @staticmethod
    def get_texts_only(ai_message) -> List[str]:
        """仅提取文本内容"""
        data = AIMessageParser.parse_ai_message(ai_message)
        return [item['text'] for item in data]

    @staticmethod
    def get_source_mapping(ai_message) -> Dict[str, List[str]]:
        """获取源ID到文本的映射"""
        data = AIMessageParser.parse_ai_message(ai_message)
        return {item['text']: item['source_id'] for item in data}



def generate_md5(src):
    m = md5(src.encode(encoding='utf-8'))
    return m.hexdigest()


def generate_random_str(randomlength=24):
    str_list = [choice(digits + ascii_letters) for i in range(randomlength)]
    random_str = ''.join(str_list)
    return random_str


def generate_token(api_key, api_secret, url="https://copilot.glodon.com/api/auth/v1/access-token"):
    """
    生成token

    :param api_key: 租户的API Key，必填项
    :param api_secret: 租户的API Secret，必填项
    :param url: 请求的接口地址, 默认为内网url
    :returns: 返回token
    """
    if api_key == "" or api_secret == "":
        print("请输入api_key和api_secret")
        return ""

    nowtime = time.time()
    timestamp = str(int(nowtime * 1000))
    noncestr = generate_random_str(24)
    raw_token = api_key + ":" + timestamp + ":" + noncestr + ":" + api_secret
    auth = generate_md5(raw_token)
    payload = {}
    headers = {
        'X-AIOT-APIKEY': api_key,
        'X-AIOT-TIMESTAMP': timestamp,
        'X-AIOT-NONCESTR': noncestr,
        'Authorization': "Basic " + auth
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            res = response.json()
            if res["code"] != 200:
                raise Exception(res["message"])

            token = "Bearer " + res["data"]["accessToken"]
            return (token)
        else:
            raise Exception(response.status_code)
    except Exception as err:
        print('An exception happened: ' + str(err))
        return ""


class CustomLLM(BaseChatModel):
    api_url: str
    access_token: str
    model_name: str
    tools: Optional[List[Any]] = None
    temperature: float
    max_tokens: int

    def bind_tools(self, tools: List[Any], **kwargs):
        return self.model_copy(update={"tools": tools})

    def _convert_tools_to_openai_format(self):
        if not self.tools:
            return []

        openai_tools = []
        for tool in self.tools:
            if hasattr(tool, "args_schema") and isinstance(tool.args_schema, type):
                try:
                    parameters = tool.args_schema.schema()
                except Exception:
                    parameters = {}
            else:
                parameters = getattr(tool, "args_schema", {})
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": (
                        parameters
                        if hasattr(tool, "args_schema")
                        else tool["parameters"]
                    ),
                },
            })
        return openai_tools

    def _generate(
            self,
            messages: List[BaseMessage],
            stop=None,
            run_manager=None,
            **kwargs
    ) -> ChatResult:
        formatted_messages = []
        for m in messages:
            if m.type == "system":
                formatted_messages.append({"role": "system", "content": m.content})
            elif m.type == "human":
                formatted_messages.append({"role": "user", "content": m.content})
            elif m.type == "ai":
                formatted_messages.append({"role": "assistant", "content": m.content})
            else:
                formatted_messages.append({"role": "user", "content": m.content})

        headers = {
            "Authorization": f"{self.access_token}" if self.access_token.startswith("Bearer") else f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        tools_payload = self._convert_tools_to_openai_format()
        if tools_payload:
            payload["tools"] = tools_payload

        resp = requests.post(self.api_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        message_data = data["choices"][0]["message"]
        output_text = message_data.get("content", "")

        # 如果是工具调用
        if "tool_calls" in message_data:
            tool_calls_list = []
            for t in message_data.get("tool_calls", []):
                # 把 JSON 字符串解析成 dict
                args_dict = json.loads(t["function"]["arguments"])
                tool_calls_list.append(
                    ToolCall(
                        id=str(uuid.uuid4()),  # 唯一 ID
                        name=t["function"]["name"],
                        args=args_dict
                    )
                )
            generation = ChatGeneration(
                message=AIMessage(content="", tool_calls=tool_calls_list)
            )
        else:
            generation = ChatGeneration(
                message=AIMessage(content=output_text)
            )
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "glodon-chat-model"


if __name__ == '__main__':
    llm = CustomLLM(
        api_url="https://copilot.glodon.com/api/cvforce/aishop/v1/chat/completions",
        # access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjI0ODA1NjIsImlhdCI6MTc2MjM5MzQ1OCwicm8iOiJ1c2VyIiwidGVuIjoiZ2RlcHRiIiwidWlkIjoiMTAwMDcwNiIsInNpZCI6MTc2NDEyNTM4Nn0.9t5Ii9p7v8hl1cAXnoYaOBO0OK_-apYjV6YLY-DoNhw",
        access_token=generate_token(api_key="TBDDAGJzAXaX5Zzl", api_secret="LEucuSDPRYCUaLj0UX1vvhoA"),
        model_name="Aejvnm7q3qmko",
        temperature=0.3,  # 确定性输出
        max_tokens=2000  # 减少token消耗
    )
    print(llm.invoke("你是谁"))