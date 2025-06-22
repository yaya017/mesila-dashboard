import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Mesila Dashboard", layout="wide")
st.title("📊 Mesila Selection Dashboard – MOFET Institute")
st.caption("Developed by Yair and his good friend 🧠")
months = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']
month_to_number = {month: i + 1 for i, month in enumerate(months)}

st.markdown("### 📅 Define Selection Year Range by Months")
start_month_name = st.selectbox("Start Month", months, index=4)
end_month_name = st.selectbox("End Month", months, index=3)
start_month = month_to_number[start_month_name]
end_month = month_to_number[end_month_name]

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    st.success("✅ File uploaded successfully.")
    df = pd.read_csv(uploaded_file)

    # Project mapping
    project_code_mapping = {
        1: "Regev", 2: "Conditional", 3: "Conversion", 10: "Chalutzim", 20: "General Referral",
        22: "TIL", 23: "PE Academics", 30: "Other", 1001: "New Direction 2020", 1002: "Summer 2023"
    }
    df["Project Code Label"] = df["Project Code"].map(project_code_mapping)

    df["Test Date"] = pd.to_datetime(df["Test Date"], errors="coerce")
    def calculate_selection_year(d, start_m, end_m):
        if pd.isnull(d):
            return np.nan
        if start_m <= end_m:
            if start_m <= d.month <= end_m:
                return d.year
            elif d.month < start_m:
                return d.year - 1
            else:
                return d.year + 1
        else:
            if d.month >= start_m or d.month <= end_m:
                return d.year
            else:
                return d.year - 1

    df["Selection Year"] = df["Test Date"].apply(lambda d: calculate_selection_year(d, start_month, end_month))

    
    # קידוד גורם מפנה מתוך קובץ אקסל
    try:
        sender_map = pd.read_excel("מפתח גורם מפנה 2 מחולק ערבי ודתי.xlsx")
        sender_map = sender_map.rename(columns={
            "SenderCode": "SenderCode",
            "ערבי=2/ יהודי=1": "Sector",
            "דתי יהודי=2/ לא דתי יהודי=1": "Religiosity"
        })
        sector_map = {1: "יהודי", 2: "ערבי"}
        relig_map = {1: "לא דתי", 2: "דתי"}
        sender_map["Sector"] = sender_map["Sector"].map(sector_map)
        sender_map["Religiosity"] = sender_map["Religiosity"].map(relig_map)
        df = df.merge(sender_map[["SenderCode", "Sector", "Religiosity"]], how="left", left_on="גורם מפנה / מס' קבוצה", right_on="SenderCode")
    except Exception as e:
        st.warning(f"⚠️ בעיה בטעינת מפתח גורם מפנה: {e}")
    st.success("✅ Data processing complete.")

    # Sidebar filters
    with st.sidebar:
        st.header("🎯 Population Filters")
        selected_gender = st.multiselect("Gender", options=sorted(df['Gender'].dropna().unique()))
        selected_project = st.multiselect("Project", options=sorted(df['Project Code Label'].dropna().unique()))
        selected_relig = st.multiselect("Religiosity", options=sorted(df['Religiosity'].dropna().unique()))
        selected_sector = st.multiselect("Sector", options=sorted(df['Sector'].dropna().unique()))
        selected_year = st.multiselect("Selection Year", options=sorted(df['Selection Year'].dropna().unique()))

    df_filtered = df.copy()
    if selected_gender:
        df_filtered = df_filtered[df_filtered['Gender'].isin(selected_gender)]
    if selected_project:
        df_filtered = df_filtered[df_filtered['Project Code Label'].isin(selected_project)]
    if selected_relig:
        df_filtered = df_filtered[df_filtered['Religiosity'].isin(selected_relig)]
    if selected_sector:
        df_filtered = df_filtered[df_filtered['Sector'].isin(selected_sector)]
    if selected_year:
        df_filtered = df_filtered[df_filtered['Selection Year'].isin(selected_year)]

    compare_by = st.selectbox("Compare groups by:", options=["None", "Gender", "Project Code Label", "Selection Year", "Sector", "Religiosity"])
    display_mode = st.radio("Display mode", ["Separate Graphs", "Combined Graph"])

    numeric_columns = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
    selected_vars = st.multiselect("Select variables to analyze", numeric_columns)
    analysis_type = st.radio("Select analysis type", ["Distribution", "Means", "Correlations"])

    if selected_vars:
        st.markdown(f"**Total N: {len(df_filtered)}**")

        if analysis_type == "Distribution":
            display_choice = st.radio("Display distribution as:", ["Graph", "Table"])

            for var in selected_vars:
                st.subheader(f"Distribution for {var}")
                if display_choice == "Graph":
                    if compare_by != "None":
                        groups = df_filtered[compare_by].dropna().unique()
                        if display_mode == "Combined Graph":
                            fig, ax = plt.subplots(figsize=(6, 3))
                            for g in groups:
                                subset = df_filtered[df_filtered[compare_by] == g][var].dropna()
                                sns.histplot(subset, stat="percent", label=f"{g} (N={len(subset)})", ax=ax)
                            ax.legend()
                            st.pyplot(fig)
                        else:
                            for g in groups:
                                subset = df_filtered[df_filtered[compare_by] == g][var].dropna()
                                fig, ax = plt.subplots(figsize=(6, 3))
                                sns.histplot(subset, stat="percent", ax=ax)
                                for patch in ax.patches:
                                    height = patch.get_height()
                                    if height > 0:
                                        ax.text(patch.get_x() + patch.get_width() / 2, height, f"{height:.1f}%", ha='center', va='bottom', fontsize=8)
                                ax.set_title(f"{var} - {g} (N={len(subset)})")
                                st.pyplot(fig)
                    else:
                        series = df_filtered[var].dropna()
                        fig, ax = plt.subplots(figsize=(6, 3))
                        sns.histplot(series, stat="percent", ax=ax)
                        for patch in ax.patches:
                            height = patch.get_height()
                            if height > 0:
                                ax.text(patch.get_x() + patch.get_width() / 2, height, f"{height:.1f}%", ha='center', va='bottom', fontsize=8)
                        ax.set_title(f"{var} (N={len(series)})")
                        st.pyplot(fig)
                elif display_choice == "Table":
                    if compare_by != "None":
                        groups = df_filtered[compare_by].dropna().unique()
                        for g in groups:
                            st.markdown(f"**{compare_by}: {g}**")
                            subset = df_filtered[df_filtered[compare_by] == g][var].dropna()
                            vc = subset.value_counts().sort_index()
                            pct = (vc / vc.sum() * 100).round(1)
                            table = pd.DataFrame({'Value': vc.index, 'Count': vc.values, 'Percent': pct.values})
                            st.dataframe(table)
                    else:
                        series = df_filtered[var].dropna()
                        vc = series.value_counts().sort_index()
                        pct = (vc / vc.sum() * 100).round(1)
                        table = pd.DataFrame({'Value': vc.index, 'Count': vc.values, 'Percent': pct.values})
                        st.dataframe(table)

                if var == "ציון מופת מסכם":
                    st.markdown("**Passing percentages:**")
                    thresholds = [7, 6, 5.5] if selected_project and any(p in ["Regev", "Conversion"] for p in selected_project) else [5.5]
                    for t in thresholds:
                        pct = (df_filtered[var] >= t).mean() * 100
                        st.write(f"Score ≥ {t}: {pct:.1f}%")

        elif analysis_type == "Means":
            st.subheader("Means")
            if compare_by != "None":
                mean_table = df_filtered.groupby(compare_by)[selected_vars].agg(['mean', 'count'])
                st.dataframe(mean_table)
            else:
                means = df_filtered[selected_vars].agg(['mean', 'count']).T
                means.columns = ['Mean', 'N']
                st.dataframe(means)

        elif analysis_type == "Correlations":
            st.subheader("Correlation Matrix")
            corr_matrix = df_filtered[selected_vars].corr()
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)
else:
    st.info("Please upload a CSV file to begin.")
