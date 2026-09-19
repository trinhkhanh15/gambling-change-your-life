from typing import Any

class PromptRenderer:
    """
    Role: Prompt Engineer & Template Manager.
    Nhận dữ liệu thô (từ WebTool) và nhét vào 
    template (.txt) để tạo ra câu lệnh hoàn chỉnh trước khi bắn lên OpenAI.
    """

    def research_prompt(self, **context: Any) -> str:
        """
        Injects fetched news data into the Research template.
        Expected context keys: 'fetched_data', 'max_theses'
        """
        pass

    def analyse_prompt(self, **context: Any) -> str:
        """
        Injects hypotheses and specific evidence into the Analyse template.
        Expected context keys: 'event_context', 'thinking_process', 'evidence'
        """
        pass