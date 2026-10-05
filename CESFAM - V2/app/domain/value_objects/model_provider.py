from enum import Enum


class ModelProvider(str, Enum):

    GEMINI = "gemini"
    CLAUDE = "claude"
    LOCAL = "local"
