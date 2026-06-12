from utils.logger import get_logger
logger = get_logger(__name__)
from .yaml_tools.base import CI_Builder,CD_Builder,TF_Builder, yaml_update
from agent_framework import tool #type: ignore
from typing import Annotated
from pydantic import Field
from utils.prompt_manager_v2 import AgentDescriptionPrompt, AgentInstructionPrompt, ToolFieldsPrompt
from ..Base_agent import Base_Agent
from utils.logger import get_logger
logger = get_logger(__name__)


class YamlAgent(Base_Agent):
    name = "yaml_agent"
    instructions = str(AgentInstructionPrompt("yaml-agent-instructions"))
    tools = [CI_Builder,CD_Builder,TF_Builder,yaml_update]

_yaml_agent_field = ToolFieldsPrompt("yaml-agent-field-description")

@tool(name="Yaml_Agent",
      description=str(AgentDescriptionPrompt("yaml-agent-description")),
      approval_mode="never_require")
async def yaml_agent(prompt: Annotated[str, Field(description = _yaml_agent_field.get("prompt"))]):
    logger.info("[yaml_agent] Called with prompt.")
    print("[yaml_agent] Called with prompt.")
    logger.debug(f"[yaml_agent] Prompt: {prompt}")
    print(f"[yaml_agent] Prompt: {prompt}")
    try:
        result = await YamlAgent.get_instance().run(prompt) #type: ignore
        logger.info("[yaml_agent] Successfully generated YAML output.")
        print("[yaml_agent] Successfully generated YAML output.")
        logger.debug(f"[yaml_agent] Output: {result}")
        print(f"[yaml_agent] Output: {result}")
        return result
    except Exception as e:
        logger.error(f"[yaml_agent] Error occurred: {e}", exc_info=True)
        print(f"[yaml_agent] Error occurred: {e}")
        raise




