import logging
from langgraph.constants import END
from langgraph.prebuilt import create_react_agent
from utils.agent_utils import AgentState, SimpleGraphBuilder, SimpleAgentRunner
from utils.llm_util import CustomLLM, generate_token

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TextRebuildAgent(SimpleGraphBuilder):

    def __init__(self, llm, tools, prompt):
        self.llm = llm
        self.tools = tools
        self.prompt = prompt
        self.agent = create_react_agent(llm, tools, prompt=(
            f"""{self.prompt}"""))
        self.agent_runner = SimpleAgentRunner(self.agent)

        super().__init__()

    def _setup_nodes(self):
        self.builder.add_node("react_agent", self.agent_runner.__run__)

    def _setup_edges(self):
        self.builder.add_edge("react_agent", END)

        self.builder.set_entry_point("react_agent")



if __name__ == '__main__':
    llm = CustomLLM(
        api_url="https://copilot.glodon.com/api/cvforce/aishop/v1/chat/completions",
        access_token=generate_token(api_key="TBDDAGJzAXaX5Zzl", api_secret="LEucuSDPRYCUaLj0UX1vvhoA"),
        model_name="Aejvnm7q3qmko",
        temperature=0.3,  # 确定性输出
        max_tokens=2000  # 减少token消耗
    )

    agent_client = TextRebuildAgent(llm=llm, tools=[], prompt="")
    print(agent_client.invoke("你是谁"))