import logging
from langgraph.constants import END
from utils.graph_utils import SimpleGraphBuilder
from utils.llm_util import CustomLLM, generate_token, AIMessageParser
from typing import TypedDict, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TextRebuildState(TypedDict):
    input_text: str
    raw_output: str
    json_output: Dict[str, Any]
    error: str


class TextRebuildAgent():
    def __init__(self, llm, tools, prompt=None):
        self.llm = llm
        self.parser = AIMessageParser()
        self.tools = tools
        self.prompt = prompt if prompt is not None else """根据文本以及坐标，把文本整理成正确的语序，使得语句通顺，结果按json列表输出。输出示例：[{"text": "", "source_id": ["", ""]}, ]。\n输入：\n\n"""

        super().__init__()

    def call_llm_node(self, state: TextRebuildState):
        """调用大模型并获取原始输出"""
        try:
            print(f"input_text {state['input_text']}")
            raw_response = self.llm.invoke(f"{self.prompt}{state['input_text']}")
            print(f"raw_response {raw_response}")
            state["raw_output"] = raw_response
            state["json_output"] = {"ai_message": self.parser.parse_ai_message(raw_response)}
        except Exception as e:
            state["error"] = f"模型调用失败: {str(e)}"
        return state

    def run(self, request):
        llm_res = self.call_llm_node(request)
        return llm_res





if __name__ == '__main__':
    llm = CustomLLM(
        api_url="https://copilot.glodon.com/api/cvforce/aishop/v1/chat/completions",
        access_token=generate_token(api_key="TBDDAGJzAXaX5Zzl", api_secret="LEucuSDPRYCUaLj0UX1vvhoA"),
        model_name="Aejvnm7q3qmko",
        temperature=0.3,  # 确定性输出
        max_tokens=2000  # 减少token消耗
    )
    print(llm.invoke("你是谁？"))
    agent_client = TextRebuildAgent(llm=llm, tools=[])

    res = agent_client.run({"input_text": "[{\"id\": \"15625\", \"x\": \"335.315\", \"y\": \"3002.99\", \"text\": \"11.6  填充墙维护墙防开裂措施;\"}]"})
    print(f"res {res}")