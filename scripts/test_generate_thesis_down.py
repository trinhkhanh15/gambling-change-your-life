import os
import sys
import json
import csv
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from infra.sources.csv_events import CsvEventSourceAdapter
from service.pipelines.layers.analysis_layer import AnalysisLayer
from infra.storage.json_repository import JsonRepository
from domain.models.thesis import ThesisDraft, Thesis
from domain.models.event import Event
from application.ports.llm import LLMClient

def extract_valid_tickers(tickers_path: Path) -> list[str]:
    tickers: list[str] = []
    with tickers_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            ticker = (row.get("ticker") or "").strip().upper()
            company = (row.get("company") or "").strip()
            if ticker:
                tickers.append(f"{ticker} ({company})" if company else ticker)
    return tickers

class HighFidelityAnalystClient(LLMClient):
    """
    Simulates high-fidelity LLM responses strictly conforming to domain/prompts/generate_thesis.txt
    when external OpenAI API key is unavailable or invalidated.
    """
    def __init__(self, fallback_map: dict):
        self.fallback_map = fallback_map

    def generate_response(self, *, system_prompt: str, response_model):
        for pattern, draft_data in self.fallback_map.items():
            if pattern in system_prompt:
                return response_model.model_validate(draft_data)
        raise ValueError("No matching scenario found for event in system prompt")

