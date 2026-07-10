# Product Requirements Document
## ChurnShield — AI-Powered Insurance Customer Retention Tool

**Author:** Nero Han  
**Version:** 1.0  
**Date:** July 2026  
**Status:** Live (MVP)

---

## 1. Problem Statement

Insurance agents manage hundreds of policies simultaneously but have no systematic way to identify which customers are at risk of churning before renewal. Without prioritization, agents treat all customers equally — contacting low-risk customers while missing high-risk ones until it's too late.

**Core pain point:** Agents don't know which customers to follow up with first.

The result: 15–25% annual churn across the industry, with most customer losses happening silently before the agent even realizes the customer was at risk.

---

## 2. Target Users

**Primary:** Independent insurance agents and agency managers  
**Secondary:** Retention teams at mid-size insurance carriers

**User profile:**
- Manages 200–500 active policies
- Spends 60%+ of time on reactive service, not proactive retention
- Has industry intuition about churn signals but no structured tool to apply it at scale
- Not technical — needs a simple UI, not a data dashboard

---

## 3. User Stories

| As a... | I want to... | So that... |
|---|---|---|
| Insurance agent | Quickly assess a customer's churn risk | I can prioritize my follow-up calls |
| Insurance agent | Upload my entire book of business | I can identify all at-risk customers at once |
| Insurance agent | See why a customer is high risk | I can trust the AI's judgment and act on it |
| Agency manager | Track risk trends across all customers | I can allocate team resources effectively |
| Insurance agent | Get reminded before high-risk customers renew | I never miss a critical outreach window |

---

## 4. Goals & Success Metrics

**North Star Metric:** High-risk customer follow-up rate  
*(% of HIGH risk customers contacted within 7 days of being flagged)*

**Supporting Metrics:**

| Metric | Target |
|---|---|
| High-risk follow-up rate | >80% within 7 days |
| Time to complete risk assessment | <10 seconds per customer |
| Bulk analysis throughput | 50+ customers per session |
| Agent trust score (self-reported) | >7/10 |

**Guardrail Metrics:**
- AI hallucination rate (factually wrong risk factors) < 5%
- False HIGH risk rate < 15% (agent override rate as proxy)

---

## 5. Risk Signals & Logic

Based on 7 years of insurance industry experience, the following signals are weighted in the risk model:

| Signal | Risk Contribution |
|---|---|
| Premium increase >25% | High |
| At-fault claims (2+ in 3 years) | High |
| Single policy, no bundle | Medium-High |
| Last contact 6+ months ago | Medium |
| Frequently late payments | Medium |
| Policy duration <1 year | Medium |
| Renewal within 30 days | Urgency multiplier |

---

## 6. Feature Requirements

### 6.1 Single Customer Analysis
- Agent inputs customer profile (name, policy type, premium change, claims, bundle status, payment record, last contact, renewal date)
- AI returns: risk level (HIGH/MEDIUM/LOW), structured risk factors with thresholds, follow-up action plan, bundle opportunity, auto-reminder recommendation
- Results saved to persistent database (deduplicated by policy number)

### 6.2 Bulk Upload
- Agent uploads Excel file with customer data
- System processes all customers in batch with progress indicator
- Results displayed with risk-level grouping and urgent renewal alerts
- **Privacy:** Bulk results are session-only, never persisted to shared database

### 6.3 Explainability Module
- Every risk assessment displays the specific signals that triggered the rating
- Each signal shows the threshold that was crossed (e.g. "Premium +40% — threshold: >25%")
- Rationale: agents won't act on AI recommendations they don't understand

### 6.4 Renewal Alert System
- Dashboard and sidebar surface HIGH risk customers renewing within 30 days
- Sorted by urgency (days to renewal)
- Designed to answer: "Who do I call today?"

### 6.5 Policy Document RAG
- Agents can upload their agency's underwriting rules, product guidelines, or claims policies
- AI references these documents when generating risk assessments
- Provides more accurate, company-specific recommendations
- Documents are session-only for privacy

### 6.6 Dashboard
- Risk distribution (pie chart)
- Risk by policy type (bar chart)
- Premium change vs. risk correlation
- Customers by carrier
- Upcoming renewal timeline by risk level

---

## 7. Design Decisions & Rationale

**Why session-only for bulk upload?**  
In a shared cloud deployment, persisting bulk upload data would expose one agency's customer PII to other users. Bulk results stay in-browser only. Production deployment would require per-agency authentication and row-level data isolation.

**Why upsert by policy number?**  
Re-analyzing the same customer (e.g. after a new claim) should update their record, not create duplicates. Policy number is used as the unique key to prevent history pollution.

**Why Claude Haiku over larger models?**  
Speed matters when agents are mid-call or reviewing multiple customers. Haiku returns results in ~2 seconds vs. 8–10 seconds for Opus, with no meaningful quality difference for structured risk assessment tasks.

**Why JSON + narrative (not just narrative)?**  
Structured JSON output allows the app to render risk factors as visual cards and extract risk levels programmatically. This also demonstrates AI explainability — a key trust signal for agent adoption.

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| AI misclassifies risk level | Agent acts on wrong priority | Explainability module shows reasoning; agent can override |
| Data privacy breach (bulk upload) | PII exposed to other users | Bulk results are session-only, never written to DB |
| Agent doesn't trust AI output | Low adoption | Show signal + threshold for every risk factor |
| Streamlit Cloud DB resets | Loss of history | Warn users; production version should use persistent cloud DB |
| API cost at scale | Expensive for large agencies | Haiku model minimizes cost; bulk analysis batched efficiently |

---

## 9. Out of Scope (V1)

- User authentication / multi-tenant architecture
- CRM integration (Salesforce, HubSpot)
- Email/SMS automated outreach
- Mobile app
- Real-time policy data sync from carrier systems

---

## 10. Future Roadmap

| Version | Feature |
|---|---|
| V2 | User login + per-agent data isolation |
| V2 | CRM integration for one-click follow-up logging |
| V3 | Outcome tracking (did the customer renew after outreach?) |
| V3 | Model fine-tuning based on actual retention outcomes |
| V4 | Carrier API integration for real-time policy data |

---

## 11. Launch Checklist

- [x] Single customer analysis with AI risk assessment
- [x] Bulk Excel upload with batch processing
- [x] Persistent database with deduplication
- [x] Renewal date tracking and 30-day alerts
- [x] Explainability module (risk factors + thresholds)
- [x] RAG integration for company policy documents
- [x] Dashboard with visual analytics
- [x] Privacy-by-design (session-only bulk data)
- [x] Deployed to Streamlit Cloud (public URL)
- [ ] User authentication
- [ ] Outcome tracking

---

*Built by Nero Han — USC Marshall MBA 2027 | 7 years insurance industry experience*  
*Live demo: https://ai-project-ru7tgaiumdr9qnf2pysyfz.streamlit.app*  
*GitHub: https://github.com/nerohan96-source/ai-project*
