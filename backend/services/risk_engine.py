"""
CarbonIQ - Risk Engine Service
Computes composite risk scores for carbon projects using:
- Wildfire proximity (haversine-based)
- Deforestation rate (country-level model)
- Political risk (country index)
- Additionality (methodology scoring)
- Reversal risk (buffer pool + audit history)
"""
import math
import random
from datetime import datetime, timezone


# ─── Country-Level Risk Indices ──────────────────────────────────
POLITICAL_RISK_INDEX = {
    "Brazil": 55, "Indonesia": 60, "Democratic Republic of Congo": 82,
    "Kenya": 52, "India": 45, "Peru": 48, "Colombia": 50,
    "Cambodia": 65, "Myanmar": 85, "Vietnam": 42,
    "Mexico": 52, "Guatemala": 58, "Tanzania": 48,
    "Mozambique": 62, "Ghana": 38, "Ethiopia": 68,
    "Malaysia": 35, "Philippines": 50, "Papua New Guinea": 58,
    "Chile": 28, "Uruguay": 22, "Costa Rica": 20,
    "United States": 18, "Canada": 12, "Australia": 15,
    "China": 45, "Thailand": 40, "Nigeria": 72,
}

DEFORESTATION_BASELINE = {
    "Brazil": 3.2, "Indonesia": 4.5, "Democratic Republic of Congo": 2.8,
    "Kenya": 1.5, "India": 1.2, "Peru": 2.1, "Colombia": 2.5,
    "Cambodia": 5.1, "Myanmar": 3.8, "Vietnam": 1.0,
    "Mexico": 1.4, "Guatemala": 2.3, "Tanzania": 1.8,
    "Mozambique": 2.0, "Ghana": 2.2, "Ethiopia": 1.6,
    "Malaysia": 3.0, "Philippines": 1.9, "Papua New Guinea": 1.7,
}

# Simulated wildfire hotspot coordinates (lat, lon)
WILDFIRE_HOTSPOTS = [
    (-3.5, -60.0),   # Amazon
    (-8.0, -63.0),   # Rondônia
    (-12.0, -55.0),  # Mato Grosso
    (-1.0, 116.0),   # Borneo
    (0.5, 110.0),    # West Kalimantan
    (-2.5, 30.0),    # Congo Basin
    (37.0, -122.0),  # California
    (-33.0, 150.0),  # Australia
    (62.0, 130.0),   # Siberia
    (-15.0, -48.0),  # Cerrado
]

