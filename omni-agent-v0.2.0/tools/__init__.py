from tools.base import Tool, ToolRegistry
from tools.terminal import TerminalTool
from tools.filesystem import FilesystemTool
from tools.web import WebFetchTool


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(TerminalTool())
    registry.register(FilesystemTool())
    registry.register(WebFetchTool())
    return registry
