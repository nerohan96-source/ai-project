import streamlit as st
import anthropic
import os
import pandas as pd
import io
import sqlite3
from datetime import datetime, date, timedelta
import plotly.express as px

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── DATABASE ──
def init_db():
    conn = sqlite3.connect("churnshield.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analyzed_at TEXT,
            customer_name TEXT,
            policy_number TEXT,
            carrier TEXT,
            policy_type TEXT,
            policy_duration REAL,
            renewal_date TEXT,
            premium_change TEXT,
            premium_reason TEXT,
            at_fault_claims INTEGER,
            bundle_status TEXT,
            payment_record TEXT,
            last_contact TEXT,
            notes TEXT,
            risk_level TEXT,
            full_analysis TEXT
        )
    """)
    # Add renewal_date column if it doesn't exist (for existing DBs)
    try:
        conn.execute("ALTER TABLE customers ADD COLUMN renewal_date TEXT")
        conn.commit()
    except Exception:
        pass
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect("churnshield.db")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    policy_num = data["policy_number"]

    # If policy number exists, update instead of insert
    if policy_num and policy_num != "N/A":
        existing = conn.execute(
            "SELECT id FROM customers WHERE policy_number = ?", (policy_num,)
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE customers SET
                    analyzed_at=?, customer_name=?, carrier=?, policy_type=?,
                    policy_duration=?, renewal_date=?, premium_change=?, premium_reason=?,
                    at_fault_claims=?, bundle_status=?, payment_record=?, last_contact=?,
                    notes=?, risk_level=?, full_analysis=?
                WHERE policy_number=?
            """, (
                now, data["customer_name"], data["carrier"], data["policy_type"],
                data["policy_duration"], data.get("renewal_date", ""),
                data["premium_change"], data["premium_reason"], data["at_fault_claims"],
                data["bundle_status"], data["payment_record"], data["last_contact"],
                data["notes"], data["risk_level"], data["full_analysis"], policy_num
            ))
            conn.commit()
            conn.close()
            return "updated"

    conn.execute("""
        INSERT INTO customers (
            analyzed_at, customer_name, policy_number, carrier, policy_type,
            policy_duration, renewal_date, premium_change, premium_reason, at_fault_claims,
            bundle_status, payment_record, last_contact, notes, risk_level, full_analysis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now, data["customer_name"], policy_num, data["carrier"],
        data["policy_type"], data["policy_duration"], data.get("renewal_date", ""),
        data["premium_change"], data["premium_reason"], data["at_fault_claims"],
        data["bundle_status"], data["payment_record"], data["last_contact"],
        data["notes"], data["risk_level"], data["full_analysis"]
    ))
    conn.commit()
    conn.close()
    return "inserted"

def load_all():
    conn = sqlite3.connect("churnshield.db")
    df = pd.read_sql("SELECT * FROM customers ORDER BY analyzed_at DESC", conn)
    conn.close()
    return df

def delete_record(record_id):
    conn = sqlite3.connect("churnshield.db")
    conn.execute("DELETE FROM customers WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

init_db()

st.set_page_config(
    page_title="ChurnShield · Insurance Risk AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1100px; }
    .risk-high {
        background: #fee2e2; border: 1px solid #ef4444;
        color: #b91c1c !important; padding: 6px 16px; border-radius: 20px;
        font-weight: 700; font-size: 0.9rem; display: inline-block;
    }
    .risk-medium {
        background: #fef3c7; border: 1px solid #f59e0b;
        color: #92400e !important; padding: 6px 16px; border-radius: 20px;
        font-weight: 700; font-size: 0.9rem; display: inline-block;
    }
    .risk-low {
        background: #dcfce7; border: 1px solid #22c55e;
        color: #166534 !important; padding: 6px 16px; border-radius: 20px;
        font-weight: 700; font-size: 0.9rem; display: inline-block;
    }
    .urgent-card {
        background: #fff1f2; border: 2px solid #ef4444;
        border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
    }
    .result-box {
        background: #f0f6ff; border: 1px solid #bfdbfe;
        border-radius: 12px; padding: 24px; margin-top: 16px;
        white-space: pre-wrap; font-size: 0.95rem; line-height: 1.8;
        color: #0f172a !important;
    }
    .stFormSubmitButton button {
        background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        font-size: 1rem !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
        color: white !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🛡️ ChurnShield")
    st.caption("Insurance Risk Intelligence")
    st.markdown("*Built for insurance agents to identify at-risk customers before renewal*")
    st.divider()
    st.markdown("**Risk Levels**")
    st.markdown('<span class="risk-high">HIGH</span> Act within 3 days', unsafe_allow_html=True)
    st.markdown('<span class="risk-medium">MEDIUM</span> Follow up this week', unsafe_allow_html=True)
    st.markdown('<span class="risk-low">LOW</span> Routine check', unsafe_allow_html=True)
    st.divider()

    all_df = load_all()
    total = len(all_df)
    if total > 0:
        st.markdown(f"**Total Customers: {total}**")
        st.markdown(f"🔴 High Risk: {len(all_df[all_df['risk_level'] == 'HIGH'])}")
        st.markdown(f"🟡 Medium Risk: {len(all_df[all_df['risk_level'] == 'MEDIUM'])}")
        st.markdown(f"🟢 Low Risk: {len(all_df[all_df['risk_level'] == 'LOW'])}")

        # Urgent renewals in sidebar
        today = date.today()
        next_30 = today + timedelta(days=30)
        if "renewal_date" in all_df.columns:
            renew_df = all_df[all_df["renewal_date"].notna() & (all_df["renewal_date"] != "")]
            if not renew_df.empty:
                renew_df = renew_df.copy()
                renew_df["renewal_date_parsed"] = pd.to_datetime(renew_df["renewal_date"], errors="coerce").dt.date
                urgent = renew_df[
                    (renew_df["renewal_date_parsed"] >= today) &
                    (renew_df["renewal_date_parsed"] <= next_30) &
                    (renew_df["risk_level"] == "HIGH")
                ]
                if not urgent.empty:
                    st.divider()
                    st.markdown(f"🚨 **{len(urgent)} HIGH risk renewing in 30 days**")
                    for _, r in urgent.iterrows():
                        st.markdown(f"• {r['customer_name']} — {r['renewal_date_parsed']}")

    st.divider()
    st.caption("Built by Nero Han · Claude AI")

# ── HEADER ──
st.markdown("# 🛡️ ChurnShield")
st.markdown("**AI-powered customer retention intelligence for insurance agents**")
st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Single Analysis", "Bulk Upload (Excel)", "History & Records", "Dashboard"])

def analyze_customer(customer_info):
    prompt = f"""You are an insurance industry expert with 7+ years of experience analyzing customer churn risk.

Based on the following customer profile, provide:
1. RISK LEVEL: HIGH / MEDIUM / LOW
2. RISK FACTORS: 2-3 bullet points
3. FOLLOW-UP ACTION: Specific action and talking points
4. AUTO-REMINDER: Yes/No + timing
5. BUNDLE OPPORTUNITY: Yes/No + products + estimated savings %

Customer Profile:
{customer_info}

Be direct, specific, and actionable.
"""
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def get_risk_level(result):
    for level in ["HIGH", "MEDIUM", "LOW"]:
        if level in result:
            return level
    return "MEDIUM"

# ── TAB 1: SINGLE ──
with tab1:
    with st.form("customer_form"):
        st.markdown("### Customer Profile")

        col0a, col0b, col0c = st.columns(3)
        with col0a:
            customer_name = st.text_input("Customer Name", placeholder="e.g. John Smith")
        with col0b:
            policy_number = st.text_input("Policy Number", placeholder="e.g. POL-123456")
        with col0c:
            carrier = st.selectbox("Carrier", [
                "State Farm", "Allstate", "Progressive", "GEICO",
                "Farmers", "Nationwide", "Liberty Mutual", "Travelers",
                "USAA", "AAA", "Mercury", "Other"
            ])

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            policy_type = st.selectbox("Policy Type", ["Auto", "Home", "Life", "Renters", "Auto + Home", "Other"])
            years = st.number_input("Policy Duration (yrs)", min_value=0.0, max_value=50.0, step=0.5)
            claims = st.number_input("At-Fault Claims (3yr)", min_value=0, max_value=10, step=1)
        with col2:
            premium_change = st.selectbox("Premium Change", ["Increased 0-10%", "Increased 10-25%", "Increased 25-50%", "Increased 50%+", "Flat", "Decreased"])
            bundle = st.selectbox("Bundle Status", ["Auto Only", "Home Only", "Auto + Home", "Auto + Life", "Other Bundle"])
            payment = st.selectbox("Payment Record", ["Always On Time", "Occasionally Late", "Frequently Late"])
        with col3:
            last_contact = st.selectbox("Last Contact", ["Within 1 month", "1-3 months ago", "3-6 months ago", "6+ months ago"])
            renewal_date = st.date_input("Renewal Date", value=None, min_value=date.today())
            premium_reason = st.text_input("Premium Change Reason", placeholder="e.g. at-fault claim")

        notes = st.text_area("Notes", placeholder="Additional context...", height=80)
        submitted = st.form_submit_button("Analyze Churn Risk →", use_container_width=True)

    if submitted:
        renewal_str = renewal_date.strftime("%Y-%m-%d") if renewal_date else ""
        days_to_renewal = (renewal_date - date.today()).days if renewal_date else None

        customer_info = f"""
- Customer Name: {customer_name or "N/A"}
- Policy Number: {policy_number or "N/A"}
- Carrier: {carrier}
- Policy Type: {policy_type}
- Policy Duration: {years} years
- Renewal Date: {renewal_str or "N/A"}{f" ({days_to_renewal} days away)" if days_to_renewal else ""}
- Premium Change: {premium_change}
- Reason: {premium_reason or "N/A"}
- At-Fault Claims (3yr): {claims}
- Bundle Status: {bundle}
- Payment Record: {payment}
- Last Contact: {last_contact}
- Notes: {notes or "N/A"}
"""
        with st.spinner("Running AI analysis..."):
            result = analyze_customer(customer_info)

        risk_level = get_risk_level(result)
        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

        st.divider()

        # Urgent renewal warning
        if renewal_date and days_to_renewal is not None and days_to_renewal <= 30 and risk_level == "HIGH":
            st.error(f"🚨 **URGENT**: This HIGH risk customer renews in **{days_to_renewal} days** — contact immediately.")

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Risk Level", risk_emoji[risk_level] + " " + risk_level)
        with col_b:
            st.metric("Policy Type", policy_type)
        with col_c:
            st.metric("Premium Change", premium_change)
        with col_d:
            st.metric("Renewal", renewal_str if renewal_str else "N/A")

        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)

        action = save_to_db({
            "customer_name": customer_name or "Customer",
            "policy_number": policy_number or "N/A",
            "carrier": carrier,
            "policy_type": policy_type,
            "policy_duration": years,
            "renewal_date": renewal_str,
            "premium_change": premium_change,
            "premium_reason": premium_reason or "N/A",
            "at_fault_claims": claims,
            "bundle_status": bundle,
            "payment_record": payment,
            "last_contact": last_contact,
            "notes": notes or "N/A",
            "risk_level": risk_level,
            "full_analysis": result
        })
        if action == "updated":
            st.info("Record updated (existing policy number found).")
        else:
            st.success("New customer saved to database.")
        st.caption("Analysis powered by Claude AI · ChurnShield by Nero Han")

# ── TAB 2: BULK UPLOAD ──
with tab2:
    st.markdown("### Bulk Customer Analysis")
    st.info("🔒 **Privacy notice:** Bulk upload results are session-only and never saved to the database. Data clears when you close the browser. For persistent records, use Single Analysis.")

    template_data = {
        "Customer Name": ["John Smith", "Jane Doe"],
        "Policy Number": ["POL-001234", "POL-005678"],
        "Carrier": ["State Farm", "Allstate"],
        "Policy Type": ["Auto", "Home"],
        "Policy Duration (yrs)": [2.5, 5.0],
        "Renewal Date": ["2025-08-15", "2025-09-01"],
        "Premium Change": ["Increased 25-50%", "Flat"],
        "Premium Change Reason": ["at-fault claim", "N/A"],
        "At-Fault Claims (3yr)": [1, 0],
        "Bundle Status": ["Auto Only", "Auto + Home"],
        "Payment Record": ["Always On Time", "Occasionally Late"],
        "Last Contact": ["3-6 months ago", "1-3 months ago"],
        "Notes": ["Considering switching", ""]
    }
    template_df = pd.DataFrame(template_data)
    buffer = io.BytesIO()
    template_df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("⬇️ Download Template", data=buffer, file_name="churnshield_template.xlsx", mime="application/vnd.ms-excel")

    st.divider()
    uploaded_file = st.file_uploader("Upload Customer Excel File", type=["xlsx", "xls"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.markdown(f"**{len(df)} customers loaded**")
        st.dataframe(df, use_container_width=True)

        if st.button("🔍 Analyze All Customers", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, row in df.iterrows():
                name = row.get("Customer Name", f"Customer {i+1}")
                status.markdown(f"Analyzing {i+1}/{len(df)}: **{name}**")

                renewal_val = row.get("Renewal Date", "")
                if pd.notna(renewal_val) and renewal_val != "":
                    try:
                        renewal_str = pd.to_datetime(renewal_val).strftime("%Y-%m-%d")
                    except Exception:
                        renewal_str = str(renewal_val)
                else:
                    renewal_str = ""

                customer_info = f"""
- Policy Type: {row.get('Policy Type', 'N/A')}
- Policy Duration: {row.get('Policy Duration (yrs)', 'N/A')} years
- Renewal Date: {renewal_str or 'N/A'}
- Premium Change: {row.get('Premium Change', 'N/A')}
- Reason: {row.get('Premium Change Reason', 'N/A')}
- At-Fault Claims (3yr): {row.get('At-Fault Claims (3yr)', 'N/A')}
- Bundle Status: {row.get('Bundle Status', 'N/A')}
- Payment Record: {row.get('Payment Record', 'N/A')}
- Last Contact: {row.get('Last Contact', 'N/A')}
- Notes: {row.get('Notes', 'N/A')}
"""
                result = analyze_customer(customer_info)
                risk = get_risk_level(result)
                results.append({
                    "Customer Name": name,
                    "Renewal Date": renewal_str,
                    "Risk Level": risk,
                    "Full Analysis": result
                })

                progress.progress((i + 1) / len(df))

            status.empty()
            progress.empty()

            result_df = pd.DataFrame(results)
            st.divider()
            st.markdown("### Results")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔴 High Risk", len(result_df[result_df["Risk Level"] == "HIGH"]))
            with col2:
                st.metric("🟡 Medium Risk", len(result_df[result_df["Risk Level"] == "MEDIUM"]))
            with col3:
                st.metric("🟢 Low Risk", len(result_df[result_df["Risk Level"] == "LOW"]))

            # Urgent renewals alert
            today = date.today()
            next_30 = today + timedelta(days=30)
            urgent_bulk = []
            for _, r in result_df.iterrows():
                if r["Renewal Date"] and r["Risk Level"] == "HIGH":
                    try:
                        rd = datetime.strptime(r["Renewal Date"], "%Y-%m-%d").date()
                        if today <= rd <= next_30:
                            urgent_bulk.append((r["Customer Name"], rd))
                    except Exception:
                        pass
            if urgent_bulk:
                st.warning(f"🚨 **{len(urgent_bulk)} HIGH risk customer(s) renewing within 30 days:** " +
                           ", ".join([f"{n} ({d})" for n, d in urgent_bulk]))

            for _, row in result_df.iterrows():
                risk = row["Risk Level"]
                emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[risk]
                renewal_label = f" | Renewal: {row['Renewal Date']}" if row.get("Renewal Date") else ""
                with st.expander(f"{emoji} {row['Customer Name']} — {risk}{renewal_label}"):
                    st.markdown(f'<div class="result-box">{row["Full Analysis"]}</div>', unsafe_allow_html=True)

            out_buffer = io.BytesIO()
            result_df.to_excel(out_buffer, index=False)
            out_buffer.seek(0)
            st.download_button("⬇️ Export Results to Excel", data=out_buffer, file_name="churnshield_results.xlsx", mime="application/vnd.ms-excel", use_container_width=True)

# ── TAB 3: HISTORY ──
with tab3:
    st.markdown("### Customer History & Records")
    hist_df = load_all()

    if hist_df.empty:
        st.info("No records yet. Analyze some customers first.")
    else:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            risk_filter = st.selectbox("Filter by Risk", ["All", "HIGH", "MEDIUM", "LOW"])
        with col_f2:
            carrier_options = ["All"] + sorted(hist_df["carrier"].dropna().unique().tolist())
            carrier_filter = st.selectbox("Filter by Carrier", carrier_options)
        with col_f3:
            search = st.text_input("Search by Name", placeholder="e.g. John")

        filtered = hist_df.copy()
        if risk_filter != "All":
            filtered = filtered[filtered["risk_level"] == risk_filter]
        if carrier_filter != "All":
            filtered = filtered[filtered["carrier"] == carrier_filter]
        if search:
            filtered = filtered[filtered["customer_name"].str.contains(search, case=False, na=False)]

        st.markdown(f"**{len(filtered)} records found**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(filtered))
        with col2:
            st.metric("🔴 High", len(filtered[filtered["risk_level"] == "HIGH"]))
        with col3:
            st.metric("🟡 Medium", len(filtered[filtered["risk_level"] == "MEDIUM"]))
        with col4:
            st.metric("🟢 Low", len(filtered[filtered["risk_level"] == "LOW"]))

        st.divider()

        display_cols = ["analyzed_at", "customer_name", "policy_number", "carrier", "policy_type", "renewal_date", "premium_change", "risk_level"]
        available_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[available_cols].rename(columns={
                "analyzed_at": "Date", "customer_name": "Name", "policy_number": "Policy #",
                "carrier": "Carrier", "policy_type": "Type", "renewal_date": "Renewal",
                "premium_change": "Premium Change", "risk_level": "Risk"
            }),
            use_container_width=True, hide_index=True
        )

        st.divider()
        st.markdown("#### Full Analysis Details")
        for _, row in filtered.iterrows():
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(row["risk_level"], "⚪")
            renewal_label = f" | Renewal: {row.get('renewal_date', '')}" if row.get("renewal_date") else ""
            with st.expander(f"{emoji} {row['customer_name']} — {row['analyzed_at']} — {row['risk_level']}{renewal_label}"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown(f"**Policy:** {row['policy_type']} | **Carrier:** {row['carrier']}")
                    st.markdown(f"**Premium Change:** {row['premium_change']}")
                    st.markdown(f"**At-Fault Claims:** {row['at_fault_claims']}")
                with col_d2:
                    st.markdown(f"**Bundle:** {row['bundle_status']}")
                    st.markdown(f"**Payment:** {row['payment_record']}")
                    st.markdown(f"**Renewal Date:** {row.get('renewal_date', 'N/A')}")
                st.markdown(f'<div class="result-box">{row["full_analysis"]}</div>', unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    delete_record(row["id"])
                    st.rerun()

        st.divider()
        buf = io.BytesIO()
        filtered.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ Export All to Excel", data=buf, file_name="churnshield_history.xlsx", mime="application/vnd.ms-excel")

# ── TAB 4: DASHBOARD ──
with tab4:
    st.markdown("### Dashboard")
    dash_df = load_all()

    if dash_df.empty:
        st.info("No data yet. Analyze some customers to see the dashboard.")
    else:
        today = date.today()
        next_30 = today + timedelta(days=30)

        # Urgent renewals section
        if "renewal_date" in dash_df.columns:
            renew_df = dash_df[dash_df["renewal_date"].notna() & (dash_df["renewal_date"] != "")].copy()
            if not renew_df.empty:
                renew_df["renewal_date_parsed"] = pd.to_datetime(renew_df["renewal_date"], errors="coerce").dt.date
                urgent = renew_df[
                    (renew_df["renewal_date_parsed"] >= today) &
                    (renew_df["renewal_date_parsed"] <= next_30) &
                    (renew_df["risk_level"] == "HIGH")
                ].sort_values("renewal_date_parsed")

                if not urgent.empty:
                    st.markdown("#### 🚨 High Risk Customers Renewing in 30 Days")
                    for _, r in urgent.iterrows():
                        days_left = (r["renewal_date_parsed"] - today).days
                        st.markdown(
                            f'<div class="urgent-card">🔴 <b>{r["customer_name"]}</b> — '
                            f'Renewal: {r["renewal_date_parsed"]} (<b>{days_left} days</b>) — '
                            f'{r["policy_type"]} | {r["carrier"]}</div>',
                            unsafe_allow_html=True
                        )
                    st.divider()

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Analyzed", len(dash_df))
        with col2:
            high_pct = round(len(dash_df[dash_df["risk_level"] == "HIGH"]) / len(dash_df) * 100)
            st.metric("High Risk %", f"{high_pct}%")
        with col3:
            bundle_only = dash_df[dash_df["bundle_status"].isin(["Auto Only", "Home Only"])]
            st.metric("No Bundle", len(bundle_only))
        with col4:
            late = dash_df[dash_df["payment_record"] != "Always On Time"]
            st.metric("Late Payments", len(late))

        st.divider()

        col_l, col_r = st.columns(2)
        color_map = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}

        with col_l:
            st.markdown("#### Risk Level Distribution")
            risk_counts = dash_df["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            fig_pie = px.pie(risk_counts, names="Risk Level", values="Count",
                             color="Risk Level", color_discrete_map=color_map, hole=0.4)
            fig_pie.update_layout(margin=dict(t=20, b=20), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_r:
            st.markdown("#### Risk by Policy Type")
            policy_risk = dash_df.groupby(["policy_type", "risk_level"]).size().reset_index(name="count")
            fig_bar = px.bar(policy_risk, x="policy_type", y="count", color="risk_level",
                             color_discrete_map=color_map, barmode="stack",
                             labels={"policy_type": "Policy Type", "count": "Customers", "risk_level": "Risk"})
            fig_bar.update_layout(margin=dict(t=20, b=20), height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

        col_l2, col_r2 = st.columns(2)

        with col_l2:
            st.markdown("#### Premium Change vs Risk")
            prem_risk = dash_df.groupby(["premium_change", "risk_level"]).size().reset_index(name="count")
            fig_prem = px.bar(prem_risk, x="premium_change", y="count", color="risk_level",
                              color_discrete_map=color_map, barmode="group",
                              labels={"premium_change": "Premium Change", "count": "Customers", "risk_level": "Risk"})
            fig_prem.update_layout(margin=dict(t=20, b=20), height=300, xaxis_tickangle=-30)
            st.plotly_chart(fig_prem, use_container_width=True)

        with col_r2:
            st.markdown("#### Customers by Carrier")
            carrier_counts = dash_df["carrier"].value_counts().reset_index()
            carrier_counts.columns = ["Carrier", "Count"]
            fig_carrier = px.bar(carrier_counts, x="Count", y="Carrier", orientation="h",
                                 color="Count", color_continuous_scale="Blues")
            fig_carrier.update_layout(margin=dict(t=20, b=20), height=300, showlegend=False)
            st.plotly_chart(fig_carrier, use_container_width=True)

        # Renewal timeline
        if "renewal_date" in dash_df.columns:
            renew_timeline = dash_df[dash_df["renewal_date"].notna() & (dash_df["renewal_date"] != "")].copy()
            if not renew_timeline.empty:
                st.markdown("#### Upcoming Renewals by Risk")
                renew_timeline["renewal_month"] = pd.to_datetime(renew_timeline["renewal_date"], errors="coerce").dt.to_period("M").astype(str)
                renew_timeline = renew_timeline[renew_timeline["renewal_month"].notna()]
                renew_grouped = renew_timeline.groupby(["renewal_month", "risk_level"]).size().reset_index(name="count")
                fig_renew = px.bar(renew_grouped, x="renewal_month", y="count", color="risk_level",
                                   color_discrete_map=color_map, barmode="stack",
                                   labels={"renewal_month": "Month", "count": "Renewals", "risk_level": "Risk"})
                fig_renew.update_layout(margin=dict(t=20, b=20), height=280)
                st.plotly_chart(fig_renew, use_container_width=True)

st.divider()
st.caption("ChurnShield · Built by Nero Han · Powered by Claude AI · github.com/nerohan96-source/ai-project")
