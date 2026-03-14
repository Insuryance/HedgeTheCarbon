"""
CarbonIQ - Crawler Service
Simulates registry data ingestion from Verra, Gold Standard, ACR, and CAR.
Generates realistic carbon project data for demo purposes.
"""
import random
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models import Project, Vintage, CrawlRun
from services.risk_engine import compute_full_risk
from models import RiskSignal


# ─── Realistic Project Templates ─────────────────────────────────

PROJECT_TEMPLATES = [
    # REDD+ Projects
    {"name": "Pacajaí REDD+ Forest Conservation", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0007", "country": "Brazil", "region": "Pará",
     "lat": -3.8, "lon": -50.7, "developer": "Biofílica", "buffer": 22.0,
     "desc": "Avoided planned deforestation in the Brazilian Amazon, protecting 90,000 hectares of tropical rainforest."},
    {"name": "Rimba Raya Biodiversity Reserve", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0007", "country": "Indonesia", "region": "Central Kalimantan",
     "lat": -2.9, "lon": 112.0, "developer": "InfiniteEARTH", "buffer": 25.0,
     "desc": "Protecting 65,000 hectares of tropical peat swamp forest on the island of Borneo."},
    {"name": "Mai Ndombe REDD+ Project", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0009", "country": "Democratic Republic of Congo", "region": "Mai-Ndombe",
     "lat": -2.1, "lon": 18.3, "developer": "Wildlife Works", "buffer": 18.0,
     "desc": "Community-based avoided deforestation in the Congo Basin, covering 300,000 hectares."},
    {"name": "Kasigau Corridor REDD Project", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0009", "country": "Kenya", "region": "Coast Province",
     "lat": -3.7, "lon": 38.6, "developer": "Wildlife Works", "buffer": 20.0,
     "desc": "Protecting dryland forest corridor between Tsavo East and Tsavo West National Parks."},
    {"name": "Cordillera Azul National Park", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0015", "country": "Peru", "region": "San Martín",
     "lat": -7.3, "lon": -76.0, "developer": "CIMA", "buffer": 15.0,
     "desc": "Preventing deforestation in 1.35 million hectares of Amazonian forest in Peru."},

    # Renewable Energy
    {"name": "Bhadla Solar Park Phase III", "registry": "Gold Standard", "project_type": "Solar",
     "methodology": "AMS-I.D", "country": "India", "region": "Rajasthan",
     "lat": 27.5, "lon": 71.9, "developer": "ACME Solar", "buffer": 0.0,
     "desc": "225 MW solar photovoltaic power plant in the Thar Desert."},
    {"name": "Jaisalmer Wind Farm Cluster", "registry": "Gold Standard", "project_type": "Wind",
     "methodology": "ACM0002", "country": "India", "region": "Rajasthan",
     "lat": 26.9, "lon": 70.9, "developer": "Suzlon Energy", "buffer": 0.0,
     "desc": "500 MW onshore wind power generation across Jaisalmer district."},
    {"name": "Lake Turkana Wind Power", "registry": "Gold Standard", "project_type": "Wind",
     "methodology": "ACM0002", "country": "Kenya", "region": "Marsabit",
     "lat": 2.4, "lon": 36.8, "developer": "LTWP", "buffer": 0.0,
     "desc": "310 MW wind farm providing 17% of Kenya's installed capacity."},

    # Cookstoves
    {"name": "UpEnergy Clean Cookstoves Uganda", "registry": "Gold Standard", "project_type": "Cookstoves",
     "methodology": "GS-Cookstove", "country": "Kenya", "region": "Nairobi",
     "lat": -1.3, "lon": 36.8, "developer": "UpEnergy", "buffer": 0.0,
     "desc": "Distribution of fuel-efficient cookstoves reducing indoor air pollution and deforestation."},
    {"name": "BioLite HomeStove Distribution", "registry": "Gold Standard", "project_type": "Cookstoves",
     "methodology": "GS-Cookstove", "country": "Ghana", "region": "Greater Accra",
     "lat": 5.6, "lon": -0.2, "developer": "BioLite", "buffer": 0.0,
     "desc": "Clean cooking technology reducing biomass fuel use by 50%."},

    # ARR (Afforestation, Reforestation)
    {"name": "Alto Huayabamba Conservation", "registry": "Verra", "project_type": "ARR",
     "methodology": "AR-ACM0003", "country": "Peru", "region": "San Martín",
     "lat": -7.6, "lon": -77.0, "developer": "Pur Projet", "buffer": 28.0,
     "desc": "Reforestation and agroforestry across 50,000 hectares of degraded land."},
    {"name": "Yarra Yarra Biodiversity Corridor", "registry": "ACR", "project_type": "ARR",
     "methodology": "AR-ACM0003", "country": "Australia", "region": "Western Australia",
     "lat": -29.3, "lon": 115.5, "developer": "Carbon Neutral", "buffer": 30.0,
     "desc": "Revegetation of 10,000 hectares of cleared farmland in the Western Australian wheatbelt."},

    # Mangrove
    {"name": "Mikoko Pamoja Mangrove Project", "registry": "Verra", "project_type": "Mangrove Restoration",
     "methodology": "VM0007", "country": "Kenya", "region": "Kwale",
     "lat": -4.4, "lon": 39.5, "developer": "ACES", "buffer": 20.0,
     "desc": "Community-led mangrove conservation and restoration protecting 117 hectares of coastal forest."},
    {"name": "Cispatá Mangrove Blue Carbon", "registry": "Verra", "project_type": "Mangrove Restoration",
     "methodology": "VM0007", "country": "Colombia", "region": "Córdoba",
     "lat": 9.4, "lon": -75.8, "developer": "CI Colombia", "buffer": 22.0,
     "desc": "Protection of 11,000 hectares of mangrove ecosystem in the Gulf of Morrosquillo."},

    # Biochar
    {"name": "Pacific Biochar Carbon Removal", "registry": "ACR", "project_type": "Biochar",
     "methodology": "VM0037", "country": "United States", "region": "California",
     "lat": 38.5, "lon": -122.5, "developer": "Pacific Biochar", "buffer": 5.0,
     "desc": "Biochar production from agricultural waste, sequestering carbon in stable form for 1000+ years."},

    # Water purification
    {"name": "LifeStraw Carbon for Water", "registry": "Gold Standard", "project_type": "Water Purification",
     "methodology": "GS-Water", "country": "Kenya", "region": "Western Kenya",
     "lat": 0.3, "lon": 34.8, "developer": "Vestergaard", "buffer": 0.0,
     "desc": "Household water purifiers eliminating need for boiling water, reducing firewood consumption."},

    # More REDD+ for diversity
    {"name": "Southern Cardamom REDD+", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0009", "country": "Cambodia", "region": "Koh Kong",
     "lat": 11.3, "lon": 103.8, "developer": "WCS", "buffer": 16.0,
     "desc": "Protecting 445,000 hectares of lowland evergreen forest in the Cardamom Mountains."},
    {"name": "Madre de Dios Amazon REDD", "registry": "Verra", "project_type": "REDD+",
     "methodology": "VM0007", "country": "Peru", "region": "Madre de Dios",
     "lat": -12.0, "lon": -69.5, "developer": "Bosques Amazónicos", "buffer": 19.0,
     "desc": "Avoiding deforestation of 100,000 hectares in the most biodiverse region on Earth."},

    # CAR registry
    {"name": "Garcia River Forest Carbon", "registry": "CAR", "project_type": "ARR",
     "methodology": "VM0006", "country": "United States", "region": "California",
     "lat": 38.9, "lon": -123.6, "developer": "TNC", "buffer": 18.0,
     "desc": "Improved forest management on 24,000 acres of coastal redwood forest."},
    {"name": "Colville Tribal Forest", "registry": "CAR", "project_type": "REDD+",
     "methodology": "VM0006", "country": "United States", "region": "Washington",
     "lat": 48.2, "lon": -118.5, "developer": "Colville Tribes", "buffer": 20.0,
     "desc": "Improved forest management across 1.4 million acres of tribal forest lands."},
]

