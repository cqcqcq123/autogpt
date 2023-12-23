from logging import Logger

from AFAAS.core.agents.planner.strategies.initial_plan import (
    InitialPlanStrategy,
    InitialPlanStrategyConfiguration,
)
from AFAAS.core.agents.planner.strategies.select_tool import (
    SelectToolStrategy,
    SelectToolStrategyConfiguration,
)
from AFAAS.interfaces.prompts.strategy import PromptStrategiesConfiguration
from AFAAS.lib.sdk.logger import AFAASLogger

LOG = AFAASLogger(name=__name__)


class StrategiesConfiguration(PromptStrategiesConfiguration):
    initial_plan: InitialPlanStrategyConfiguration
    select_tool: SelectToolStrategyConfiguration


class StrategiesSet:
    from AFAAS.interfaces.prompts.strategy import AbstractPromptStrategy

    @staticmethod
    def get_strategies(
        logger: Logger = Logger(__name__),
    ) -> list[AbstractPromptStrategy]:
        return [
            InitialPlanStrategy(**InitialPlanStrategy.default_configuration.dict()),
            # SelectToolStrategy(
            #     **SelectToolStrategy.default_configuration.dict()
            # ),
        ]