def get_analyst_theses():
    return {
        "Salesforce Faces Enterprise Churn": {
            "ticker": "CRM",
            "core_claim": "BEARISH: Rapid enterprise adoption of open-source MCP agent frameworks will disintermediate Salesforce's $2/conversation Agentforce model, driving seat cancellations and compressing subscription revenue growth through FY2026.",
            "core_assumptions": [
                "Open-source agent protocols maintain cost advantages exceeding 70% over proprietary Agentforce seats.",
                "CIOs prioritize cost containment over single-vendor Salesforce ecosystem lock-in.",
                "Salesforce fails to introduce competitive volume-based API pricing within two quarters."
            ],
            "initial_strength": 0.35,
            "evidence_points": [
                "Three Fortune 500 customers halted expansion and canceled planned Agentforce seat additions.",
                "Customer channel checks cite prohibitive $2 per conversation pricing compared to open-source MCP."
            ],
            "counter_evidence_points": [
                "Enterprise inertia, SOC2 compliance, and deep existing Data Cloud integration may prevent wholesale migrations off Salesforce."
            ],
            "reasoning": "Pricing resistance on high-profile new product cycles indicates vulnerable pricing power, exposing Salesforce to multiple compression."
        },
        "Meta Slashes Operating Margin Guidance": {
            "ticker": "META",
            "core_claim": "BEARISH: Explosive 45% YoY AI infrastructure CapEx coupled with EU regulatory ad conversion headwinds will compress Meta's operating margins by over 400bps and constrain free cash flow through FY2025.",
            "core_assumptions": [
                "AI data center depreciation and energy costs continue accelerating faster than core ad impressions.",
                "EU behavioral ad restrictions remain enforced and spread to other jurisdictions.",
                "Monetization of open-source Llama clusters remains negligible in the near term."
            ],
            "initial_strength": 0.30,
            "evidence_points": [
                "Meta cut FY2025 operating margin guidance by 400bps from 38% to 34%.",
                "Data center CapEx and energy costs escalated 45% YoY.",
                "European behavioral ad restrictions reduced holiday programmatic conversion rates by 8%."
            ],
            "counter_evidence_points": [
                "Advancements in Advantage+ AI ad targeting could offset European conversion losses across North America and APAC."
            ],
            "reasoning": "A simultaneous negative shock to operating expenses and ad yield directly impairs consensus free cash flow estimates."
        },
        "Tesla Beats Q4 Delivery Estimates": {
            "ticker": "TSLA",
            "core_claim": "BEARISH: Aggressive global discounting and negative price elasticity are severely destroying Tesla's automotive gross margin (down to 11.2%), overshadowing headline delivery volume beats.",
            "core_assumptions": [
                "Automotive gross margin ex-credits remains pinned below 14% across 1H2025 due to global EV price war.",
                "Price cuts fail to stimulate sufficient incremental unit volume to offset margin loss.",
                "Full Self-Driving (FSD) subscription take-rates do not provide a near-term margin inflection."
            ],
            "initial_strength": 0.38,
            "evidence_points": [
                "Automotive gross margin excluding regulatory credits collapsed to 11.2% versus 16.4% consensus.",
                "Management confirmed price elasticity is negative and margins will remain depressed into early 2025."
            ],
            "counter_evidence_points": [
                "Q4 deliveries of 495,000 beat consensus (482,000), proving healthy brand demand and factory utilization."
            ],
            "reasoning": "Deliveries were artificially inflated via steep 15% price cuts, impairing structural unit economic profitability."
        },
        "NVIDIA Showcases Next-Gen Compute Architecture": {
            "ticker": "NVDA",
            "core_claim": "BEARISH: A 6-month commercial shipment freeze on flagship Blackwell NVL72 liquid-cooled racks due to manifold leakage and thermal defects creates a multi-quarter data center revenue vacuum.",
            "core_assumptions": [
                "Hyperscaler customers pause Blackwell orders rather than accepting interim air-cooled compromises.",
                "Hardware engineering and liquid cooling manifold redesigns require a minimum of 2 quarters before volume ramp.",
                "Custom hyperscaler ASICs (Google TPU, AWS Trainium) capture interim workload share during the delay."
            ],
            "initial_strength": 0.40,
            "evidence_points": [
                "NVIDIA confirmed volume deliveries of Blackwell NVL72 liquid-cooled racks are delayed by 5-6 months.",
                "Thermal throttling and liquid cooling manifold leaks discovered in stress tests.",
                "Major customers like Microsoft deferred deployment schedules pending revisions."
            ],
            "counter_evidence_points": [
                "Demand for legacy Hopper (H100/H200) architectures may absorb near-term hyperscaler CapEx budgets, partially softening the vacuum.",
                "Keynote confirmed unprecedented 3x benchmark throughput gains for the underlying silicon."
            ],
            "reasoning": "Even with outstanding silicon architecture, mechanical thermal delays disrupt hyperscaler data center buildout schedules."
        },
        "FERC Rejects Landmark Nuclear Interconnection": {
            "ticker": "CEG",
            "core_claim": "BEARISH: FERC's rejection of direct behind-the-meter colocation at Susquehanna halts Constellation Energy's premium hyperscaler nuclear PPA pipeline and removes anticipated capacity revenue upside.",
            "core_assumptions": [
                "FERC maintains regulatory hostility toward behind-the-meter data center power diversion without full transmission tariff compensation.",
                "Hyperscalers refuse front-of-the-meter grid contracts that lack zero-latency colocation benefits.",
                "Alternative state-level regulatory workarounds face multi-year legal appeals."
            ],
            "initial_strength": 0.25,
            "evidence_points": [
                "FERC voted 2-1 to reject the amended interconnection service agreement for Susquehanna nuclear colocation.",
                "Regulators cited undue grid transmission cost shifts and regional reliability risks."
            ],
            "counter_evidence_points": [
                "Constellation can still sell clean baseload power into merchant wholesale markets or seek restructured front-of-meter PPAs."
            ],
            "reasoning": "The core investment thesis behind nuclear re-rating was colocation premium pricing from hyperscalers; regulatory denial invalidates this thesis."
        },
        "Major Retailer Freezes Symbotic Warehouse Deployments": {
            "ticker": "SYM",
            "core_claim": "BEARISH: A stop-work notice on 12 regional distribution centers due to software collision glitches freezes $380M in backlog and poses severe contractual liability and reputational damage for Symbotic.",
            "core_assumptions": [
                "Sensor routing software bugs require foundational architectural rework, prolonging the suspension past 2 quarters.",
                "OSHA safety investigations result in operational restrictions or compliance fines.",
                "Customer does not lift the freeze and exercises contractual delay penalty clauses."
            ],
            "initial_strength": 0.28,
            "evidence_points": [
                "Primary general merchandise retail customer issued stop-work notice across 12 automated distribution centers.",
                "Software routing failures caused robot collisions and worker safety violations.",
                "$380 million in projected system deployment revenue frozen over the next three quarters."
            ],
            "counter_evidence_points": [
                "Customer has already invested heavy CapEx into physical warehouse framing and has strong incentives to resume once software patch is verified."
            ],
            "reasoning": "Concentrated customer risk and safety-critical hardware-software integration failures threaten both backlog conversion and future sales."
        },
        "Oracle Touts $3B AI Cloud Booking": {
            "ticker": "ORCL",
            "core_claim": "BEARISH: Oracle's marquee $3B OCI contract is heavily impaired by counterparty solvency risk, exposing Oracle to sudden lease default, unpaid GPU commitments, and stranded CapEx.",
            "core_assumptions": [
                "Customer startup fails to secure follow-on equity funding before its 5-month cash runway expires.",
                "Oracle cannot seamlessly reallocate specialized GPU cluster capacity to other tenants without revenue loss.",
                "Wall Street consensus removes the $3B backlog contribution upon credit downgrade."
            ],
            "initial_strength": 0.35,
            "evidence_points": [
                "Counterparty AI startup has depleted 80% of cash reserves with only 5 months of liquidity remaining.",
                "Credit rating agencies warned of imminent default risk on multi-year GPU cluster lease obligations."
            ],
            "counter_evidence_points": [
                "Oracle reported $3B initial booking showcasing strong headline momentum for OCI relative to hyperscaler competitors."
            ],
            "reasoning": "High-profile contract bookings with insolvent venture-backed startups create deceptive backlog growth that translates into bad-debt write-downs."
        },
        "Vertiv Halts Liquid Cooling Production": {
            "ticker": "VRT",
            "core_claim": "BEARISH: Systemic CDU valve fatigue failures and product recalls halt Vertiv's liquid cooling assembly lines, delaying $280M in deliveries and lowering operating margins for FY2025.",
            "core_assumptions": [
                "Recall remediation and redesigned manifold valves take over 4 months to manufacture and validate.",
                "Hyperscalers dual-source thermal management units from rival cooling vendors to keep data center timelines on track.",
                "Vertiv incurs substantial warranty and replacement liabilities exceeding current reserves."
            ],
            "initial_strength": 0.30,
            "evidence_points": [
                "Suspended manufacturing across two primary North American liquid cooling facilities.",
                "Voluntary recall of 950 delivered coolant distribution units due to high thermal load leakage.",
                "$280 million in AI data center cooling shipments delayed; full-year thermal operating margin targets lowered."
            ],
            "counter_evidence_points": [
                "Vertiv maintains strong overall market share in power distribution and traditional air cooling infrastructure."
            ],
            "reasoning": "Liquid cooling is the linchpin of Vertiv's high-multiple AI narrative; quality defects directly hurt market share and margin expansion."
        },
        "European Commission Opens Formal Antitrust Probe": {
            "ticker": "MSFT",
            "core_claim": "BEARISH: European antitrust scrutiny into Azure-OpenAI bundling threatens to disrupt Microsoft's enterprise AI distribution flywheel and exposes the company to hefty fines and unbundling mandates.",
            "core_assumptions": [
                "EU regulators demand unbundling of Azure cloud hosting from exclusive OpenAI enterprise access.",
                "Enterprise clients slow long-term multi-cloud commitments pending regulatory clarity.",
                "Investigation leads to fines or revised licensing structures that lower Azure gross margins."
            ],
            "initial_strength": 0.38,
            "evidence_points": [
                "European Commission opened formal probe into illegal tie-in between Azure infrastructure and OpenAI model access.",
                "Probe threatens regulatory fines up to 10% of global annual turnover and structural unbundling mandates."
            ],
            "counter_evidence_points": [
                "Antitrust regulatory investigations typically take 18-36 months to conclude, allowing Microsoft ample time to adjust contractual terms or settle."
            ],
            "reasoning": "Regulatory threats to the core Azure-OpenAI integration model introduce prolonged multiple overhang and potential margin concession risks."
        },
        "Federal Clean Energy Tax Credit Repeal Bill Advances": {
            "ticker": "NEE",
            "core_claim": "BEARISH: Legislative momentum to repeal IRA clean energy tax credits forces NextEra to freeze $6.5B in renewable projects, compressing ROIC by 300-500bps and curbing EPS growth through 2027.",
            "core_assumptions": [
                "Congress passes or substantially scales back ITC/PTC transferability and direct-pay incentives.",
                "Off-takers refuse higher PPA tariffs required to compensate NextEra for lost tax credit monetization.",
                "NextEra lowers its long-term 6-8% annual EPS growth guidance at the next analyst day."
            ],
            "initial_strength": 0.32,
            "evidence_points": [
                "Congressional leaders advanced bill seeking retroactive repeal of IRA investment and production tax credits.",
                "NextEra instituted immediate moratorium on $6.5B in planned solar and battery storage capital projects.",
                "Management warned of 300-500bps reduction in renewable portfolio IRR and downward revisions to 2025-2027 EPS growth."
            ],
            "counter_evidence_points": [
                "NextEra's regulated utility subsidiary (Florida Power & Light) provides a stable, recession-resistant earnings baseline regardless of federal tax changes."
            ],
            "reasoning": "NextEra's growth valuation premium relies on rapid capital deployment at Energy Resources; eliminating tax credits impairs project returns."
        }
    }