# Additionality scoring by methodology type
METHODOLOGY_ADDITIONALITY = {
    "VM0007": 72, "VM0009": 78, "VM0015": 65, "VM0037": 80,
    "VM0006": 70, "VM0010": 85, "ACM0002": 82, "AMS-I.D": 88,
    "AMS-II.G": 90, "AMS-III.AV": 75, "GS-Cookstove": 85,
    "GS-Water": 80, "AR-ACM0003": 68, "CDM-Meth": 60,
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points."""
    R = 6371.0
    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = math.sin(dlat / 2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def compute_wildfire_risk(lat: float, lon: float) -> float:
    """Score 0-100 based on proximity to known wildfire hotspots."""
    if lat is None or lon is None:
        return 30.0  # Default moderate risk for unknown locations

    min_distance = min(
        haversine_distance(lat, lon, hlat, hlon)
        for hlat, hlon in WILDFIRE_HOTSPOTS
    )

    # Convert distance to risk score (closer = higher risk)
    if min_distance < 50:
        return min(95.0, 95 - (min_distance * 0.1))
    elif min_distance < 200:
        return 70 - ((min_distance - 50) / 150) * 30
    elif min_distance < 500:
        return 40 - ((min_distance - 200) / 300) * 20
    elif min_distance < 1000:
        return 20 - ((min_distance - 500) / 500) * 10
    else:
        return max(5.0, 10 - (min_distance / 5000) * 5)


def compute_deforestation_risk(country: str, project_type: str) -> float:
    """Annual deforestation rate risk for NBS projects."""
    base_rate = DEFORESTATION_BASELINE.get(country, 1.5)

    # NBS projects are more sensitive
    if project_type in ["REDD+", "ARR", "Mangrove Restoration", "Afforestation"]:
        multiplier = 1.5
    else:
        multiplier = 0.3  # Non-land-use projects have minimal deforestation risk

    # Add some variance
    jitter = random.uniform(-0.3, 0.3)
    rate = (base_rate * multiplier) + jitter

    # Normalize to 0-100 scale
    return min(100.0, max(0.0, rate * 12))


def compute_political_risk(country: str) -> float:
    """Country-level political/governance risk."""
    return float(POLITICAL_RISK_INDEX.get(country, 50))


def compute_additionality(methodology: str, buffer_pool_percent: float) -> float:
    """Additionality score based on methodology rigor and buffer pool."""
    base_score = METHODOLOGY_ADDITIONALITY.get(methodology, 65)

    # Buffer pool contribution
    if buffer_pool_percent >= 20:
        buffer_bonus = 10
    elif buffer_pool_percent >= 10:
        buffer_bonus = 5
    else:
        buffer_bonus = -5

    return min(100.0, max(0.0, float(base_score + buffer_bonus + random.uniform(-3, 3))))


def compute_reversal_risk(
    buffer_pool_percent: float,
    wildfire_score: float,
    political_score: float,
    has_reversal_events: bool = False,
    project_type: str = ""
) -> float:
    """Probability of credit reversal (invalidation)."""
    # NBS projects have inherently higher reversal risk
    base_risk = 20.0
    if project_type in ["REDD+", "ARR", "Mangrove Restoration", "Afforestation"]:
        base_risk = 35.0

    # Buffer pool reduces risk
    buffer_reduction = min(buffer_pool_percent * 0.8, 25.0)

    # Environmental factors increase risk
    env_factor = (wildfire_score * 0.3 + political_score * 0.2) * 0.4

    # Historical reversals dramatically increase risk
    reversal_penalty = 25.0 if has_reversal_events else 0.0

    risk = base_risk - buffer_reduction + env_factor + reversal_penalty
    return min(100.0, max(0.0, risk + random.uniform(-2, 2)))


def compute_buffer_pool_health(buffer_pool_percent: float, reversal_risk: float) -> float:
    """Health of the buffer pool relative to risk exposure."""
    if buffer_pool_percent <= 0:
        return 10.0

    # Ideal buffer is proportional to reversal risk
    ideal_buffer = reversal_risk * 0.4
    if ideal_buffer <= 0:
        return 90.0

    ratio = buffer_pool_percent / ideal_buffer
    health = min(100.0, ratio * 80)
    return max(0.0, health)


def compute_overall_risk_rating(composite: float) -> str:
    """Convert composite score to rating category."""
    if composite >= 70:
        return "CRITICAL"
    elif composite >= 50:
        return "HIGH"
    elif composite >= 30:
        return "MEDIUM"
    else:
        return "LOW"


def compute_composite_risk(
    wildfire: float,
    deforestation: float,
    political: float,
    additionality: float,
    reversal: float,
    buffer_health: float
) -> float:
    """
    Weighted composite risk score.
    Lower additionality & buffer health = higher risk.
    """
    weights = {
        "wildfire": 0.15,
        "deforestation": 0.15,
        "political": 0.15,
        "reversal": 0.25,
        "additionality_inverse": 0.15,  # Invert: low additionality = high risk
        "buffer_inverse": 0.15,         # Invert: low buffer health = high risk
    }

    composite = (
        wildfire * weights["wildfire"]
        + deforestation * weights["deforestation"]
        + political * weights["political"]
        + reversal * weights["reversal"]
        + (100 - additionality) * weights["additionality_inverse"]
        + (100 - buffer_health) * weights["buffer_inverse"]
    )

    return round(min(100.0, max(0.0, composite)), 2)


def compute_full_risk(project, audits=None) -> dict:
    """
    Compute all risk signals for a project.
    Returns dict ready for RiskSignal creation.
    """
    has_reversals = False
    if audits:
        has_reversals = any(a.reversal_event for a in audits)

    wildfire = compute_wildfire_risk(project.latitude, project.longitude)
    deforestation = compute_deforestation_risk(project.country, project.project_type)
    political = compute_political_risk(project.country)
    additionality = compute_additionality(
        project.methodology or "CDM-Meth",
        project.buffer_pool_percent or 0
    )
    reversal = compute_reversal_risk(
        project.buffer_pool_percent or 0,
        wildfire,
        political,
        has_reversals,
        project.project_type
    )
    buffer_health = compute_buffer_pool_health(
        project.buffer_pool_percent or 0,
        reversal
    )
    composite = compute_composite_risk(
        wildfire, deforestation, political, additionality, reversal, buffer_health
    )
    rating = compute_overall_risk_rating(composite)

    return {
        "project_id": project.id,
        "wildfire_proximity": round(wildfire, 2),
        "deforestation_rate": round(deforestation, 2),
        "political_risk_score": round(political, 2),
        "additionality_score": round(additionality, 2),
        "reversal_risk": round(reversal, 2),
        "buffer_pool_health": round(buffer_health, 2),
        "overall_risk_rating": rating,
        "composite_score": composite,
    }
