# 🌿 HedgeTheCarbon — Hedge The Carbon

> **Pricing carbon on science, not sentiment.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Status: Building](https://img.shields.io/badge/Status-Building-brightgreen)]()
[![Market: Voluntary Carbon](https://img.shields.io/badge/Market-Voluntary%20Carbon-blue)]()
[![Alpha: Quant](https://img.shields.io/badge/Alpha-Quant%20Driven-orange)]()

---

## 🧠 What Is CarbonIQ?

**CarbonIQ** is an AI-native quant hedge fund for the Voluntary Carbon Market (VCM) — think *Renaissance Technologies meets climate finance*.

The $2B voluntary carbon market is pricing credits on vibes. Identical credits trade at **10x price differences** based on who you know and which broker you're calling. No Bloomberg terminal. No mark-to-model. No math.

**We built the math layer.**

Our AI engine scores every carbon credit like a credit rating — factoring in satellite deforestation imagery, wildfire risk, registry audit trails, buffer pool balances, and additionality verification. That score reveals the gap between what a credit is *worth* and what it's *trading for*.

**That gap is alpha.**

---

## ⚡ The Three-Layer Stack

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1 — DATA INGESTION & REGISTRY INTELLIGENCE       │
│  Verra · Gold Standard · ACR · CAR                      │
│  + Satellite imagery · Fire risk maps · Deforestation   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2 — AI QUANT PRICING ENGINE (Mark-to-Model)      │
│  Carbon Quality Score (CQS):                            │
│    → Additionality Score                                │
│    → Permanence Risk                                    │
│    → Verification Rigor                                 │
│    → Co-benefit Premium                                 │
│  Output: Fair Value Per Tonne vs. Market Price          │
├─────────────────────────────────────────────────────────┤
│  LAYER 3 — AUTONOMOUS AI AGENTS + TRADE EXECUTION       │
│  Live on dashboard · Learn the market in real time      │
│  Scan OTC feeds · Flag mispriced credits                │
│  Execute trades autonomously with full audit trail      │
└─────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Agents — Our Edge

We didn't just build a pricing model. We built **autonomous trading agents** that:

- 🔍 **Scan** — Continuously monitor Xpansiv/CBL exchange feeds, OTC broker quotes, and live registry issuances
- 🧮 **Score** — Re-score every credit against our Carbon Quality Score (CQS) in real time
- 📊 **Learn** — Agents update their priors from market movements, buffer pool stress events, and satellite signals
- ⚡ **Execute** — Flag and execute trades autonomously. Long high-CQS, short low-CQS. Human in loop only for final sign-off (for now)
- 📋 **Report** — Auto-generate trade memos with confidence scores and risk attribution

---

## 📈 Alpha Sources

| Alpha Source | Mechanism |
|---|---|
| **Quality Mispricing** | Low-CQS credits at parity with high-CQS → short low, long high |
| **Vintage Curve Arb** | Older vintages systematically mispriced vs. newer same-project |
| **Buffer Pool Stress** | Fire/drought signals → predict drawdowns before market reprices |
| **Registry Issuance Lag** | New issuances take weeks to hit secondary — front-run the float |
| **Co-benefit Premium** | CORSIA/Article 6 eligible credits at discount → structural long |

---

## 📊 Market Timing

| Segment | Today | 2030 |
|---|---|---|
| Voluntary Carbon Market | ~$2B | $50B+ |
| Nature-Based Solutions | ~$800M | $20B+ |
| CORSIA Aviation Demand | Pre-compliance | $5–10B/yr from 2027 |
| Article 6 Bilateral Deals | Nascent | $30B+ potential |

> **CORSIA aviation compliance kicks in 2027. Article 6 rulebook settled at COP29. The market is about to institutionalize. First quant fund in the room wins.**

---

## 🏗️ Repository Structure

```
HedgeTheCarbon/
├── ingestion/          # Registry crawlers: Verra, Gold Standard, ACR, CAR
├── scoring/            # Carbon Quality Score (CQS) engine
│   ├── additionality/
│   ├── permanence/
│   ├── verification/
│   └── cobenefits/
├── pricing/            # Mark-to-model fair value engine
├── agents/             # Autonomous trading agents + dashboard integration
│   ├── scanner/
│   ├── executor/
│   └── reporter/
├── data/               # Satellite signals, fire risk, deforestation datasets
├── dashboard/          # Live monitoring UI
└── docs/               # Research, methodology, trade memos
```

---

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/Insuryance/HedgeTheCarbon.git
cd HedgeTheCarbon

# Install dependencies
pip install -r requirements.txt

# Run the data ingestion pipeline
python ingestion/run_crawlers.py

# Score a universe of active projects
python scoring/score_universe.py

# Launch the agent dashboard
python agents/dashboard.py
```

---

## 🛰️ Data Sources

- **[Verra Registry](https://registry.verra.org/)** — VCS project database, issuances, retirements
- **[Gold Standard Registry](https://registry.goldstandard.org/)** — GS4GG credits
- **[American Carbon Registry](https://americancarbonregistry.org/)** — ACR project data
- **[Xpansiv/CBL](https://xpansiv.com/)** — Spot market price feeds
- **NASA FIRMS** — Wildfire and burn area data
- **Global Forest Watch** — Deforestation signals
- **PRODES/INPE** — Amazon deforestation monitoring

---

## 🧬 The Carbon Quality Score (CQS)

Every credit in our universe gets a proprietary **CQS** from 0–100:

```
CQS = w₁(Additionality) + w₂(Permanence) + w₃(Verification) + w₄(Co-benefit)

Where:
  Additionality  → Was this carbon actually additional?
  Permanence     → Buffer pool adequacy + fire/drought exposure + political risk
  Verification   → Third-party auditor track record + methodology vintage
  Co-benefit     → Biodiversity, community, water — Article 6 / CORSIA premium
```

**Fair Value spread = CQS-implied price − market price = Alpha signal**

---

## 🌍 Why This Matters

The voluntary carbon market is the financing mechanism for the world's most critical nature conservation and climate projects. When credits are mispriced, bad projects get funded and good ones don't.

CarbonIQ doesn't just generate alpha — **it pushes capital toward integrity**.

---

## 👥 Team

Built by [Insuryance](https://github.com/Insuryance) — at the intersection of quantitative finance, climate science, and AI.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

> *"The market is pricing carbon on sentiment. We're pricing it on science."*
>
> **— HedgeTheCarbon**
