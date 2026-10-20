
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="📊",
    layout="wide"
)

# ---------------- HEADER ----------------
st.title("📊 Student Performance Analyzer")
st.write(
    "Analyze student marks, attendance, and academic performance "
    "using an interactive dashboard."
)

# ---------------- LOAD DATA ----------------
st.sidebar.header("📂 Student Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload student CSV",
    type=["csv"]
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        st.error("Unable to read the CSV file. Please check the file.")
        st.stop()
else:
    file_path = Path(__file__).parent / "students.csv"

    if not file_path.exists():
        st.error(
            "students.csv file not found. Upload a CSV file "
            "or add students.csv to the project folder."
        )
        st.stop()

    df = pd.read_csv(file_path)

# ---------------- VALIDATE DATA ----------------
subjects = ["Math", "Science", "English"]
required_columns = ["Name", *subjects, "Attendance"]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "Missing required CSV columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

if df.empty:
    st.warning("The CSV file contains no student records.")
    st.stop()

df["Name"] = df["Name"].astype("string").str.strip()

if df["Name"].isna().any() or df["Name"].eq("").any():
    st.error("Every student must have a name.")
    st.stop()

# Convert marks and attendance into numeric values
for column in subjects + ["Attendance"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

if df[subjects + ["Attendance"]].isna().any().any():
    st.error(
        "Marks and attendance must contain valid numbers. "
        "Please fix blank or non-numeric values in your CSV."
    )
    st.stop()

if not df[subjects + ["Attendance"]].apply(
    lambda column: column.between(0, 100).all()
).all():
    st.error("Marks and attendance must be between 0 and 100.")
    st.stop()

# ---------------- CALCULATE PERFORMANCE ----------------
df["Average"] = df[subjects].mean(axis=1).round(2)

def get_category(average):
    if average >= 85:
        return "Excellent"
    elif average >= 70:
        return "Good"
    elif average >= 50:
        return "Needs Improvement"
    else:
        return "At Risk"

df["Performance"] = df["Average"].apply(get_category)

# ---------------- SIDEBAR FILTER ----------------
st.sidebar.header("🔎 Filters")

student_options = ["All Students"] + sorted(
    df["Name"].unique().tolist()
)

selected_student = st.sidebar.selectbox(
    "Select student",
    student_options
)

if selected_student == "All Students":
    filtered_df = df.copy()
else:
    filtered_df = df[df["Name"] == selected_student].copy()

# ---------------- METRICS ----------------
st.subheader("📌 Performance Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Students", len(filtered_df))

with col2:
    st.metric(
        "Average Marks",
        f"{filtered_df['Average'].mean():.2f}/100"
    )

with col3:
    st.metric(
        "Average Attendance",
        f"{filtered_df['Attendance'].mean():.1f}%"
    )

with col4:
    st.metric(
        "Excellent Performers",
        int((filtered_df["Performance"] == "Excellent").sum())
    )

# ---------------- STUDENT RECORDS ----------------
st.subheader("📋 Student Records")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# ---------------- SUBJECT AVERAGES ----------------
st.subheader("📚 Subject-wise Average Marks")

subject_averages = (
    filtered_df[subjects]
    .mean()
    .reset_index()
)

subject_averages.columns = ["Subject", "Average Marks"]

subject_chart = px.bar(
    subject_averages,
    x="Subject",
    y="Average Marks",
    color="Subject",
    text_auto=".1f",
    title="Average Marks by Subject"
)

subject_chart.update_layout(
    showlegend=False,
    yaxis_range=[0, 100]
)

st.plotly_chart(subject_chart, use_container_width=True)

# ---------------- STUDENT COMPARISON ----------------
st.subheader("👩‍🎓 Student Performance Comparison")

student_chart = px.bar(
    filtered_df,
    x="Name",
    y="Average",
    color="Performance",
    text="Average",
    title="Average Marks by Student",
    hover_data=["Attendance"]
)

student_chart.update_layout(yaxis_range=[0, 100])

st.plotly_chart(student_chart, use_container_width=True)

# ---------------- ATTENDANCE ANALYSIS ----------------
st.subheader("🗓️ Attendance Analysis")

attendance_chart = px.bar(
    filtered_df,
    x="Name",
    y="Attendance",
    color="Attendance",
    text="Attendance",
    title="Attendance by Student",
    color_continuous_scale="Blues"
)

attendance_chart.update_layout(yaxis_range=[0, 100])

st.plotly_chart(attendance_chart, use_container_width=True)

# ---------------- PERFORMANCE CATEGORIES ----------------
st.subheader("🎯 Performance Categories")

category_counts = (
    filtered_df["Performance"]
    .value_counts()
    .rename_axis("Performance")
    .reset_index(name="Students")
)

category_chart = px.pie(
    category_counts,
    names="Performance",
    values="Students",
    title="Student Performance Distribution",
    hole=0.4
)

st.plotly_chart(category_chart, use_container_width=True)

# ---------------- SUBJECTS NEEDING ATTENTION ----------------
st.subheader("📝 Subjects Needing Attention")

if selected_student == "All Students":
    weak_subjects = subject_averages[
        subject_averages["Average Marks"] < 70
    ]

    if weak_subjects.empty:
        st.success(
            "No subject has an average below 70 in this dataset."
        )
    else:
        st.warning("These subjects have an average below 70:")
        st.dataframe(
            weak_subjects,
            use_container_width=True,
            hide_index=True
        )
else:
    student_row = filtered_df.iloc[0]
    weak_subjects = [
        subject for subject in subjects
        if student_row[subject] < 70
    ]

    if weak_subjects:
        st.warning(
            "Marks below 70 in: " + ", ".join(weak_subjects)
        )
    else:
        st.success("All subject marks are at least 70.")

# ---------------- DOWNLOAD REPORT ----------------
st.subheader("📥 Download Report")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Analyzed Student Data",
    data=csv_data,
    file_name="student_performance_report.csv",
    mime="text/csv"
)

st.caption(
    "Student Performance Analyzer | Educational project using "
    "sample or uploaded data. Performance categories are based "
    "on simple thresholds and are not official academic evaluations."
)
