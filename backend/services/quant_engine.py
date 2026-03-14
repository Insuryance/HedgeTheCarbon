"""
CarbonIQ - Quant Engine Service
Fair-value pricing, arbitrage detection, and portfolio valuation.

Fair Value Formula:
  FV = (MarketPrice × ReliabilityScore) − (LiquidityDiscount + ReversalRiskPremium)
"""
from typing import List, Dict, Any, Optional


def compute_reliability_score(
    additionality_score: float,
    audit_quality_score: float,
    buffer_pool_percent: float
) -> float:
    """
    Reliability = weighted combination of credit quality factors.
    Output: 0.0 to 1.5 multiplier (>1.0 means premium, <1.0 means discount).
    """
    # Normalize inputs to 0-1 range
    add_norm = additionality_score / 100.0
    audit_norm = audit_quality_score / 100.0
    buffer_norm = min(buffer_pool_percent / 30.0, 1.0)  # 30%+ buffer is ideal

    weighted = (add_norm * 0.40) + (audit_norm * 0.35) + (buffer_norm * 0.25)

    # Scale to 0.5 - 1.3 range (never more than 1.3x premium)
    return 0.5 + (weighted * 0.8)


def compute_liquidity_discount(
    retirement_velocity: float,
    total_volume: int,
    available_volume: int
) -> float:
    """
    Illiquid credits should be discounted.
    Returns discount in USD per tonne.
    """
    # Low retirement velocity = illiquid
    if retirement_velocity <= 0:
        velocity_discount = 3.0
    elif retirement_velocity < 5:
        velocity_discount = 2.0 * (1 - retirement_velocity / 5)
    else:
        velocity_discount = 0.0

    # Very small or very large volumes affect liquidity
    if total_volume < 10000:
        volume_discount = 1.5  # Micro-projects are illiquid
    elif total_volume > 5000000:
        volume_discount = 0.5  # Large projects may flood market
    else:
        volume_discount = 0.0

    # Low availability ratio
    if total_volume > 0:
        avail_ratio = available_volume / total_volume
        if avail_ratio < 0.1:
            scarcity_premium = -1.0  # Scarcity adds value
        elif avail_ratio > 0.8:
            oversupply_discount = 0.5
        else:
            scarcity_premium = 0.0
            oversupply_discount = 0.0
    else:
        scarcity_premium = 0.0
        oversupply_discount = 0.0

    total = velocity_discount + volume_discount
    if total_volume > 0 and available_volume / total_volume < 0.1:
        total -= 1.0
    elif total_volume > 0 and available_volume / total_volume > 0.8:
        total += 0.5

    return max(0.0, round(total, 2))


def compute_reversal_risk_premium(
    reversal_risk: float,
    wildfire_proximity: float,
    political_risk: float,
    project_type: str
) -> float:
    """
    Premium charged for credit reversal (invalidation) risk.
    Returns premium in USD per tonne.
    """
    # Base premium from reversal risk score
    base = (reversal_risk / 100.0) * 8.0  # Up to $8/tonne

    # Environmental risk adder
    env_risk = (wildfire_proximity / 100.0) * 2.0  # Up to $2/tonne

    # Political risk adder
    pol_risk = (political_risk / 100.0) * 1.5  # Up to $1.50/tonne

    # NBS projects carry higher reversal premium
    nbs_types = {"REDD+", "ARR", "Mangrove Restoration", "Afforestation"}
    type_multiplier = 1.3 if project_type in nbs_types else 1.0

    premium = (base + env_risk + pol_risk) * type_multiplier
    return round(min(premium, 15.0), 2)  # Cap at $15


def compute_fair_value(
    market_price: float,
    reliability_score: float,
    liquidity_discount: float,
    reversal_risk_premium: float
) -> float:
    """
    FV = (MarketPrice × ReliabilityScore) − (LiquidityDiscount + ReversalRiskPremium)
    """
    fv = (market_price * reliability_score) - (liquidity_discount + reversal_risk_premium)
    return round(max(0.01, fv), 2)


