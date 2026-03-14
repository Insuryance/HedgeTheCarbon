"""
CarbonIQ - PDF Parser Service (Simulated)
Simulates LLM-based extraction of structured data from Project Design Documents (PDDs).
In production, this would call Gemini/GPT-4 to extract fields from actual PDFs.
"""
import random
from typing import Optional
from services.vector_service import vector_service


# ─── Simulated PDD Content Templates ────────────────────────────

PDD_TEMPLATES = {
    "REDD+": {
        "additionality_claim": "Without the project, the forest area would be converted to agricultural land "
                               "due to economic pressures. The project provides alternative livelihoods.",
        "baseline_assumptions": "Baseline deforestation rate calculated using historical satellite imagery "
                                "(2005-2015). Annual forest loss projected at {rate}% based on regional trends.",
        "leakage_risk": "Activity-shifting leakage monitored in a 20km buffer zone. Market leakage "
                        "assessed through regional timber market analysis. Estimated leakage: {pct}%.",
        "co_benefits": ["Biodiversity conservation", "Community employment", "Watershed protection",
                        "Indigenous rights", "Educational programs"],
        "monitoring_plan": "Annual field surveys, quarterly satellite monitoring (Sentinel-2/Landsat), "
                          "community-based fire patrol, permanent sample plots re-measured every 5 years.",
    },
    "ARR": {
        "additionality_claim": "Land was degraded and would remain unforested without intervention. "
                               "Financial barrier analysis demonstrates project viability only with carbon revenue.",
        "baseline_assumptions": "Baseline scenario: continued grassland/degraded land with zero net carbon "
                                "sequestration. Soil carbon baseline measured at {tco2} tCO2/ha.",
        "leakage_risk": "Low leakage risk as planting occurs on degraded non-agricultural land. "
                        "No displacement of existing land use activities.",
        "co_benefits": ["Soil restoration", "Habitat creation", "Water table improvement",
                        "Employment", "Carbon education"],
        "monitoring_plan": "Biennial biomass measurement, annual survival assessments, "
                          "soil carbon sampling every 5 years, remote sensing verification.",
    },
    "Cookstoves": {
        "additionality_claim": "Clean cookstoves would not achieve market penetration without carbon finance. "
                               "Barrier analysis shows cost differential of ${cost} per household.",
        "baseline_assumptions": "Baseline fuel consumption: {kg}kg firewood per household per month. "
                                "Emission factor: 1.8 tCO2e per tonne of non-renewable biomass.",
        "leakage_risk": "Minimal leakage. Displaced firewood not expected to be sold or burned elsewhere. "
                        "Cross-border leakage not applicable.",
        "co_benefits": ["Indoor air quality improvement", "Women's time saving",
                        "Reduced deforestation", "Health improvement", "Economic savings"],
        "monitoring_plan": "Kitchen performance tests (KPT) on 5% sample annually, "
                          "usage surveys, stove inspection, fuel consumption metering.",
    },
    "default": {
        "additionality_claim": "Project activities would not be financially viable without carbon revenue. "
                               "Investment barrier analysis demonstrates below-benchmark IRR without credits.",
        "baseline_assumptions": "Baseline emissions calculated using approved methodology parameters. "
                                "Conservative assumptions applied per registry guidelines.",
        "leakage_risk": "Leakage risk assessed as {level}. Monitoring protocols in place.",
        "co_benefits": ["Environmental improvement", "Community development", "Employment"],
        "monitoring_plan": "Annual monitoring with third-party verification every {years} years.",
    },
}


def extract_pdd_data(project_name: str, project_type: str, country: str) -> dict:
    """
    Simulate LLM extraction of PDD document fields.
    In production: send PDF to Gemini/GPT-4 and parse structured output.
    """
    template = PDD_TEMPLATES.get(project_type, PDD_TEMPLATES["default"])

    # Fill in template variables with plausible values
    result = {
        "project_name": project_name,
        "document_type": "PDD",
        "additionality_claim": template["additionality_claim"].format(
            rate=round(random.uniform(1.5, 4.5), 1),
            cost=random.randint(15, 45),
        ) if "{" in template["additionality_claim"] else template["additionality_claim"],
        "baseline_assumptions": template["baseline_assumptions"].format(
            rate=round(random.uniform(1.0, 5.0), 1),
            tco2=random.randint(40, 120),
            kg=random.randint(80, 250),
        ) if "{" in template["baseline_assumptions"] else template["baseline_assumptions"],
        "leakage_risk": template["leakage_risk"].format(
            pct=random.randint(3, 15),
            level=random.choice(["low", "moderate"]),
        ) if "{" in template["leakage_risk"] else template["leakage_risk"],
        "co_benefits": random.sample(template["co_benefits"], k=min(3, len(template["co_benefits"]))),
        "monitoring_plan": template["monitoring_plan"].format(
            years=random.choice([2, 3, 5]),
        ) if "{" in template["monitoring_plan"] else template["monitoring_plan"],
        "crediting_period": f"{random.choice([20, 25, 30])} years",
        "estimated_annual_reductions": f"{random.randint(10000, 500000)} tCO2e",
        "extraction_confidence": round(random.uniform(0.78, 0.96), 2),
    }

    # Index in vector service for similarity search
    full_text = f"{project_name}. {result['additionality_claim']} {result['baseline_assumptions']} {result['monitoring_plan']}"
    vector_service.add_document(
        doc_id=f"pdd_{project_name[:30].replace(' ', '_').lower()}",
        title=f"PDD: {project_name}",
        text=full_text,
        metadata={"project_type": project_type, "country": country},
    )

    return result


def extract_monitoring_report(project_name: str, project_type: str) -> dict:
    """Simulate extraction from a monitoring report."""
    return {
        "project_name": project_name,
        "document_type": "Monitoring Report",
        "reporting_period": f"Jan {random.randint(2022, 2024)} - Dec {random.randint(2023, 2025)}",
        "verified_reductions": f"{random.randint(5000, 300000)} tCO2e",
        "deviation_from_baseline": f"{random.uniform(-15, 10):.1f}%",
        "monitoring_gaps": random.choice([
            "None identified",
            "Minor gap in fire monitoring during rainy season",
            "GPS coordinate update needed for plot #12",
        ]),
        "community_engagement_score": round(random.uniform(60, 95), 1),
        "extraction_confidence": round(random.uniform(0.72, 0.92), 2),
    }
