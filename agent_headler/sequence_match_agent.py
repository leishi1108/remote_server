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


class SequenceMatchAgent:
    def __init__(self, text_key, model, tools=None, prompt=None):
        if tools is None:
            tools = []
        self.text_key = text_key
        self.model = model
        self.prompt = prompt if prompt is not None else "你是建筑行业的专家，请根据输入文本内容选择匹配的工序。\n匹配要求：\n1、如果没有匹配的项目就返回空列表，不需要解释原因；\n2、输出是匹配的工序的列表，必须在下列工序集合中: [加固处理, 勾缝处理, 涂料喷刷, 磨光, 打蜡, 防滑处理, 裱糊处理, 刚性层处理, 排气处理, 排水处理, 垫层处理, 基层处理, 回填, 钢筋焊接, 植筋, 塞口处理, 龙骨安装, 嵌缝, 吊杆安装, 防腐处理, 抹灰, 防锈处理, 隔离处理, 底层处理, 找平, 找坡, 结合处理, 保温处理, 防水处理, 隔气处理, 防护处理, 面层处理, 涂料喷刷\中层漆喷刷, 涂料喷刷\底漆喷刷, 回填\房心回填, 面层处理\块料挂贴, 面层处理\块料挂贴\干挂, 面层处理\块料挂贴\湿挂]；"


        super().__init__()

    def call_llm_node(self, state: TextRebuildState):
        """调用大模型并获取原始输出"""
        try:
            prompt = f"{self.prompt}\n输入: {state['input_text']}\n输出: "
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
        temperature=0.01,  # 确定性输出
        max_tokens=8000  # 减少token消耗
    )
    # print(llm.invoke("你是谁？"))
    agent_client = SequenceMatchAgent(text_key="input_text", model=llm)

    res = agent_client.run({"input_text": "楼面5-防滑地砖-其他层\n"})
    print(f"res {res} type {type(res)}")