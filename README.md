# 🛡️ ChurnShield — Insurance Customer Retention AI

**AI-powered churn risk analyzer for insurance agents**

Live demo → [ai-project-ru7tgaiumdr9qnf2pysyfz.streamlit.app](https://ai-project-ru7tgaiumdr9qnf2pysyfz.streamlit.app)

---

## The Problem

Insurance agents lose 15–25% of their book of business annually to churn. The challenge: agents manage hundreds of policies and have no systematic way to identify which customers are at risk before renewal — so they only find out when it's too late.

## The Solution

ChurnShield uses Claude AI to analyze customer risk signals drawn from 7 years of insurance industry experience. Agents input customer data and instantly get a risk assessment, follow-up action plan, and bundle opportunity — so they can prioritize outreach before the renewal date.

---

## Features

| Feature | Description |
|---|---|
| **Single Analysis** | Input a customer profile and get an AI risk assessment in seconds |
| **Bulk Upload** | Upload an Excel file to analyze an entire book of business at once |
| **Renewal Alerts** | Flags HIGH risk customers renewing within 30 days |
| **Session History** | Persistent database tracks all analyzed customers over time |
| **Dashboard** | Visual breakdown of risk distribution, policy types, premium changes, and renewal timeline |
| **Export** | Download results to Excel for CRM upload or team sharing |
| **Privacy by Design** | Bulk upload results are session-only and never persisted to the database |

---

## Risk Signals Used

Based on real patterns observed in insurance retention:

- **Premium increase %** — especially 25%+ increases driven by at-fault claims
- **At-fault claims (last 3 years)** — strongest predictor of dissatisfaction
- **Bundle status** — single-policy customers churn at 2x the rate of bundled customers
- **Payment record** — late payments signal financial stress or disengagement
- **Last contact date** — customers not contacted in 6+ months are significantly more likely to shop
- **Renewal date** — urgency window for outreach

---

## Product Design Decisions

**Why session-only for bulk upload?**
In a shared deployment, storing bulk upload data would expose one agency's customer PII to other users. Bulk results stay in-browser only. For production use, each agency would need their own authenticated deployment.

**Why upsert by policy number?**
Re-analyzing a customer (e.g. after a new claim) should update their record, not create duplicates. The database uses policy number as the unique key.

**Why Claude Haiku?**
Speed matters for agents mid-call. Haiku returns results in ~2 seconds vs. 8–10 seconds for larger models, with no meaningful quality difference for structured risk assessment tasks.

---

## Tech Stack

- **Frontend**: Streamlit
- **AI**: Anthropic Claude API (claude-haiku-4-5)
- **Database**: SQLite (persistent across sessions)
- **Data**: Pandas, openpyxl
- **Charts**: Plotly

---

## Run Locally

```bash
git clone https://github.com/nerohan96-source/ai-project.git
cd ai-project
pip install -r requirements.txt

# Set your API key
$env:ANTHROPIC_API_KEY = "your-key-here"

streamlit run app.py
```

---

## About

Built by **Nero Han** — USC Marshall MBA 2027 candidate with 7 years of insurance industry experience.

This project was built to demonstrate applied AI product thinking: identifying a real workflow pain point, selecting the right signals from domain expertise, and shipping a working tool — not just a prototype.

For production deployment, recommended additions:
- User authentication (per-agency login)
- Row-level data isolation
- CRM integration (Salesforce / HubSpot)
- Email/SMS reminder automation

---

*Powered by [Claude AI](https://anthropic.com) · Built with [Streamlit](https://streamlit.io)*
