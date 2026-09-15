import streamlit as st
import pandas as pd
import plotly.express as px

from signal_detector import (
    prepare_data,
    detect_signals,
    summarize_signals
)

from submission_checker import (
    check_submission,
    calculate_module_scores,
    generate_gap_report
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Drug Safety Signal Detector",
    page_icon="💊",
    layout="wide"
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title(
    "💊 Drug Safety Signal Detector & "
    "Regulatory Submission Readiness Checker"
)

st.caption(
    "AI-assisted pharmacovigilance and CTD readiness analysis"
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title("Application Modes")

mode = st.sidebar.radio(
    "Select Mode",
    [
        "Signal Detection",
        "Submission Readiness"
    ]
)


# =========================================================
# MODE 1 — SIGNAL DETECTION
# =========================================================

if mode == "Signal Detection":

    st.header("🔎 Drug Safety Signal Detection")

    st.write(
        """
        Upload adverse-event reports and the system will analyze
        drug-event combinations using Proportional Reporting Ratio
        (PRR) statistics.
        """
    )

    uploaded_file = st.file_uploader(
        "Upload adverse-event CSV",
        type=["csv"]
    )

    # -----------------------------------------------------
    # DEMO DATA
    # -----------------------------------------------------

    if uploaded_file is None:

        st.info(
            "No file uploaded. Using built-in demonstration data."
        )

        demo_data = pd.DataFrame({
            "drug": [
                "DrugA", "DrugA", "DrugA", "DrugA",
                "DrugA", "DrugA", "DrugA",
                "DrugB", "DrugB", "DrugB",
                "DrugB", "DrugC", "DrugC",
                "DrugC", "DrugC", "DrugD",
                "DrugD", "DrugD", "DrugE", "DrugE"
            ],

            "event": [
                "Headache", "Headache", "Headache",
                "Nausea", "Nausea", "Fatigue",
                "Fatigue",
                "Headache", "Nausea", "Fatigue",
                "Rash", "Headache", "Nausea",
                "Rash", "Rash", "Headache",
                "Nausea", "Rash", "Headache", "Nausea"
            ]
        })

        data = demo_data

    else:

        data = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")

    st.dataframe(
        data.head(20),
        use_container_width=True
    )

    # -----------------------------------------------------
    # COLUMN SELECTION
    # -----------------------------------------------------

    st.subheader("Column Mapping")

    columns = list(data.columns)

    col1, col2 = st.columns(2)

    with col1:
        drug_column = st.selectbox(
            "Drug column",
            columns
        )

    with col2:
        event_column = st.selectbox(
            "Adverse-event column",
            columns,
            index=min(1, len(columns) - 1)
        )

    cleaned_data = prepare_data(
        data,
        drug_column,
        event_column
    )

    # -----------------------------------------------------
    # PARAMETERS
    # -----------------------------------------------------

    st.subheader("Signal Detection Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:
        min_reports = st.number_input(
            "Minimum reports",
            min_value=1,
            value=3
        )

    with col2:
        prr_threshold = st.number_input(
            "PRR threshold",
            min_value=0.1,
            value=2.0,
            step=0.1
        )

    with col3:
        chi_threshold = st.number_input(
            "Chi-square threshold",
            min_value=0.1,
            value=4.0,
            step=0.1
        )

    # -----------------------------------------------------
    # RUN ANALYSIS
    # -----------------------------------------------------

    if st.button(
        "🚀 Run Signal Detection",
        type="primary"
    ):

        results = detect_signals(
            cleaned_data,
            min_reports=min_reports,
            prr_threshold=prr_threshold,
            chi_square_threshold=chi_threshold
        )

        summary = summarize_signals(results)

        st.session_state["signal_results"] = results

        # -------------------------------------------------
        # KPI CARDS
        # -------------------------------------------------

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Drug-Event Combinations",
            summary["total_combinations"]
        )

        c2.metric(
            "Potential Signals",
            summary["potential_signals"]
        )

        c3.metric(
            "Highest PRR",
            summary["highest_prr"]
        )

    # -----------------------------------------------------
    # DISPLAY RESULTS
    # -----------------------------------------------------

    if "signal_results" in st.session_state:

        results = st.session_state["signal_results"]

        st.subheader("Signal Detection Results")

        if results.empty:

            st.warning(
                "No drug-event combinations met the minimum "
                "report threshold."
            )

        else:

            st.dataframe(
                results,
                use_container_width=True
            )

            potential = results[
                results["signal"] == "Potential Signal"
            ]

            if not potential.empty:

                st.subheader("🚨 Potential Safety Signals")

                st.dataframe(
                    potential,
                    use_container_width=True
                )

                # -----------------------------------------
                # PRR CHART
                # -----------------------------------------

                chart_data = results.copy()

                chart_data["Drug-Event"] = (
                    chart_data["drug"]
                    + " → "
                    + chart_data["event"]
                )

                chart_data = chart_data.sort_values(
                    "PRR",
                    ascending=False
                ).head(15)

                fig = px.bar(
                    chart_data,
                    x="Drug-Event",
                    y="PRR",
                    title="Top Drug-Event PRR Values"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            # ---------------------------------------------
            # DOWNLOAD
            # ---------------------------------------------

            csv = results.to_csv(index=False)

            st.download_button(
                "⬇️ Download Signal Report",
                csv,
                "signal_detection_report.csv",
                "text/csv"
            )


# =========================================================
# MODE 2 — SUBMISSION READINESS
# =========================================================

else:

    st.header("📋 Regulatory Submission Readiness")

    st.write(
        """
        Check a drug dossier outline against the configured
        CTD checklist and identify missing sections.
        """
    )

    # -----------------------------------------------------
    # INPUT METHOD
    # -----------------------------------------------------

    input_method = st.radio(
        "Dossier input method",
        [
            "Enter sections manually",
            "Upload CSV"
        ]
    )

    dossier_items = []

    if input_method == "Enter sections manually":

        text = st.text_area(
            "Enter dossier sections — one per line",
            height=250,
            placeholder=(
                "CTD introduction\n"
                "Quality overall summary\n"
                "Drug substance information\n"
                "Manufacturing process\n"
                "Pharmacology studies"
            )
        )

        dossier_items = [
            item.strip()
            for item in text.splitlines()
            if item.strip()
        ]

    else:

        uploaded = st.file_uploader(
            "Upload dossier outline CSV",
            type=["csv"]
        )

        if uploaded:

            dossier_df = pd.read_csv(uploaded)

            st.dataframe(
                dossier_df.head(20),
                use_container_width=True
            )

            selected_column = st.selectbox(
                "Select section-name column",
                dossier_df.columns
            )

            dossier_items = (
                dossier_df[selected_column]
                .dropna()
                .astype(str)
                .tolist()
            )

    # -----------------------------------------------------
    # ANALYZE
    # -----------------------------------------------------

    if st.button(
        "🔍 Check Submission Readiness",
        type="primary"
    ):

        if not dossier_items:

            st.error(
                "Please enter or upload at least one dossier section."
            )

        else:

            checklist = check_submission(
                dossier_items
            )

            scores = calculate_module_scores(
                checklist
            )

            gaps = generate_gap_report(
                checklist
            )

            st.session_state["checklist"] = checklist
            st.session_state["scores"] = scores
            st.session_state["gaps"] = gaps

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------

    if "scores" in st.session_state:

        scores = st.session_state["scores"]
        checklist = st.session_state["checklist"]
        gaps = st.session_state["gaps"]

        st.subheader("📊 Module Completeness")

        # Overall score

        total_completed = scores["Completed"].sum()
        total_sections = scores["Total"].sum()

        overall = (
            total_completed / total_sections * 100
            if total_sections > 0
            else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Overall Completeness",
            f"{overall:.1f}%"
        )

        c2.metric(
            "Completed Sections",
            total_completed
        )

        c3.metric(
            "Missing Sections",
            len(gaps)
        )

        # ---------------------------------------------
        # SCORE TABLE
        # ---------------------------------------------

        st.dataframe(
            scores,
            use_container_width=True
        )

        # ---------------------------------------------
        # COMPLETENESS CHART
        # ---------------------------------------------

        fig = px.bar(
            scores,
            x="Module",
            y="Completeness",
            title="CTD Module Completeness"
        )

        fig.update_yaxes(
            range=[0, 100]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ---------------------------------------------
        # GAP REPORT
        # ---------------------------------------------

        st.subheader("⚠️ Gap Report")

        if gaps.empty:

            st.success(
                "No missing sections were detected "
                "against the configured checklist."
            )

        else:

            st.dataframe(
                gaps,
                use_container_width=True
            )

            gap_csv = gaps.to_csv(
                index=False
            )

            st.download_button(
                "⬇️ Download Gap Report",
                gap_csv,
                "submission_gap_report.csv",
                "text/csv"
            )

        # ---------------------------------------------
        # FULL CHECKLIST
        # ---------------------------------------------

        st.subheader("📑 Detailed Checklist")

        st.dataframe(
            checklist,
            use_container_width=True
        )
