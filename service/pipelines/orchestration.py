from datetime import datetime, timezone
from hashlib import sha256
from typing import List, Optional

from domain.models.session import Thesis
from domain.models.analyse_layer import AnalyseInput, AnalyseOutput
from domain.models.research_layer import ResearchItem, ResearchInput
from domain.models.prediction import Prediction, PredictionStatus
from domain.models.feedback import Reality, Evaluation

from service.pipelines.prediction_service import PredictionService
from service.pipelines.evaluation_service import EvaluationService

from service.tools.web_tool import WebTool
from service.shared.prompt_renderer import PromptRenderer

from infra.llm.openai import OpenAIClient


class Orchestrator:
    def __init__(
        self,
        openai_api_key: str | None = None,
        *,
        llm_client: OpenAIClient | None = None,
        web_tool: WebTool | None = None,
        prediction_service: PredictionService | None = None,
        evaluation_service: EvaluationService | None = None,
    ):
        self.theses: List[Thesis] = []

        self.web_tool = web_tool or WebTool()

        self.llm = llm_client or OpenAIClient(
            api_key=openai_api_key or ""
        )

        self.prompt_renderer = PromptRenderer()

        self.prediction_service = (
            prediction_service
            or PredictionService(
                llm_client=self.llm,
                prompt_renderer=self.prompt_renderer,
            )
        )

        self.evaluation_service = (
            evaluation_service
            or EvaluationService(
                llm_client=self.llm,
                prompt_renderer=self.prompt_renderer,
            )
        )

    @staticmethod
    def _thesis_id(content: str) -> str:
        digest = sha256(
            content.encode("utf-8")
        ).hexdigest()[:16]

        return f"thesis-{digest}"

    def _active_prediction(
        self,
        thesis_id: str,
    ) -> Prediction | None:

        for prediction in reversed(
            self.prediction_service.get_predictions()
        ):
            if (
                prediction.thesis_id == thesis_id
                and prediction.status == PredictionStatus.ACTIVE
            ):
                return prediction

        return None


    def execute(
        self,
        max_results: Optional[int] = 3,
    ) -> List[Thesis]:
        """
        Execute the research -> analysis -> prediction pipeline.
        """

        self.theses = []

        query = """
        (earnings OR revenue OR margin OR guidance OR demand OR orders OR capex)
        ("beat expectations" OR "missed expectations" OR forecast OR outlook OR downgrade OR upgrade)
        (company OR shares OR stock)
        (site:reuters.com OR site:ft.com OR site:wsj.com OR site:cnbc.com)
        """


        fetched_data = self.web_tool.search_and_fetch(
            query=query,
        )

        print("Web search and fetch completed.")


        research_input = ResearchInput(
            fetched_data=fetched_data,
            max_theses_count=max_results,
        )

        research_prompt = self.prompt_renderer.research_prompt(
            **research_input.model_dump()
        )

        llm_research_output = self.llm.generate_response(
            system_prompt=research_prompt,
            response_model=List[ResearchItem],
        )

        print("LLM Research Called.")


        for item in llm_research_output:

            search_results = {}

            for query in item.search_queries:
                search_results.update(
                    self.web_tool.search_and_fetch(
                        query=query
                    )
                )


            analyse_input = AnalyseInput(
                content=item.content,
                thinking=item.thinking,
                research_data=search_results,
            )

            analyse_prompt = self.prompt_renderer.analyse_prompt(
                **analyse_input.model_dump()
            )

            llm_analyse_output = self.llm.generate_response(
                system_prompt=analyse_prompt,
                response_model=AnalyseOutput,
            )

            print("LLM Analysis Called.")


            thesis_id = self._thesis_id(item.content)


            prediction_input = type(
                "PredictionAnalysisContext",
                (),
                {
                    "thesis_id": thesis_id,
                    "information_cutoff": datetime.now(timezone.utc),
                    "content": item.content,
                    "thinking": item.thinking,
                    "research_data": search_results,
                    "prediction": llm_analyse_output.prediction,
                    "evidence": llm_analyse_output.evidence,
                    "counter_evidence": llm_analyse_output.counter_evidence,
                    "confidence": llm_analyse_output.confidence,
                },
            )()


            existing_prediction = self._active_prediction(
                thesis_id
            )

            prediction = self.prediction_service.generate(
                analysis_output=prediction_input,
                existing_prediction=existing_prediction,
            )

            print("LLM Prediction Called.")

            thesis = Thesis(
                content=item.content,
                thinking=item.thinking,
                prediction=llm_analyse_output.prediction,
                evidence=llm_analyse_output.evidence,
                counter_evidence=llm_analyse_output.counter_evidence,
                confidence=llm_analyse_output.confidence,
                created_at=datetime.now(timezone.utc),
                prediction_record=prediction,
            )

            self.theses.append(thesis)

        return self.theses


    def evaluate_prediction(
        self,
        prediction: Prediction,
        reality: Reality,
    ) -> Evaluation:
        """
        Compare a prediction with the observed reality.
        """

        evaluation = self.evaluation_service.evaluate(
            prediction=prediction,
            reality=reality,
        )

        print(
            f"Prediction {prediction.id} "
            f"v{prediction.version} evaluated."
        )

        return evaluation


    def _find_prediction(
        self,
        prediction_id: str,
    ) -> Prediction | None:

        for prediction in self.prediction_service.get_predictions():
            if prediction.id == prediction_id:
                return prediction

        return None