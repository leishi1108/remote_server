import logging
from langgraph.constants import END
from utils.graph_utils import SimpleGraphBuilder
from utils.llm_util import CustomLLM, generate_token, AIMessageParser
from typing import TypedDict, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ImageTabelState(TypedDict):
    image: List[float, Any]
    raw_output: str
    json_output: Dict[str, Any]
    error: str


class ImageTableAgent:
    def __init__(self, model, tools=None, prompt=None):
        if tools is None:
            tools = []
        self.model = model
        self.parser = AIMessageParser()
        self.tools = tools
        self.prompt = prompt if prompt is not None else "根据输入的图像，解析其中的表格内容。\n生成要求：\n1、输出结果中只包含解析结果的json列表，如果无法生成清单则返回空列表，不需要解释原因。"


        super().__init__()

    def call_llm_node(self, state: ImageTabelState):
        """调用大模型并获取原始输出"""
        try:
            prompt = f"{self.prompt}\n{state['image']}\n输出: "
            print(f"prompt: {prompt}\n")
            raw_response = self.model.invoke(f"{prompt}")
            print(f"raw_response {raw_response}\n")

            content_key = "content"
            if hasattr(raw_response, content_key):
                content = getattr(raw_response, content_key)
            else:
                content = raw_response

            state["raw_output"] = content
            state["json_output"] = {"ai_message": content}
        except Exception as e:
            state["json_output"] = {}
            # state["error"] = f"模型调用失败: {str(e)}"
        return state

    def run(self, request):
        llm_res = self.call_llm_node(request)
        print(f"llm_res {llm_res}\n")
        return llm_res


if __name__ == '__main__':
    llm = CustomLLM(
        api_url="https://copilot.glodon.com/api/cvforce/aishop/v1/chat/completions",
        access_token=generate_token(api_key="TBDDAGJzAXaX5Zzl", api_secret="LEucuSDPRYCUaLj0UX1vvhoA"),
        # model_name="Aejvnm7q3qmko",  # r1
        model_name = "Awd7m0gtxfphu", # v3
        temperature=0.3,  # 确定性输出
        max_tokens=12000  # 减少token消耗
    )
    # print(llm.invoke("你是谁？"))
    agent_client = ImageTableAgent(model=llm)

    res = agent_client.run({"image": []})
    print(f"res {res} type {type(res)}")