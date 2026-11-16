
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_COMPARISON_FILE = (
    BASE_DIR
    / "network_information_result"
    / "Comparison_Results.json"
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_comparison_data(file_path, modified_time):
    """
    Load comparison JSON.
    modified_time is used to refresh cache after JSON changes.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def flatten_json(data, parent_path=""):
    """
    Convert nested JSON into parameter/value rows.
    """

    rows = []

    if isinstance(data, dict):
        for key, value in data.items():

            current_path = (
                f"{parent_path}.{key}"
                if parent_path
                else str(key)
            )

            rows.extend(
                flatten_json(value, current_path)
            )

    elif isinstance(data, list):
        for index, value in enumerate(data):

            current_path = f"{parent_path}[{index}]"

            rows.extend(
                flatten_json(value, current_path)
            )

    else:
        rows.append({
            "Parameter": parent_path,
            "Value": data
        })

    return rows


def get_scenario_names(data):
    """
    Find scenario names in common JSON structures.
    """

    names = set()

    def walk(value):
        if isinstance(value, dict):

            for key, item in value.items():

                normalized_key = str(key).lower().replace("_", " ")

                if normalized_key in (
                    "scenario name",
                    "scenario",
                    "scenario id"
                ):
                    if isinstance(item, (str, int, float)):
                        names.add(str(item))

                walk(item)

        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)

    return sorted(names)


def get_numeric_dataframe(rows):
    """
    Keep rows whose values can be converted to numbers.
    """

    numeric_rows = []

    for row in rows:
        value = row["Value"]

        if isinstance(value, bool) or value is None:
            continue

        try:
            numeric_value = float(value)

            numeric_rows.append({
                "Parameter": row["Parameter"],
                "Value": numeric_value
            })

        except (ValueError, TypeError):
            continue

    return pd.DataFrame(numeric_rows)


# ============================================================
# DASHBOARD
# ============================================================

def run_dashboard(comparison_file=DEFAULT_COMPARISON_FILE):

    st.set_page_config(
        page_title="EPANET Scenario Dashboard",
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(
        """
        <style>
        .main-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .sub-title {
            color: #8a94a6;
            font-size: 15px;
            margin-bottom: 22px;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(120, 140, 160, 0.08);
            border: 1px solid rgba(120, 140, 160, 0.18);
            padding: 14px;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    comparison_file = Path(comparison_file)

    st.markdown(
        '<div class="main-title">💧 EPANET Scenario Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        'Interactive hydraulic scenario analysis'
        '</div>',
        unsafe_allow_html=True
    )

    if not comparison_file.exists():
        st.error(
            f"Comparison file not found: {comparison_file}"
        )
        st.stop()

    modified_time = comparison_file.stat().st_mtime

    try:
        data = load_comparison_data(
            str(comparison_file),
            modified_time
        )
    except Exception as error:
        st.error(f"Could not load comparison JSON: {error}")
        st.stop()

    if not isinstance(data, dict):
        st.error("The comparison JSON root must be an object.")
        st.stop()

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.title("Analysis Controls")

    sections = list(data.keys())

    selected_section = st.sidebar.selectbox(
        "Select analysis section",
        sections
    )

    section_data = data[selected_section]

    all_rows = flatten_json(section_data)

    dataframe = pd.DataFrame(
        all_rows,
        columns=["Parameter", "Value"]
    )

    scenario_names = get_scenario_names(section_data)

    selected_scenario = st.sidebar.selectbox(
        "Select scenario",
        ["All scenarios"] + scenario_names
    )

    # --------------------------------------------------------
    # FILTER DATA
    # --------------------------------------------------------

    filtered_rows = all_rows

    if selected_scenario != "All scenarios":
        filtered_rows = [
            row for row in all_rows
            if selected_scenario.lower()
            in row["Parameter"].lower()
        ]

    filtered_df = pd.DataFrame(
        filtered_rows,
        columns=["Parameter", "Value"]
    )

    parameter_names = sorted(
        filtered_df["Parameter"].dropna().unique().tolist()
    )

    selected_parameter = None

    if parameter_names:
        selected_parameter = st.sidebar.selectbox(
            "Select parameter",
            parameter_names
        )

    # --------------------------------------------------------
    # TOP METRICS
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Analysis Sections",
        len(sections)
    )

    col2.metric(
        "Detected Scenarios",
        len(scenario_names)
    )

    col3.metric(
        "Available Data Rows",
        len(all_rows)
    )

    st.divider()

    # --------------------------------------------------------
    # SELECTED SECTION
    # --------------------------------------------------------

    st.subheader(selected_section)

    if selected_scenario != "All scenarios":
        st.caption(f"Selected scenario: {selected_scenario}")
    else:
        st.caption("Showing all available scenarios in this section.")

    # --------------------------------------------------------
    # PARAMETER VIEW
    # --------------------------------------------------------

    if selected_parameter:

        st.subheader("Selected Parameter")

        parameter_df = filtered_df[
            filtered_df["Parameter"] == selected_parameter
        ].copy()

        st.write(f"**Parameter:** {selected_parameter}")

        numeric_value = get_numeric_dataframe(
            parameter_df.to_dict("records")
        )

        if not numeric_value.empty:
            st.metric(
                "Numeric value",
                f"{numeric_value.iloc[0]['Value']:,.6g}"
            )

        else:
            st.write(parameter_df["Value"].astype(str).tolist())

    # --------------------------------------------------------
    # NUMERIC DATA
    # --------------------------------------------------------

    numeric_df = get_numeric_dataframe(filtered_rows)

    if not numeric_df.empty:

        st.subheader("Numeric Data Visualization")

        chart_parameters = sorted(
            numeric_df["Parameter"].unique().tolist()
        )

        selected_chart_parameter = st.selectbox(
            "Choose parameter for chart",
            chart_parameters,
            key="chart_parameter"
        )

        chart_df = numeric_df[
            numeric_df["Parameter"] == selected_chart_parameter
        ].copy()

        if not chart_df.empty:

            chart_df["Record"] = range(1, len(chart_df) + 1)

            figure = px.line(
                chart_df,
                x="Record",
                y="Value",
                markers=True,
                title=selected_chart_parameter,
                template="plotly_white"
            )

            figure.update_layout(
                height=420,
                xaxis_title="Data record",
                yaxis_title="Value",
                hovermode="x unified"
            )

            st.plotly_chart(
                figure,
                use_container_width=True
            )

    else:
        st.info(
            "No numeric values were found in this section."
        )

    # --------------------------------------------------------
    # DATA TABLE
    # --------------------------------------------------------

    st.divider()

    st.subheader("Detailed Data")

    search_text = st.text_input(
        "Search in parameter names",
        placeholder="Type a keyword..."
    )

    display_df = filtered_df.copy()

    if search_text:
        display_df = display_df[
            display_df["Parameter"].str.contains(
                search_text,
                case=False,
                na=False
            )
        ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # RAW JSON
    # --------------------------------------------------------

    with st.expander("View selected section JSON"):
        st.json(section_data)


if __name__ == "__main__":
    run_dashboard()