def determine_signal(alpha_percent: float, confidence: float) -> str:
    """Determine trade signal from alpha and confidence."""
    if alpha_percent > 15 and confidence > 60:
        return "STRONG BUY"
    elif alpha_percent > 5:
        return "BUY"
    elif alpha_percent < -15 and confidence > 60:
        return "STRONG SELL"
    elif alpha_percent < -5:
        return "SELL"
    else:
        return "HOLD"


def compute_confidence(
    additionality: float,
    audit_quality: float,
    data_completeness: float = 80.0
) -> float:
    """
    Confidence in the fair-value estimate.
    More data and higher quality audits = higher confidence.
    """
    conf = (additionality * 0.3 + audit_quality * 0.4 + data_completeness * 0.3)
    return round(min(100.0, max(10.0, conf)), 1)


def price_project(
    project_id: str,
    project_name: str,
    registry: str,
    project_type: str,
    market_price: float,
    additionality_score: float,
    audit_quality_score: float,
    buffer_pool_percent: float,
    retirement_velocity: float,
    total_volume: int,
    available_volume: int,
    reversal_risk: float,
    wildfire_proximity: float,
    political_risk: float,
) -> dict:
    """
    Full pricing pipeline for a single project.
    Returns FairValueResult-compatible dict.
    """
    reliability = compute_reliability_score(
        additionality_score, audit_quality_score, buffer_pool_percent
    )
    liquidity_disc = compute_liquidity_discount(
        retirement_velocity, total_volume, available_volume
    )
    reversal_prem = compute_reversal_risk_premium(
        reversal_risk, wildfire_proximity, political_risk, project_type
    )
    fair_value = compute_fair_value(
        market_price, reliability, liquidity_disc, reversal_prem
    )
    alpha = round(fair_value - market_price, 2)
    alpha_pct = round((alpha / market_price * 100) if market_price > 0 else 0, 2)
    confidence = compute_confidence(additionality_score, audit_quality_score)
    signal = determine_signal(alpha_pct, confidence)

    return {
        "project_id": project_id,
        "project_name": project_name,
        "registry": registry,
        "market_price": market_price,
        "reliability_score": round(reliability, 4),
        "liquidity_discount": liquidity_disc,
        "reversal_risk_premium": reversal_prem,
        "fair_value": fair_value,
        "alpha": alpha,
        "alpha_percent": alpha_pct,
        "signal": signal,
        "confidence": confidence,
        "breakdown": {
            "additionality_score": additionality_score,
            "audit_quality_score": audit_quality_score,
            "buffer_pool_percent": buffer_pool_percent,
            "reversal_risk": reversal_risk,
            "wildfire_proximity": wildfire_proximity,
            "political_risk": political_risk,
            "retirement_velocity": retirement_velocity,
            "total_volume": total_volume,
            "available_volume": available_volume,
        }
    }


def detect_arbitrage_opportunities(valuations: List[dict], min_alpha_pct: float = 10.0) -> List[dict]:
    """
    Find projects where fair value significantly exceeds market price.
    These represent potential alpha opportunities.
    """
    opportunities = []
    for v in valuations:
        if v["alpha_percent"] > min_alpha_pct and v["confidence"] > 40:
            opportunities.append({
                "project_id": v["project_id"],
                "project_name": v["project_name"],
                "registry": v["registry"],
                "project_type": v["breakdown"].get("project_type", ""),
                "country": "",
                "market_price": v["market_price"],
                "fair_value": v["fair_value"],
                "alpha": v["alpha"],
                "alpha_percent": v["alpha_percent"],
                "risk_rating": "",
                "signal": v["signal"],
            })

    # Sort by alpha descending
    opportunities.sort(key=lambda x: x["alpha_percent"], reverse=True)
    return opportunities
