import logging
from langgraph.constants import END
from utils.graph_utils import SimpleGraphBuilder
from utils.llm_util import CustomLLM, generate_token, AIMessageParser
from utils.knowledge import PARTIAL_DICT
from typing import TypedDict, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ListMakeState(TypedDict):
    text: str
    context: str
    raw_output: str
    json_output: Dict[str, Any]
    error: str


class ListMakeAgent:
    def __init__(self, text_key, context_key, model, prompt=None):
        self.text_key = text_key
        self.context_key = context_key
        self.model = model
        self.prompt = prompt if prompt is not None else "根据项目信息要求，尽可能从输入文本中提取匹配的信息，生成建筑行业的项目清单。\n生成要求：\n1、输出结果中只包含清单列表，如果无法生成清单则返回空列表；\n2、如果输入文本中没有匹配内容，则不生成清单；\n3、钢筋混凝土构件的清单按照混凝土强度等级分别生成清单；\n4、尽可能提取合适的部位信息，如空间、楼层；"
        self.partial_dict = PARTIAL_DICT


        super().__init__()


    def call_llm_node(self, state: ListMakeState):
        """调用大模型并获取原始输出"""
        try:
            context = state['context']
            if context not in self.partial_dict:
                print(f"context: {context} not in partial_dict, return\n")
                return

            context_content = self.partial_dict[context]
            prompt = f"{self.prompt}\n项目信息要求: {context_content}\n清单格式: {{'项目名称': '', '项目特征': ''}}。\n输入: {state['text']}\n输出:\n"

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
        max_tokens=8000  # 减少token消耗
    )
    # print(llm.invoke("你是谁？"))
    agent_client = ListMakeAgent(text_key="text", context_key="context", model=llm)
    res = agent_client.run({"text": "五、挡土墙、底板\n1、材料:钢筋混凝土:C35(抗渗等级P6);钢筋:A为HPB300级,C为HRB400级;\n2、挡土墙、底板混凝土施工中,在混凝土中掺入水泥用量HEA微膨胀剂(置换水泥)。\n3、除注明外,基础梁均对轴线居中布置或与柱、墙边平齐。\n4、底板迎水面及挡土墙迎土面混凝土保护层为40mm,底板背水面的混凝土保护层厚度为25mm,挡土墙背土面混凝土保护层厚度为20mm。防水板板底设置100厚C15的素混凝土垫层\n5、除注明外,挡土墙均对轴线居中布置或与柱边平齐。\n6、挡墙后填土不得采用粘土与建筑垃圾作为回填土,宜选用碎石土等透水性大的材料作为回填土,压实系数不小于0.94。\n7、框架柱、框支柱迎土面钢筋保护层厚度应向外加15mm。", "context": "现浇混凝土构件_挡土墙"})
    print(f"res {res} type {type(res)}")