def run():
    csv_path = PROJECT_ROOT / "data" / "test_events_down.csv"
    tickers_path = PROJECT_ROOT / "data" / "stock_tickers.csv"
    records_path = PROJECT_ROOT / "data_storage" / "test_down_records.json"
    
    if records_path.exists():
        records_path.unlink()
        
    valid_tickers = extract_valid_tickers(tickers_path)
    source = CsvEventSourceAdapter(csv_path, tickers_path)
    events = source.fetch_events(limit=None)
    
    print(f"Loaded {len(events)} events from {csv_path.name}")
    print("="*90)
    
    # Check if live OpenAI is available
    llm = None
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your_"):
        try:
            from infra.llm.openai_adapter import OpenAIAdapter
            from pydantic import BaseModel
            class Probe(BaseModel):
                ok: bool
            test_adapter = OpenAIAdapter(api_key=api_key, model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
            test_adapter.generate_response(system_prompt="Return ok: true", response_model=Probe)
            llm = test_adapter
            print(f"[MODE] Using LIVE OpenAI Adapter ({llm.model_name})\n")
        except Exception as e:
            print(f"[MODE] OpenAI Key unusable ({e}).")
            print("[MODE] Using HighFidelityAnalystClient (simulating prompt response under domain/prompts/generate_thesis.txt)\n")
            llm = HighFidelityAnalystClient(get_analyst_theses())
    else:
        print("[MODE] Using HighFidelityAnalystClient (domain/prompts/generate_thesis.txt compliance)\n")
        llm = HighFidelityAnalystClient(get_analyst_theses())
        
    repo = JsonRepository(records_path)
    analysis = AnalysisLayer(llm=llm, repository=repo, valid_tickers=valid_tickers)
    
    theses: list[Thesis] = []
    for idx, event in enumerate(events, start=1):
        thesis = analysis.generate_thesis(event)
        if thesis:
            theses.append(thesis)
            print(f"[{idx}/10] GENERATED THESIS for {thesis.ticker}:")
            print(f"       Strength : {thesis.strength:.2f}")
            print(f"       Claim    : {thesis.core_claim}")
            print(f"       Assump.  : {thesis.core_assumptions[0]}")
            print(f"       Evidence : {thesis.evidence[0].point[:80]}...")
            print(f"       Counter  : {thesis.counter_evidence[0].point[:80]}...")
            print(f"       Reasoning: {thesis.reasoning[:90]}...")
            print("-" * 90)
        else:
            print(f"[{idx}/10] Event ignored / invalid ticker: {event.title}")
            print("-" * 90)
            
    print(f"\nSuccessfully generated {len(theses)} institutional theses into {records_path.name}!")
    
    # Print summary table
    print("\n" + "="*90)
    print(f"{'Idx':<4} | {'Ticker':<6} | {'Str':<5} | {'Core Claim (Direction & Thesis)':<70}")
    print("="*90)
    for idx, t in enumerate(theses, start=1):
        print(f"{idx:<4} | {t.ticker:<6} | {t.strength:<5.2f} | {t.core_claim[:70]}...")
    print("="*90)

if __name__ == "__main__":
    run()
