import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Novintix Result Evaluator", layout="wide")

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>

html, body {
    background: linear-gradient(to bottom right, #f8fafc, #e2e8f0);
    font-size: 18px !important;
}

.big-title {
    font-size: 40px;
    font-weight: 900;
    color: #033e59;
    text-align: center;
    margin-bottom: -5px;
}

.sub-title {
    font-size: 20px;
    font-weight: 600;
    color: #f4a303;
    text-align: center;
    margin-bottom: 25px;
}

.section-header {
    font-size: 26px;
    font-weight: 800;
    color: #033e59;
    margin-bottom: 14px;
}

.dataframe th {
    background-color: #f4a303 !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: 900 !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# SCORE COMPUTATION
# ---------------------------------------------------------
def compute_buckets(df: pd.DataFrame) -> pd.DataFrame:
    def sum_range(row, start, end):
        return sum(row.get(f"Q{i}", 0) for i in range(start, end + 1))

    df["Aptitude (20) [Q1–Q20]"] = df.apply(lambda r: sum_range(r, 1, 20), axis=1)
    df["AI/ML/DS (30) [Q21–Q40 + Q61–Q70]"] = df.apply(
        lambda r: sum_range(r, 21, 40) + sum_range(r, 61, 70), axis=1
    )
    df["FSD/DB (30) [Q41–Q60 + Q71–Q80]"] = df.apply(
        lambda r: sum_range(r, 41, 60) + sum_range(r, 71, 80), axis=1
    )
    df["DevOps/Testing (20) [Q81–Q100]"] = df.apply(
        lambda r: sum_range(r, 81, 100), axis=1
    )

    df["Overall (100)"] = (
        df["Aptitude (20) [Q1–Q20]"]
        + df["AI/ML/DS (30) [Q21–Q40 + Q61–Q70]"]
        + df["FSD/DB (30) [Q41–Q60 + Q71–Q80]"]
        + df["DevOps/Testing (20) [Q81–Q100]"]
    )
    return df


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown("<div class='big-title'>Novintix</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Digital – Result Evaluator</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# MULTI-FILE UPLOAD + MERGE
# ---------------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload multiple Result Files (same structure): (.xlsx, .xls, .xlsm, .csv, .tsv, .txt, .clsx)",
    type=["xlsx", "xls", "xlsm", "csv", "tsv", "txt", "clsx"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.stop()

merged_list = []

for uploaded_file in uploaded_files:
    ext = uploaded_file.name.split(".")[-1].lower()

    try:
        if ext in ["xlsx", "xls", "xlsm", "clsx"]:
            df_part = pd.read_excel(uploaded_file)
        elif ext in ["csv", "txt"]:
            df_part = pd.read_csv(uploaded_file)
        elif ext == "tsv":
            df_part = pd.read_csv(uploaded_file, sep="\t")
        else:
            st.error(f"❌ Unsupported file type: {uploaded_file.name}")
            st.stop()

        merged_list.append(df_part)

    except Exception as e:
        st.error(f"❌ Error reading file {uploaded_file.name}: {e}")
        st.stop()

# MERGE ALL UPLOADED FILES
df_raw = pd.concat(merged_list, ignore_index=True)

# VALIDATE REQUIRED COLUMNS
if "Student name" not in df_raw.columns or "Email" not in df_raw.columns:
    st.error("❌ All files must contain 'Student name' and 'Email' columns.")
    st.stop()

df = compute_buckets(df_raw)

st.success("✅ Files uploaded, merged & processed successfully!")


# ---------------------------------------------------------
# SECTION + TOP FILTERS
# ---------------------------------------------------------
sections = [
    "Overall (100)",
    "Aptitude (20) [Q1–Q20]",
    "AI/ML/DS (30) [Q21–Q40 + Q61–Q70]",
    "FSD/DB (30) [Q41–Q60 + Q71–Q80]",
    "DevOps/Testing (20) [Q81–Q100]",
]

col_left, col_right = st.columns([3, 1])

with col_left:
    selected_section = st.selectbox("Choose Category", sections)

with col_right:
    top_n = st.selectbox("Show Top:", [5, 10, 20, 30, 40, 50, len(df)])

df_sorted = df.sort_values(by=selected_section, ascending=False).head(top_n)
df_sorted = df_sorted.reset_index(drop=True)
df_sorted.index += 1  # rank index


# ---------------------------------------------------------
# RANK STATE
# ---------------------------------------------------------
if "rank_index" not in st.session_state:
    st.session_state.rank_index = 1

total_students = len(df_sorted)

st.session_state.rank_index = max(1, min(st.session_state.rank_index, total_students))
rank = st.session_state.rank_index

selected_student = df_sorted.iloc[rank - 1]


# ---------------------------------------------------------
# VISUALS (BAR LEFT, PIE RIGHT)
# ---------------------------------------------------------
vis_left, vis_right = st.columns(2)

# ---------- BAR CHART ----------
with vis_left:
    st.markdown("<div class='section-header'>Performance Chart</div>", unsafe_allow_html=True)

    fig1 = px.bar(
        df_sorted,
        x="Student name",
        y=selected_section,
        text=selected_section,
        color=selected_section,
        color_continuous_scale=[[0, "#033e59"], [1, "#f4a303"]],
    )
    fig1.update_layout(xaxis_tickangle=-45, height=430, font=dict(size=15))
    st.plotly_chart(fig1, use_container_width=True)

# ---------- PIE CHART ----------
with vis_right:
    st.markdown("<div class='section-header'>Bucket Contribution</div>", unsafe_allow_html=True)

    pie_data = pd.DataFrame(
        {
            "Bucket": [
                "Aptitude",
                "AI/ML/DS",
                "FSD/DB",
                "DevOps/Testing",
            ],
            "Score": [
                selected_student["Aptitude (20) [Q1–Q20]"],
                selected_student["AI/ML/DS (30) [Q21–Q40 + Q61–Q70]"],
                selected_student["FSD/DB (30) [Q41–Q60 + Q71–Q80]"],
                selected_student["DevOps/Testing (20) [Q81–Q100]"],
            ],
        }
    )

    fig2 = px.pie(
        pie_data,
        names="Bucket",
        values="Score",
        color_discrete_sequence=px.colors.sequential.Oranges,
    )
    fig2.update_traces(textinfo="percent+label")
    fig2.update_layout(height=380, font=dict(size=14))
    st.plotly_chart(fig2, use_container_width=True)

    # Navigation buttons under the pie chart
    nav_left, nav_center, nav_right = st.columns([1, 2, 1])

    with nav_left:
        if st.button("⬅ Previous", key="prev_btn"):
            if rank > 1:
                st.session_state.rank_index -= 1

    with nav_center:
        st.markdown(
            f"<p style='text-align:center; font-weight:700; color:#033e59; font-size:18px;'>"
            f"Rank {rank}: {selected_student['Student name']}</p>",
            unsafe_allow_html=True,
        )

    with nav_right:
        if st.button("Next ➡", key="next_btn"):
            if rank < total_students:
                st.session_state.rank_index += 1


# ---------------------------------------------------------
# TABLE – SELECTED COLUMN BOLD
# ---------------------------------------------------------
st.markdown("<div class='section-header'>Top Students</div>", unsafe_allow_html=True)

df_display = df_sorted[
    [
        "Student name",
        "Email",
        "Aptitude (20) [Q1–Q20]",
        "AI/ML/DS (30) [Q21–Q40 + Q61–Q70]",
        "FSD/DB (30) [Q41–Q60 + Q71–Q80]",
        "DevOps/Testing (20) [Q81–Q100]",
        "Overall (100)",
    ]
].copy()


def highlight_selected(col: pd.Series):
    style = []
    for _ in col:
        if col.name == selected_section:
            style.append("font-weight: 900; color:#033e59;")
        else:
            style.append("")
    return style


st.dataframe(
    df_display.style.apply(highlight_selected, axis=0),
    height=450,
    use_container_width=True,
)

# ---------------------------------------------------------
# DOWNLOAD CSV
# ---------------------------------------------------------
full_csv = df.to_csv(index=False)

st.download_button(
    "⬇ Download Full Results (All Students)",
    full_csv,
    "full_results.csv",
    mime="text/csv",
    use_container_width=True,
)
