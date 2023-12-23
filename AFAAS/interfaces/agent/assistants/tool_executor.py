from __future__ import annotations

from AFAAS.interfaces.agent.features.agentmixin import AgentMixin


class ToolExecutor(AgentMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from AFAAS.lib.sdk.logger import AFAASLogger

        AFAASLogger(name=__name__).trace(
            "ToolExecutor : Has not been implemented yet"
        )
        AFAASLogger(name=__name__).trace(
            "ToolExecutor : Will be part of a @tool wrapper redisign"
        )