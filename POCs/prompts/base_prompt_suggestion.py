"""
Author: Sarvagya Meel
Email: sarvagyameel2@gmail.com
Date: 01/03/2025
"""
from abc import abstractmethod, ABC

from POCs.Prompts.postgress_prompt_suggestion import PromptSuggestion


class BasePromptSuggestion(ABC):

    @abstractmethod
    def get_suggestions(self, **kwargs) -> list[PromptSuggestion]:
        return [PromptSuggestion()]