VVB_NAMES = [
    "RINA", "SCS Global", "Earthood", "S&A Carbon", "TÜV SÜD",
    "TÜV NORD", "Bureau Veritas", "DNV", "Aster Global", "AENOR",
]


def _generate_vintages(project_id: str, project_type: str) -> list:
    """Generate 3-5 vintages with realistic volumes and pricing."""
    num_vintages = random.randint(3, 5)
    base_year = random.randint(2018, 2022)

    # Price ranges by project type
    price_ranges = {
        "REDD+": (4.0, 18.0), "ARR": (8.0, 25.0),
        "Cookstoves": (3.0, 8.0), "Wind": (1.5, 5.0),
        "Solar": (1.0, 4.5), "Mangrove Restoration": (12.0, 35.0),
        "Biochar": (80.0, 150.0), "Water Purification": (3.0, 7.0),
    }
    price_min, price_max = price_ranges.get(project_type, (3.0, 15.0))

    vintages = []
    for i in range(num_vintages):
        year = base_year + i
        volume = random.randint(10000, 2000000)
        retired_pct = random.uniform(0.1, 0.85)
        retired = int(volume * retired_pct)
        available = volume - retired
        price = round(random.uniform(price_min, price_max), 2)
        velocity = round(retired_pct * 100 / max(1, (2025 - year)), 1)

        vintages.append({
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "issuance_year": year,
            "total_volume": volume,
            "retired_volume": retired,
            "available_volume": available,
            "retirement_velocity": velocity,
            "price_per_tonne": price,
        })

    return vintages


