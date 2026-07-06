import streamlit as st
import anthropic
import os
import pandas as pd
import io
import sqlite3
from datetime import datetime

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
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect("churnshield.db")
    conn.execute("""
        INSERT INTO customers (
            analyzed_at, customer_name, policy_number, carrier, policy_type,
            policy_duration, premium_change, premium_reason, at_fault_claims,
            bundle_status, payment_record, last_contact, notes, risk_level, full_analysis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        data["customer_name"], data["policy_number"], data["carrier"],
        data["policy_type"], data["policy_duration"], data["premium_change"],
        data["premium_reason"], data["at_fault_claims"], data["bundle_status"],
        data["payment_record"], data["last_contact"], data["notes"],
        data["risk_level"], data["full_analysis"]
    ))
    conn.commit()
    conn.close()

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
    st.divider()
    st.markdown("**Risk Levels**")
    st.markdown('<span class="risk-high">HIGH</span> Act within 3 days', unsafe_allow_html=True)
    st.markdown('<span class="risk-medium">MEDIUM</span> Follow up this week', unsafe_allow_html=True)
    st.markdown('<span class="risk-low">LOW</span> Routine check', unsafe_allow_html=True)
    st.divider()

    # DB stats
    all_df = load_all()
    total = len(all_df)
    if total > 0:
        st.markdown(f"**Total Customers Analyzed: {total}**")
        high_count = len(all_df[all_df["risk_level"] == "HIGH"])
        st.markdown(f"🔴 High Risk: {high_count}")
        st.markdown(f"🟡 Medium Risk: {len(all_df[all_df['risk_level'] == 'MEDIUM'])}")
        st.markdown(f"🟢 Low Risk: {len(all_df[all_df['risk_level'] == 'LOW'])}")

    st.divider()
    st.caption("Built by Nero Han · Claude AI")

# ── HEADER ──
st.markdown("# 🛡️ ChurnShield")
st.markdown("**AI-powered customer retention intelligence for insurance agents**")
st.divider()

# ── TABS ──
tab1, tab2, tab3 = st.tabs(["Single Analysis", "Bulk Upload (Excel)", "History & Records"])

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
            premium_reason = st.text_input("Premium Change Reason", placeholder="e.g. at-fault claim")
            notes = st.text_area("Notes", placeholder="Additional context...", height=100)

        submitted = st.form_submit_button("Analyze Churn Risk →", use_container_width=True)

    if submitted:
        customer_info = f"""
- Customer Name: {customer_name or "N/A"}
- Policy Number: {policy_number or "N/A"}
- Carrier: {carrier}
- Policy Type: {policy_type}
- Policy Duration: {years} years
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
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            st.metric("Risk Level", risk_emoji[risk_level] + " " + risk_level)
        with col_b:
            st.metric("Policy Type", policy_type)
        with col_c:
            st.metric("Premium Change", premium_change)

        st.markdown(f'<div class="result-box">{result}</div>', unsafe_allow_html=True)

        save_to_db({
            "customer_name": customer_name or f"Customer",
            "policy_number": policy_number or "N/A",
            "carrier": carrier,
            "policy_type": policy_type,
            "policy_duration": years,
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

        st.success("Saved to database.")
        st.divider()
        st.caption("Analysis powered by Claude AI · ChurnShield by Nero Han")

# ── TAB 2: BULK UPLOAD ──
with tab2:
    st.markdown("### Bulk Customer Analysis")

    template_data = {
        "Customer Name": ["John Smith", "Jane Doe"],
        "Policy Type": ["Auto", "Home"],
        "Policy Duration (yrs)": [2.5, 5.0],
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
                status.markdown(f"Analyzing {i+1}/{len(df)}: **{row.get('Customer Name', f'Customer {i+1}')}**")
                customer_info = f"""
- Policy Type: {row.get('Policy Type', 'N/A')}
- Policy Duration: {row.get('Policy Duration (yrs)', 'N/A')} years
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
                    "Customer Name": row.get("Customer Name", f"Customer {i+1}"),
                    "Risk Level": risk,
                    "Full Analysis": result
                })

                save_to_db({
                    "customer_name": row.get("Customer Name", f"Customer {i+1}"),
                    "policy_number": "N/A",
                    "carrier": "N/A",
                    "policy_type": row.get("Policy Type", "N/A"),
                    "policy_duration": row.get("Policy Duration (yrs)", 0),
                    "premium_change": row.get("Premium Change", "N/A"),
                    "premium_reason": row.get("Premium Change Reason", "N/A"),
                    "at_fault_claims": row.get("At-Fault Claims (3yr)", 0),
                    "bundle_status": row.get("Bundle Status", "N/A"),
                    "payment_record": row.get("Payment Record", "N/A"),
                    "last_contact": row.get("Last Contact", "N/A"),
                    "notes": row.get("Notes", "N/A"),
                    "risk_level": risk,
                    "full_analysis": result
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

            for _, row in result_df.iterrows():
                risk = row["Risk Level"]
                emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[risk]
                with st.expander(f"{emoji} {row['Customer Name']} — {risk} RISK"):
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
        # Filters
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

        # Summary metrics
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

        # Records table
        display_cols = ["analyzed_at", "customer_name", "policy_number", "carrier", "policy_type", "premium_change", "risk_level"]
        st.dataframe(
            filtered[display_cols].rename(columns={
                "analyzed_at": "Date", "customer_name": "Name", "policy_number": "Policy #",
                "carrier": "Carrier", "policy_type": "Type", "premium_change": "Premium Change", "risk_level": "Risk"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # Expandable detail view
        st.markdown("#### Full Analysis Details")
        for _, row in filtered.iterrows():
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(row["risk_level"], "⚪")
            with st.expander(f"{emoji} {row['customer_name']} — {row['analyzed_at']} — {row['risk_level']}"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown(f"**Policy:** {row['policy_type']} | **Carrier:** {row['carrier']}")
                    st.markdown(f"**Premium Change:** {row['premium_change']}")
                    st.markdown(f"**At-Fault Claims:** {row['at_fault_claims']}")
                with col_d2:
                    st.markdown(f"**Bundle:** {row['bundle_status']}")
                    st.markdown(f"**Payment:** {row['payment_record']}")
                    st.markdown(f"**Last Contact:** {row['last_contact']}")
                st.markdown(f'<div class="result-box">{row["full_analysis"]}</div>', unsafe_allow_html=True)
                if st.button(f"🗑️ Delete", key=f"del_{row['id']}"):
                    delete_record(row["id"])
                    st.rerun()

        st.divider()

        # Export all
        buf = io.BytesIO()
        filtered.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button("⬇️ Export All to Excel", data=buf, file_name="churnshield_history.xlsx", mime="application/vnd.ms-excel")

st.divider()
st.caption("ChurnShield · Built by Nero Han · Powered by Claude AI · github.com/nerohan96-source/ai-project")
