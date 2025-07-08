import logging

from aws_doc_sdk_examples_tools.lliam.domain.operations import build_ailly_config
from aws_doc_sdk_examples_tools.lliam.domain.commands import CreatePrompts
from aws_doc_sdk_examples_tools.lliam.service_layer.unit_of_work import FsUnitOfWork

logger = logging.getLogger(__name__)


def create_prompts(cmd: CreatePrompts, uow: FsUnitOfWork):
    with uow:
        system_prompts = uow.prompts.get_all(cmd.system_prompts)
        ailly_config = build_ailly_config(system_prompts)
        prompts = uow.doc_gen.get_new_prompts(cmd.doc_gen_root)
        uow.prompts.batch(prompts)
        uow.prompts.add(ailly_config)
        uow.prompts.set_partition(cmd.out_dir)
        uow.commit()
