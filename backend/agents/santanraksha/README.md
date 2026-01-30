# 👶 SantanRaksha Agents

**Child Health AI Agents for Postnatal & Pediatric Care**

## Agents in this Category

| Agent | File Location | Purpose |
|-------|---------------|---------|
| **Postnatal Agent** | `../postnatal_agent.py` | Mother's recovery (0-6 weeks), breastfeeding, mental health |
| **Pediatric Agent** | `../pediatric_agent.py` | Child illness triage (IMNCI protocols) |
| **Vaccine Agent** | `../vaccine_agent.py` | IAP 2023 immunization schedule |
| **Growth Agent** | `../growth_agent.py` | WHO growth monitoring, nutrition |

## Clinical Standards Used

- **IAP 2023** - Indian Academy of Pediatrics vaccination schedule
- **IMNCI** - Integrated Management of Neonatal & Childhood Illness
- **WHO Growth Standards** - Z-score calculations for malnutrition
- **NHM SUMAN** - Postnatal care (6 checkups in 42 days)
- **EPDS** - Edinburgh Postnatal Depression Scale
- **RBSK 4Ds** - Developmental screening

## When These Agents Are Used

These agents are active when `mother.active_system = "santanraksha"` (after delivery).
