import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Novintix Result Evaluator", layout="wide")

# ---------------------------------------------------------
# CUSTOM CSS WITH YOUR COLOR COMBINATION (033e59 & f4a303)
# ---------------------------------------------------------
st.markdown("""
<style>

html, body {
    background: linear-gradient(to bottom right, #f8fafc, #e2e8f0);
    font-size: 20px !important;
}

.big-title {
    font-size: 46px;
    font-weight: 900;
    color: #033e59;
    text-align: center;
    margin-bottom: -5px;
}

.sub-title {
    font-size: 22px;
    font-weight: 600;
    color: #f4a303;
    text-align: center;
    margin-bottom: 30px;
}

.section-header {
    font-size: 34px;
    font-weight: 800;
    color: #033e59;
    margin-bottom: 18px;
}

.dataframe th {
    background-color: #f4a303 !important;
    color: white !important;
    font-size: 18px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BUCKET PROCESSING WITH QUESTION RANGES
# ---------------------------------------------------------
def compute_buckets(df):

    def sum_range(row, start, end):
        return sum(row.get(f"Q{i}", 0) for i in range(start, end + 1))

    df["Aptitude (20) [Q1–Q20]"] = df.apply(lambda r: sum_range(r, 1, 20), axis=1)
    df["AI/ML/DS (30) [Q21–Q40 + Q61–Q70]"] = df.apply(lambda r: sum_range(r, 21, 40) + sum_range(r, 61, 70), axis=1)
    df["FSD/DB (30) [Q41–Q60 + Q71–Q80]"] = df.apply(lambda r: sum_range(r, 41, 60) + sum_range(r, 71, 80), axis=1)
    df["DevOps/Testing (20) [Q81–Q100]"] = df.apply(lambda r: sum_range(r, 81, 100), axis=1)

    df["Overall (100)"] = (
        df["Aptitude (20) [Q1–Q20]"] +
        df["AI/ML/DS (30) [Q21–Q40 + Q61–Q70]"] +
        df["FSD/DB (30) [Q41–Q60 + Q71–Q80]"] +
        df["DevOps/Testing (20) [Q81–Q100]"]
    )

    return df

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("<div class='big-title'>Novintix</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Digital – Result Evaluator</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if not uploaded_file:
    st.stop()

df_raw = pd.read_excel(uploaded_file)

if "Student name" not in df_raw.columns or "Email" not in df_raw.columns:
    st.error("❌ Excel must contain 'Student name' and 'Email'")
    st.stop()

df = compute_buckets(df_raw)
st.success("✅ File uploaded & processed successfully!")

# ---------------------------------------------------------
# CATEGORY + TOP FILTERS
# ---------------------------------------------------------
sections = [
    "Overall (100)",
    "Aptitude (20) [Q1–Q20]",
    "AI/ML/DS (30) [Q21–Q40 + Q61–Q70]",
    "FSD/DB (30) [Q41–Q60 + Q71–Q80]",
    "DevOps/Testing (20) [Q81–Q100]"
]

with st.container():
    col_left, col_right = st.columns([3, 1])

    with col_left:
        selected_section = st.selectbox("Choose Category", sections)

    with col_right:
        top_options = [5, 10, 20, 30, 40, 50, len(df)]
        top_choice = st.selectbox("Show Top:", top_options)

# ---------------------------------------------------------
# FILTER DATA
# ---------------------------------------------------------
df_sorted = df.sort_values(by=selected_section, ascending=False).head(top_choice)
df_sorted_reset = df_sorted.reset_index(drop=True)
df_sorted_reset.index += 1

# ---------------------------------------------------------
# VISUALS
# ---------------------------------------------------------
vis_left, vis_right = st.columns(2)

# Bar Chart
with vis_left:
    st.markdown("<div class='section-header'>Performance Chart</div>", unsafe_allow_html=True)

    fig1 = px.bar(
        df_sorted_reset,
        x="Student name",
        y=selected_section,
        text=selected_section,
        color=selected_section,
        color_continuous_scale=[[0, "#033e59"], [1, "#f4a303"]],
    )
    fig1.update_layout(xaxis_tickangle=-45, height=450, font=dict(size=18))
    st.plotly_chart(fig1, use_container_width=True)

# Pie Chart
with vis_right:
    st.markdown("<div class='section-header'>Score Contribution</div>", unsafe_allow_html=True)

    fig2 = px.pie(
        df_sorted_reset,
        names="Student name",
        values=selected_section,
        color_discrete_sequence=px.colors.sequential.Oranges,
    )
    fig2.update_traces(textinfo="percent+label")
    fig2.update_layout(height=450, font=dict(size=18))
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# TABLE
# ---------------------------------------------------------
st.markdown("<div class='section-header'>Top Students</div>", unsafe_allow_html=True)

st.dataframe(
    df_sorted_reset[["Student name", "Email", selected_section]],
    height=450,
    use_container_width=True
)

# ---------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------
csv = df_sorted_reset.to_csv(index=False)

st.download_button(
    "⬇ Download Results CSV",
    csv,
    "results.csv",
    mime="text/csv",
    use_container_width=True
)
