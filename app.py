import streamlit as st
import anthropic
import os
import pandas as pd
import io

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# 保存历史记录
if "history" not in st.session_state:
    st.session_state.history = []

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
    st.markdown("**How it works**")
    st.markdown("1. Single: Fill in customer profile\n2. Bulk: Upload Excel file\n3. Get AI risk assessment\n4. Export results")
    st.divider()
    st.markdown("**Risk Levels**")
    st.markdown('<span class="risk-high">HIGH</span>', unsafe_allow_html=True)
    st.markdown("Act within 3 days")
    st.markdown('<span class="risk-medium">MEDIUM</span>', unsafe_allow_html=True)
    st.markdown("Follow up this week")
    st.markdown('<span class="risk-low">LOW</span>', unsafe_allow_html=True)
    st.markdown("Schedule routine check")
    st.divider()

    # 历史记录
    if st.session_state.history:
        st.markdown(f"**Session History ({len(st.session_state.history)})**")
        for i, h in enumerate(st.session_state.history):
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(h["Risk Level"], "⚪")
            st.markdown(f"{emoji} {h['Customer Name']}")

        st.divider()

        # 导出按钮
        hist_df = pd.DataFrame(st.session_state.history)
        buf = io.BytesIO()
        hist_df.to_excel(buf, index=False)
        buf.seek(0)
        st.download_button(
            "⬇️ Export All to Excel",
            data=buf,
            file_name="churnshield_session.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    st.divider()
    st.caption("Built by Nero Han · Claude AI")

# ── HEADER ──
st.markdown("# ChurnShield")
st.markdown("**AI-powered customer retention intelligence for insurance agents**")
st.divider()

# ── TABS ──
tab1, tab2 = st.tabs(["Single Analysis", "Bulk Upload (Excel)"])

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

        # 基本信息行
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

        # 保存到历史记录
        st.session_state.history.append({
            "Customer Name": customer_name or f"Customer {len(st.session_state.history)+1}",
            "Policy Number": policy_number or "N/A",
            "Carrier": carrier,
            "Policy Type": policy_type,
            "Premium Change": premium_change,
            "At-Fault Claims": claims,
            "Bundle Status": bundle,
            "Risk Level": risk_level,
            "Full Analysis": result
        })

        st.divider()
        st.caption("Analysis powered by Claude AI · ChurnShield by Nero Han")

# ── TAB 2: BULK UPLOAD ──
with tab2:
    st.markdown("### Bulk Customer Analysis")
    st.markdown("Upload an Excel file with customer data. Download the template below to get started.")

    # Template download
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

    st.download_button(
        "⬇️ Download Template",
        data=buffer,
        file_name="churnshield_template.xlsx",
        mime="application/vnd.ms-excel"
    )

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
                status.markdown(f"Analyzing customer {i+1} of {len(df)}: **{row.get('Customer Name', f'Customer {i+1}')}**")

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
                progress.progress((i + 1) / len(df))

            status.empty()
            progress.empty()

            result_df = pd.DataFrame(results)

            st.divider()
            st.markdown("### Results")

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                high = len(result_df[result_df["Risk Level"] == "HIGH"])
                st.metric("🔴 High Risk", high)
            with col2:
                med = len(result_df[result_df["Risk Level"] == "MEDIUM"])
                st.metric("🟡 Medium Risk", med)
            with col3:
                low = len(result_df[result_df["Risk Level"] == "LOW"])
                st.metric("🟢 Low Risk", low)

            # Results table
            for _, row in result_df.iterrows():
                risk = row["Risk Level"]
                risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                with st.expander(f"{risk_emoji[risk]} {row['Customer Name']} — {risk} RISK"):
                    st.markdown(f'<div class="result-box">{row["Full Analysis"]}</div>', unsafe_allow_html=True)

            # Export
            out_buffer = io.BytesIO()
            result_df.to_excel(out_buffer, index=False)
            out_buffer.seek(0)
            st.download_button(
                "⬇️ Export Results to Excel",
                data=out_buffer,
                file_name="churnshield_results.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )

st.divider()
st.caption("ChurnShield · Built by Nero Han · Powered by Claude AI · github.com/nerohan96-source/ai-project")
