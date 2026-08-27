from datetime import datetime
from typing import List, Optional

from domain.models.session import Thesis
from domain.models.analyse_layer import AnalyseInput, AnalyseOutput
from domain.models.research_layer import ResearchItem, ResearchInput

from service.tools.web_tool import WebTool
from service.shared.prompt_renderer import PromptRenderer

from infra.llm.openai import OpenAIClient

class Orchestrator:
    def __init__(self, openai_api_key: str):
        self.theses: List[Thesis] = []
        self.web_tool = WebTool()
        self.llm = OpenAIClient(api_key=openai_api_key)
        self.prompt_renderer = PromptRenderer()

    def execute(
        self,
        max_results: Optional[int] = 3,
    ) -> List[Thesis]:
        """Execute the analysis pipeline for the given query."""

        self.theses = []

        query = """
        (earnings OR revenue OR margin OR guidance OR demand OR orders OR capex)
        ("beat expectations" OR "missed expectations" OR forecast OR outlook OR downgrade OR upgrade)
        (company OR shares OR stock)
        (site:reuters.com OR site:ft.com OR site:wsj.com OR site:cnbc.com)
        """

        # Step 1: Search and fetch data from the web
        fetched_data = self.web_tool.search_and_fetch(
            query=query,
        )

        # Step 2: Research the fetched data using LLM
        research_input = ResearchInput(
            fetched_data=fetched_data,
            max_theses_count=max_results
        )
        research_prompt = self.prompt_renderer.research_prompt(**research_input.model_dump())
        llm_research_output = self.llm.generate_response(
            system_prompt=research_prompt,
            response_model=List[ResearchItem],
        )

        # Step 3: Analyse the research output using LLM
        
        for item in llm_research_output:
            search_queries = item.search_queries
            search_results = {}

            for query in search_queries:
                search_results.update(self.web_tool.search_and_fetch(query=query))

            analyse_input = AnalyseInput(
                content=item.content,
                thinking=item.thinking,
                research_data=search_results
            ) 

            analyse_prompt = self.prompt_renderer.analyse_prompt(**analyse_input.model_dump())
            llm_analyse_output = self.llm.generate_response(
                system_prompt=analyse_prompt,
                response_model=AnalyseOutput,
            )

            # Step 4: Collect the theses and outcomes
            thesis = Thesis(
                content=item.content,
                thinking=item.thinking,
                prediction=llm_analyse_output.prediction,
                evidence=llm_analyse_output.evidence,
                counter_evidence=llm_analyse_output.counter_evidence,
                confidence=llm_analyse_output.confidence,
                created_at=datetime.now()
            )

            if not hasattr(self, 'theses'):
                self.theses = []
            self.theses.append(thesis)

        return self.theses

        