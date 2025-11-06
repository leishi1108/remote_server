import logging
from langgraph.constants import END
from langgraph.prebuilt import create_react_agent
from utils.agent_utils import AgentState, SimpleGraphBuilder, SimpleAgentRunner

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TextRebuildAgent(SimpleGraphBuilder):

    def __init__(self, llm, tools, prompt):
        super().__init__()
        self.llm = llm
        self.tools = tools
        self.prompt = prompt
        self.agent = create_react_agent(llm, tools, prompt=(
            """self.prompt"""))
        self.agent_runner = SimpleAgentRunner(self.agent)

    def _setup_nodes(self):
        self.builder.add_node("react_agent", self.agent_runner)

    def _setup_edges(self):
        self.builder.add_edge("react_agent", END)

        self.builder.set_entry_point("react_agent")