def _generate_audits(project_id: str) -> list:
    """Generate 1-3 realistic audit records."""
    num_audits = random.randint(1, 3)
    audits = []

    for i in range(num_audits):
        audit_date = datetime.now(timezone.utc) - timedelta(days=random.randint(90, 900))
        has_reversal = random.random() < 0.08  # 8% chance of reversal event
        quality = random.uniform(55, 95)

        findings = random.choice([
            "No material findings. Project operating within parameters.",
            "Minor non-conformity in monitoring methodology. Corrective action requested.",
            "Baseline recalculation required due to updated deforestation data.",
            "Leakage assessment methodology needs strengthening.",
            "Co-benefit claims verified. Community engagement documented.",
            "Buffer pool contribution confirmed. No reversals detected.",
            "Satellite imagery confirms forest cover maintained within project boundary.",
        ])

        if has_reversal:
            findings = "MATERIAL FINDING: Partial reversal event detected. Buffer pool credits cancelled."
            quality = random.uniform(30, 55)

        audits.append({
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "vvb_name": random.choice(VVB_NAMES),
            "audit_date": audit_date,
            "audit_type": random.choice(["validation", "verification", "verification"]),
            "findings_summary": findings,
            "reversal_event": has_reversal,
            "corrective_actions": "N/A" if not has_reversal else "Buffer pool credits cancelled per registry rules.",
            "audit_quality_score": round(quality, 1),
        })

    return audits


def run_crawl(db: Session, registries: list = None) -> dict:
    """
    Simulate a full registry crawl.
    Populates database with realistic carbon project data.
    Returns crawl run summary.
    """
    if registries is None:
        registries = ["Verra", "Gold Standard", "ACR", "CAR"]

    from models import Audit as AuditModel

    results = []

    for registry in registries:
        crawl_run = CrawlRun(
            id=str(uuid.uuid4()),
            registry=registry,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(crawl_run)
        db.flush()

        templates = [t for t in PROJECT_TEMPLATES if t["registry"] == registry]
        new_count = 0
        updated_count = 0

        for tmpl in templates:
            # Check if project already exists by name
            existing = db.query(Project).filter(Project.name == tmpl["name"]).first()
            if existing:
                updated_count += 1
                continue

            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                registry=tmpl["registry"],
                registry_id=f"{tmpl['registry'][:3].upper()}-{random.randint(1000, 9999)}",
                name=tmpl["name"],
                developer=tmpl["developer"],
                methodology=tmpl["methodology"],
                project_type=tmpl["project_type"],
                country=tmpl["country"],
                region=tmpl["region"],
                latitude=tmpl["lat"],
                longitude=tmpl["lon"],
                buffer_pool_percent=tmpl["buffer"],
                status="active",
                co_benefits=str(random.sample([
                    "Biodiversity", "Community Development", "Clean Water",
                    "Education", "Employment", "Health", "Gender Equality"
                ], k=random.randint(2, 4))),
                description=tmpl["desc"],
            )
            db.add(project)
            db.flush()

            # Generate vintages
            for v_data in _generate_vintages(project_id, tmpl["project_type"]):
                db.add(Vintage(**v_data))

            # Generate audits
            audit_objects = []
            for a_data in _generate_audits(project_id):
                audit = AuditModel(**a_data)
                db.add(audit)
                audit_objects.append(audit)

            db.flush()

            # Compute risk signals
            risk_data = compute_full_risk(project, audit_objects)
            db.add(RiskSignal(**risk_data))

            new_count += 1

        crawl_run.status = "completed"
        crawl_run.projects_found = len(templates)
        crawl_run.projects_new = new_count
        crawl_run.projects_updated = updated_count
        crawl_run.completed_at = datetime.now(timezone.utc)

        results.append({
            "registry": registry,
            "found": len(templates),
            "new": new_count,
            "updated": updated_count,
        })

    db.commit()

    return {
        "status": "completed",
        "registries_crawled": len(registries),
        "results": results,
        "total_new": sum(r["new"] for r in results),
        "total_updated": sum(r["updated"] for r in results),
    }
