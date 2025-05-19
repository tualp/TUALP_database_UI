import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt

# --- 7. Visualization ---
def plot_pump_curve(df, x_axis, y_axis, legend):
    plt.figure(figsize=(8, 5))
    if legend and legend in df.columns:
        for key, grp in df.groupby(legend):
            plt.scatter(grp[x_axis], grp[y_axis], marker='o', label=str(key))
        plt.legend(title=legend)
    else:
        plt.scatter(df[x_axis], df[y_axis], marker='o')
    plt.xlabel(x_axis)
    plt.ylabel(y_axis)
    plt.title(f'{y_axis} vs {x_axis}')
    plt.grid(True)
    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.close()

    
# --- 1. Login Page ---
def login():
    st.title("Pump Test Data App - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "TUALP" and password == "TUALP2025":
            st.session_state['logged_in'] = True
        else:
            st.error("Invalid credentials")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- 2. Data Upload & Default Data ---
st.sidebar.title("Data Source")
default_files = {
    "Gas test": "All_pump.csv",
    "Catalog": "Catalog_All.csv",
    "Viscosity and emulsion": "df_Viscosity.csv"
}

db_choice = st.sidebar.selectbox("Select Default Database", list(default_files.keys()))
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

# Reset session state when database changes
if 'previous_db' not in st.session_state:
    st.session_state['previous_db'] = None

current_db = uploaded_file.name if uploaded_file else db_choice
if current_db != st.session_state['previous_db']:
    # Reset all filter selections to "All"
    for col in ["Test", "Pump", "Case", "TargetRPM", "TargetP_psi"]:
        st.session_state[f"selected_{col}"] = "All"
    st.session_state['previous_db'] = current_db

def load_data(file, file_name=None):
    if file is not None:
        if file_name is None:
            file_name = file
        ext = os.path.splitext(file_name)[1].lower()
        if ext == ".csv":
            return pd.read_csv(file)
        elif ext == ".xlsx":
            return pd.read_excel(file)
        else:
            st.error("Unsupported file type!")
            return None
    return None

df = None
if uploaded_file:
    df = load_data(uploaded_file, uploaded_file.name)
    st.session_state['data_source'] = "User Upload"
    st.session_state['db_name'] = uploaded_file.name
else:
    df = load_data(default_files[db_choice])
    st.session_state['data_source'] = db_choice
    st.session_state['db_name'] = db_choice
print(df)
st.session_state['df'] = df

# --- 5. Data Status Page (Dynamic Cross-Filtering) ---
st.sidebar.write("## Data Status Selection")

# Start with the full dataframe
filtered_df = df.copy()

# Get unique values for each filter, always include "All" at the top
def get_options(series):
    opts = sorted(series.dropna().unique())
    return ["All"] + opts

# Initialize session state for each filter
for col in ["Test", "Pump", "Case", "TargetRPM", "TargetP_psi"]:
    if f"selected_{col}" not in st.session_state:
        st.session_state[f"selected_{col}"] = "All"

# Dynamic filtering logic
# 1. Show all filters, each time options are based on current filtered_df
# 2. After each selection, filter the dataframe for the next filter's options

# Test filter
test_options = get_options(filtered_df["Test"])
selected_test = st.sidebar.selectbox("Test", test_options, index=test_options.index(st.session_state["selected_Test"]))
if selected_test != "All":
    filtered_df = filtered_df[filtered_df["Test"] == selected_test]
st.session_state["selected_Test"] = selected_test

# Pump filter
pump_options = get_options(filtered_df["Pump"])
selected_pump = st.sidebar.selectbox("Pump", pump_options, index=pump_options.index(st.session_state["selected_Pump"]))
if selected_pump != "All":
    filtered_df = filtered_df[filtered_df["Pump"] == selected_pump]
st.session_state["selected_Pump"] = selected_pump

# Case filter
case_options = get_options(filtered_df["Case"])
print(filtered_df["Case"])
print(case_options)
selected_case = st.sidebar.selectbox("Case", case_options, index=case_options.index(st.session_state["selected_Case"]))
if selected_case != "All":
    filtered_df = filtered_df[filtered_df["Case"] == selected_case]
st.session_state["selected_Case"] = selected_case

# TargetRPM filter
rpm_options = get_options(filtered_df["TargetRPM"])
selected_rpm = st.sidebar.selectbox("TargetRPM", rpm_options, index=rpm_options.index(st.session_state["selected_TargetRPM"]))
if selected_rpm != "All":
    filtered_df = filtered_df[filtered_df["TargetRPM"] == selected_rpm]
st.session_state["selected_TargetRPM"] = selected_rpm

# TargetP_psi filter
psi_options = get_options(filtered_df["TargetP_psi"])
selected_psi = st.sidebar.selectbox("TargetP_psi", psi_options, index=psi_options.index(st.session_state["selected_TargetP_psi"]))
if selected_psi != "All":
    filtered_df = filtered_df[filtered_df["TargetP_psi"] == selected_psi]
st.session_state["selected_TargetP_psi"] = selected_psi

# Now filtered_df is the result of all current selections
test_data = filtered_df

# --- Page Navigation ---
tab1, tab2 = st.tabs(["Test data", "Data visualization"])

with tab1:
    if test_data.empty:
        st.info('No data available for the current filter selection.')
    else:
        # --- Test Case Info ---
        if 'Comments' in test_data.columns:
            st.write("### Test Case Info")
            unique_comments = test_data['Comments'].dropna().unique()
            if len(unique_comments) > 0:
                for i, comment in enumerate(unique_comments, 1):
                    # If there are multiple comments, show only up to first period
                    if len(unique_comments) > 1:
                        comment = comment.split('.')[0] + '.'
                    st.write(f"Test {i}:", comment)
            else:
                st.write("No case available")
        st.write("### Test Data")
        st.dataframe(test_data)

with tab2:
    st.write("## Data Visualization")
    if test_data.empty:
        st.info('No data available for the current filter selection.')
    else:
        # Only use numeric columns for x, y, legend
        numeric_columns = [col for col in test_data.columns if pd.api.types.is_numeric_dtype(test_data[col])]
        # Move 'QL_bpd' and 'QG_bpd' to the top if they exist
        preferred = [col for col in ['QL_bpd', 'QG_bpd'] if col in numeric_columns]
        other_cols = [col for col in numeric_columns if col not in preferred]
        vis_columns = preferred + other_cols
        x_axis = st.selectbox("X-axis", vis_columns, key="x_axis_vis")
        preferred1 = ['DP_psi','Head_ft']
        preferred2 = [col for col in numeric_columns if col.startswith('dp')]
        other_cols = [col for col in numeric_columns if col not in preferred1 and col not in preferred2]
        vis_columns = preferred1 + preferred2 + other_cols
        y_axis = st.selectbox("Y-axis", vis_columns, key="y_axis_vis")
        # Legend: move columns starting with 'Target' to the top
        target_cols = [col for col in numeric_columns if col.startswith('Target')]
        other_legend_cols = [col for col in numeric_columns if col not in target_cols]
        legend_columns = target_cols + other_legend_cols if target_cols else numeric_columns
        legend = st.selectbox("Legend", legend_columns, key="legend_vis")
        if st.button("Plot", key="plot_vis"):
            plot_pump_curve(test_data, x_axis, y_axis, legend)

# --- 8. Export ---
st.write("## Export Data")
if st.button("Export Filtered Data"):
    csv = test_data.to_csv(index=False)
    st.download_button("Download CSV", csv, "filtered_data.csv", "text/csv")
