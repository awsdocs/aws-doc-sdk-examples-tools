import yaml
from typing import List

from aws_doc_sdk_examples_tools.lliam.domain.model import Prompt


def build_ailly_config(system_prompts: List[Prompt]) -> Prompt:
    """Create the .aillyrc configuration file."""
    fence = "---"
    options = {
        "isolated": "true",
        "overwrite": "true",
        # MCP assistance did not produce noticeably different results, but it was
        # slowing things down by 10x. Disabled for now.
        # "mcp": {
        #     "awslabs.aws-documentation-mcp-server": {
        #         "type": "stdio",
        #         "command": "uvx",
        #         "args": ["awslabs.aws-documentation-mcp-server@latest"],
        #     }
        # },
    }
    options_block = yaml.dump(options).strip()
    prompt_strs = [p.content for p in system_prompts]
    prompts_block = "\n".join(prompt_strs)

    content = f"{fence}\n{options_block}\n{fence}\n{prompts_block}"
    return Prompt(".aillyrc", content)
