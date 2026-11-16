
"""
EPANET Interactive Report Generator
Version: 1.0

Purpose:
Generate guided engineering reports from EPANET simulation
and comparison results.

Features:
- Step-by-step interactive guidance
- Educational explanations for report options
- Scenario selection:
    1. One scenario
    2. Multiple scenarios
    3. All scenarios
    4. Filter by input parameters
- Element selection
- Statistical Summary
- Element-Level Analysis
- Time-Series Analysis
- Scenario Comparison
- Network Performance
- Sensitivity Analysis
- Correlation Analysis
- Scenario Ranking
- Combined JSON output
- Separate JSON output
- Report generation confirmation
- Multiple report sessions

Data sources:
- Simulation_Results.json
- Comparison_Results.json
- Scenario_Definitions.json
"""

import json
import math
import statistics

from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# 1. CONFIGURATION
# ============================================================

REPORT_TYPES = {
    "1": "Scenario Comparison",
    "2": "Element Analysis",
    "3": "Network Performance",
    "4": "Sensitivity Analysis",
    "5": "Correlation Analysis",
    "6": "Scenario Ranking"
}

DETAIL_LEVELS = {
    "1": "Statistical Summary",
    "2": "Element-Level",
    "3": "Time-Series"
}

GROUPS = {
    "1": "Node",
    "2": "Link"
}


# ============================================================
# 2. GENERAL UTILITIES
# ============================================================

def timestamp():

    return datetime.now(
        timezone.utc
    ).isoformat()


def print_line():

    print("-" * 70)


def print_section(title):

    print("\n")
    print("=" * 70)
    print(title)
    print("=" * 70)


def pause():

    input("\nPress Enter to continue...")


def load_json(file_path):

    file_path = Path(file_path)

    if not file_path.is_file():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def clean_json(value):

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, dict):

        return {
            str(key): clean_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):

        return [
            clean_json(item)
            for item in value
        ]

    return str(value)


def save_json(data, file_path):

    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            clean_json(data),
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False
        )


def ask_choice(
    prompt,
    valid_choices
):

    while True:

        value = input(prompt).strip()

        if value in valid_choices:
            return value

        print(
            "\nInvalid selection."
        )

        print(
            "Available choices:",
            ", ".join(valid_choices)
        )


def ask_yes_no(
    prompt,
    default=True
):

    suffix = (
        "[Y/n]"
        if default
        else "[y/N]"
    )

    answer = input(
        f"{prompt} {suffix}: "
    ).strip().lower()

    if not answer:
        return default

    return answer in (
        "y",
        "yes",
        "1"
    )


def calculate_statistics(values):

    numeric_values = []

    for value in values:

        if isinstance(value, bool):
            continue

        try:

            number = float(value)

        except (TypeError, ValueError):

            continue

        if math.isfinite(number):

            numeric_values.append(number)

    if not numeric_values:

        return {
            "Count": 0,
            "Minimum": None,
            "Maximum": None,
            "Mean": None,
            "Median": None,
            "Standard_Deviation": None
        }

    return {

        "Count": len(numeric_values),

        "Minimum": min(numeric_values),

        "Maximum": max(numeric_values),

        "Mean": statistics.mean(
            numeric_values
        ),

        "Median": statistics.median(
            numeric_values
        ),

        "Standard_Deviation": (
            statistics.stdev(numeric_values)
            if len(numeric_values) > 1
            else 0.0
        )
    }


# ============================================================
# 3. DATA INITIALIZATION
# ============================================================

def initialize_report_data(
    simulation_file,
    comparison_file,
    scenario_file
):

    print_section(
        "INITIALIZING REPORT DATA"
    )

    simulation_data = load_json(
        simulation_file
    )

    print("[OK] Simulation results loaded.")

    comparison_data = load_json(
        comparison_file
    )

    print("[OK] Comparison results loaded.")

    scenario_data = load_json(
        scenario_file
    )

    print("[OK] Scenario definitions loaded.")

    return (
        simulation_data,
        comparison_data,
        scenario_data
    )


# ============================================================
# 4. SCENARIO INFORMATION
# ============================================================

def get_scenario_names(scenario_data):

    names = []

    for scenario in scenario_data.get(
        "Scenarios",
        []
    ):

        if not isinstance(scenario, dict):
            continue

        name = scenario.get(
            "Scenario name"
        )

        if name:
            names.append(str(name))

    return names


def get_successful_scenarios(simulation_data):

    scenarios = simulation_data.get(
        "Scenarios",
        {}
    )

    if not isinstance(scenarios, dict):
        return []

    return [

        name

        for name, data in scenarios.items()

        if data.get("Status") == "SUCCESS"

    ]


def get_available_scenarios(
    simulation_data,
    scenario_data
):

    defined = get_scenario_names(
        scenario_data
    )

    successful = set(
        get_successful_scenarios(
            simulation_data
        )
    )

    return [
        name
        for name in defined
        if name in successful
    ]


def display_scenarios(scenario_names):

    print_section(
        "AVAILABLE SUCCESSFUL SCENARIOS"
    )

    for index, name in enumerate(
        scenario_names,
        start=1
    ):

        print(
            f"{index:>3}. {name}"
        )

    print_line()

    print(
        "Total successful scenarios:",
        len(scenario_names)
    )


# ============================================================
# 5. SCENARIO INPUT EXTRACTION
# ============================================================

def extract_scenario_parameters(scenario_data):
    """
    Extract numeric scenario inputs directly from
    Scenario_Definitions.json.

    Supports:
    - Direct numeric values
    - Nested list/dictionary values such as Demand
    """

    result = {}

    for scenario in scenario_data.get(
        "Scenarios",
        []
    ):

        name = scenario.get(
            "Scenario name"
        )

        if not name:
            continue

        parameters = {}

        for change in scenario.get(
            "Changes",
            []
        ):

            component = change.get(
                "Component",
                ""
            )

            element = change.get(
                "Element",
                ""
            )

            parameter = change.get(
                "Parameter",
                ""
            )

            base_key = (
                f"{component}.{element}.{parameter}"
            )

            value = change.get(
                "New SI Value"
            )

            if isinstance(
                value,
                (int, float)
            ) and not isinstance(value, bool):

                parameters[base_key] = float(value)

            elif isinstance(value, list):

                for item in value:

                    if not isinstance(item, dict):
                        continue

                    for sub_key, sub_value in item.items():

                        if (
                            isinstance(sub_value, (int, float))
                            and not isinstance(sub_value, bool)
                        ):

                            parameters[
                                f"{base_key}.{sub_key}"
                            ] = float(sub_value)

        result[name] = parameters

    return result


def get_available_input_parameters(scenario_data):

    scenario_parameters = (
        extract_scenario_parameters(
            scenario_data
        )
    )

    return sorted({

        key

        for parameters in scenario_parameters.values()

        for key in parameters

    })


# ============================================================
# 6. GUIDED SCENARIO SELECTION
# ============================================================

def select_scenarios(
    scenario_names,
    scenario_data
):

    print_section(
        "STEP 1 - SCENARIO SELECTION"
    )

    print(
        "This step determines which simulation scenarios"
    )

    print(
        "will be included in the report."
    )

    print_line()

    print("1. One scenario")
    print("2. Multiple scenarios")
    print("3. All successful scenarios")
    print("4. Filter scenarios by input parameters")

    print_line()

    print(
        "\nExplanation:"
    )

    print(
        "One scenario: useful for examining a single simulation."
    )

    print(
        "Multiple scenarios: useful for comparing selected cases."
    )

    print(
        "All scenarios: includes every successful simulation."
    )

    print(
        "Parameter filter: selects scenarios using Demand,"
    )

    print(
        "Diameter, or other numeric input parameters."
    )

    choice = ask_choice(
        "\nSelect scenario selection method: ",
        {"1", "2", "3", "4"}
    )

    # --------------------------------------------------------
    # ALL SCENARIOS
    # --------------------------------------------------------

    if choice == "3":

        print(
            "\nAll successful scenarios selected."
        )

        return list(scenario_names)

    # --------------------------------------------------------
    # ONE OR MULTIPLE SCENARIOS
    # --------------------------------------------------------

    if choice in ("1", "2"):

        display_scenarios(
            scenario_names
        )

        if choice == "1":

            valid = {
                str(i)
                for i in range(
                    1,
                    len(scenario_names) + 1
                )
            }

            selected = ask_choice(
                "\nEnter scenario number: ",
                valid
            )

            return [
                scenario_names[
                    int(selected) - 1
                ]
            ]

        while True:

            raw = input(
                "\nEnter scenario numbers separated by commas: "
            ).strip()

            indexes = []

            valid_input = True

            for item in raw.split(","):

                try:

                    number = int(item.strip())

                except ValueError:

                    valid_input = False
                    break

                if not (
                    1 <= number <= len(scenario_names)
                ):

                    valid_input = False
                    break

                indexes.append(number - 1)

            if valid_input and indexes:

                selected = list(dict.fromkeys(

                    scenario_names[index]

                    for index in indexes

                ))

                return selected

            print(
                "\nInvalid scenario numbers."
            )

            print(
                "Please try again."
            )

    # --------------------------------------------------------
    # FILTER BY INPUT PARAMETERS
    # --------------------------------------------------------

    scenario_parameters = (
        extract_scenario_parameters(
            scenario_data
        )
    )

    available_parameters = sorted({

        key

        for parameters in scenario_parameters.values()

        for key in parameters

    })

    if not available_parameters:

        print(
            "\nNo numeric input parameters are available."
        )

        return []

    print_section(
        "PARAMETER FILTER"
    )

    print(
        "Choose an input parameter to filter the scenarios."
    )

    print(
        "Example: Demand or Pipe Diameter."
    )

    for index, parameter in enumerate(
        available_parameters,
        start=1
    ):

        print(
            f"{index}. {parameter}"
        )

    valid = {
        str(i)
        for i in range(
            1,
            len(available_parameters) + 1
        )
    }

    parameter_choice = ask_choice(
        "\nSelect parameter: ",
        valid
    )

    selected_parameter = available_parameters[
        int(parameter_choice) - 1
    ]

    print_section(
        "FILTER CONDITION"
    )

    print("1. Equal to")
    print("2. Greater than")
    print("3. Less than")
    print("4. Greater than or equal to")
    print("5. Less than or equal to")

    operator = ask_choice(
        "\nSelect condition: ",
        {"1", "2", "3", "4", "5"}
    )

    while True:

        try:

            target = float(
                input(
                    "\nEnter filter value: "
                ).strip()
            )

            break

        except ValueError:

            print(
                "Please enter a valid numeric value."
            )

    selected = []

    for scenario_name in scenario_names:

        value = scenario_parameters.get(
            scenario_name,
            {}
        ).get(
            selected_parameter
        )

        if value is None:
            continue

        conditions = {

            "1": value == target,

            "2": value > target,

            "3": value < target,

            "4": value >= target,

            "5": value <= target

        }

        if conditions[operator]:

            selected.append(
                scenario_name
            )

    print(
        "\nMatching scenarios:",
        len(selected)
    )

    return selected


# ============================================================
# 7. GUIDED REPORT SELECTION
# ============================================================

def select_report_types():

    print_section(
        "STEP 2 - REPORT TYPE SELECTION"
    )

    print(
        "Choose the engineering analysis you want to generate."
    )

    print_line()

    explanations = {

        "1": (
            "Scenario Comparison",
            "Compares hydraulic results against the reference "
            "scenario. Useful for identifying changes in "
            "Pressure, Flow, Velocity and Headloss."
        ),

        "2": (
            "Element Analysis",
            "Examines individual nodes or links. You can select "
            "elements and inspect their statistics or time series."
        ),

        "3": (
            "Network Performance",
            "Displays network-level performance indicators "
            "calculated by ComparisonEngine."
        ),

        "4": (
            "Sensitivity Analysis",
            "Shows how input parameter changes relate to "
            "hydraulic output changes using the existing "
            "linear sensitivity calculations."
        ),

        "5": (
            "Correlation Analysis",
            "Displays Pearson, Spearman and Kendall relationships "
            "between scenario inputs and hydraulic outputs."
        ),

        "6": (
            "Scenario Ranking",
            "Ranks scenarios independently for available "
            "hydraulic indicators. Mathematical ranking does "
            "not necessarily mean engineering optimum."
        )
    }

    for key, (name, explanation) in explanations.items():

        print(f"\n{key}. {name}")

        print(
            f"   {explanation}"
        )

    print("\n7. All reports")

    print_line()

    print(
        "You can select multiple reports."
    )

    print(
        "Example: 1,2,5"
    )

    while True:

        raw = input(
            "\nEnter report numbers: "
        ).strip()

        if raw == "7":

            return list(REPORT_TYPES.keys())

        selected = []

        valid_input = True

        for item in raw.split(","):

            item = item.strip()

            if item not in REPORT_TYPES:

                valid_input = False
                break

            if item not in selected:

                selected.append(item)

        if valid_input and selected:

            return selected

        print(
            "\nInvalid selection. Please try again."
        )


# ============================================================
# 8. GUIDED DETAIL LEVEL SELECTION
# ============================================================

def select_detail_levels():

    print_section(
        "STEP 3 - REPORT DETAIL LEVEL"
    )

    print(
        "Choose how much detail should be included."
    )

    print_line()

    print(
        "1. Statistical Summary"
    )

    print(
        "   Provides Minimum, Maximum, Mean, Median,"
    )

    print(
        "   Standard Deviation and sample count."
    )

    print(
        "\n2. Element-Level"
    )

    print(
        "   Shows the selected network element names"
    )

    print(
        "   and their associated results."
    )

    print(
        "\n3. Time-Series"
    )

    print(
        "   Includes values at individual simulation"
    )

    print(
        "   time steps."
    )

    print(
        "\n4. All available detail levels"
    )

    print_line()

    choice = ask_choice(
        "\nSelect detail level: ",
        {"1", "2", "3", "4"}
    )

    if choice == "4":

        return list(
            DETAIL_LEVELS.values()
        )

    return [
        DETAIL_LEVELS[choice]
    ]


# ============================================================
# 9. RESTORE SERIALIZED DATAFRAME
# ============================================================

def restore_dataframe(serialized):
    """
    Restore the ResultsManager split-format DataFrame.

    Expected structure:
    {
        "Format": "split",
        "Index": [...],
        "Columns": [...],
        "Data": [...]
    }
    """

    if not isinstance(serialized, dict):
        return None

    if serialized.get("Format") != "split":
        return None

    try:

        index = serialized["Index"]

        columns = serialized["Columns"]

        data = serialized["Data"]

        if len(data) != len(index):
            return None

        if any(
            len(row) != len(columns)
            for row in data
        ):

            return None

        return {

            "Index": index,

            "Columns": columns,

            "Data": data

        }

    except (
        KeyError,
        TypeError
    ):

        return None


def dataframe_values(dataframe):

    values = []

    if not dataframe:
        return values

    for row in dataframe["Data"]:

        for value in row:

            if isinstance(value, bool):
                continue

            try:

                number = float(value)

            except (TypeError, ValueError):

                continue

            if math.isfinite(number):

                values.append(number)

    return values


def get_element_series(
    dataframe,
    element
):

    if not dataframe:
        return None

    columns = dataframe["Columns"]

    try:

        column_index = columns.index(
            element
        )

    except ValueError:

        return None

    result = []

    for time_value, row in zip(
        dataframe["Index"],
        dataframe["Data"]
    ):

        value = row[column_index]

        # Preserve strings for Status and other
        # non-numeric result variables.

        try:

            numeric_value = float(value)

            if not math.isfinite(numeric_value):
                output_value = None
            else:
                output_value = numeric_value

        except (TypeError, ValueError):

            output_value = value

        result.append({

            "Time": time_value,

            "Value": output_value

        })

    return result


# ============================================================
# 10. GROUP AND VARIABLE SELECTION
# ============================================================

def select_group():

    print_section(
        "STEP 4 - NETWORK ELEMENT GROUP"
    )

    print(
        "Nodes represent junctions, reservoirs and tanks."
    )

    print(
        "Links represent pipes, pumps and valves."
    )

    print_line()

    print("1. Nodes")
    print("2. Links")

    choice = ask_choice(
        "\nSelect element group: ",
        {"1", "2"}
    )

    return GROUPS[choice]


def get_result_group_name(group):

    if group == "Node":
        return "Node_Results"

    return "Link_Results"


def available_variables(
    simulation_data,
    selected_scenarios,
    group
):

    result_name = get_result_group_name(
        group
    )

    variables = set()

    all_scenarios = simulation_data.get(
        "Scenarios",
        {}
    )

    for scenario_name in selected_scenarios:

        scenario = all_scenarios.get(
            scenario_name,
            {}
        )

        result_group = scenario.get(
            result_name,
            {}
        )

        variables.update(
            result_group.keys()
        )

    return sorted(variables)


def select_variables(
    simulation_data,
    selected_scenarios,
    group
):

    variables = available_variables(
        simulation_data,
        selected_scenarios,
        group
    )

    if not variables:

        print(
            "\nNo variables are available for this group."
        )

        return []

    print_section(
        "RESULT VARIABLE SELECTION"
    )

    print(
        "Choose the hydraulic variable to examine."
    )

    print(
        "Examples:"
    )

    print(
        "Node: Pressure, Head, Demand"
    )

    print(
        "Link: Flow, Velocity, Headloss"
    )

    print(
        "Status may also be available."
    )

    print_line()

    for index, variable in enumerate(
        variables,
        start=1
    ):

        print(
            f"{index}. {variable}"
        )

    print(
        "\n0. All available variables"
    )

    while True:

        choice = input(
            "\nSelect variable: "
        ).strip()

        if choice == "0":

            return variables

        try:

            index = int(choice) - 1

            if 0 <= index < len(variables):

                return [
                    variables[index]
                ]

        except ValueError:

            pass

        print(
            "Invalid selection. Try again."
        )


# ============================================================
# 11. ELEMENT SELECTION
# ============================================================

def available_elements(
    simulation_data,
    selected_scenarios,
    group,
    variables
):

    result_name = get_result_group_name(
        group
    )

    elements = set()

    all_scenarios = simulation_data.get(
        "Scenarios",
        {}
    )

    for scenario_name in selected_scenarios:

        scenario = all_scenarios.get(
            scenario_name,
            {}
        )

        result_group = scenario.get(
            result_name,
            {}
        )

        for variable in variables:

            dataframe = restore_dataframe(
                result_group.get(variable)
            )

            if dataframe:

                elements.update(
                    dataframe["Columns"]
                )

    return sorted(elements)


def select_elements(
    simulation_data,
    selected_scenarios,
    group,
    variables
):

    print_section(
        "STEP 5 - ELEMENT SELECTION"
    )

    print(
        "Choose which network elements should be included."
    )

    print_line()

    print("1. One element")
    print("2. Multiple elements")
    print("3. All available elements")

    print_line()

    choice = ask_choice(
        "\nSelect element selection method: ",
        {"1", "2", "3"}
    )

    elements = available_elements(
        simulation_data,
        selected_scenarios,
        group,
        variables
    )

    if not elements:

        print(
            "\nNo elements found."
        )

        return []

    if choice == "3":

        return elements

    print_section(
        "AVAILABLE ELEMENTS"
    )

    for index, element in enumerate(
        elements,
        start=1
    ):

        print(
            f"{index}. {element}"
        )

    if choice == "1":

        valid = {
            str(i)
            for i in range(
                1,
                len(elements) + 1
            )
        }

        selected = ask_choice(
            "\nEnter element number: ",
            valid
        )

        return [
            elements[
                int(selected) - 1
            ]
        ]

    while True:

        raw = input(
            "\nEnter element numbers separated by commas: "
        ).strip()

        selected_indexes = []

        valid_input = True

        for item in raw.split(","):

            try:

                number = int(item.strip())

            except ValueError:

                valid_input = False
                break

            if not (
                1 <= number <= len(elements)
            ):

                valid_input = False
                break

            selected_indexes.append(
                number - 1
            )

        if valid_input and selected_indexes:

            return list(dict.fromkeys(

                elements[index]

                for index in selected_indexes

            ))

        print(
            "Invalid selection. Try again."
        )


# ============================================================
# 12. ELEMENT ANALYSIS
# ============================================================

def build_element_analysis(
    simulation_data,
    selected_scenarios,
    detail_levels
):

    print_section(
        "ELEMENT ANALYSIS CONFIGURATION"
    )

    group = select_group()

    variables = select_variables(
        simulation_data,
        selected_scenarios,
        group
    )

    if not variables:

        return {
            "Status": "NO_DATA",
            "Reason": "No variables available."
        }

    elements = select_elements(
        simulation_data,
        selected_scenarios,
        group,
        variables
    )

    if not elements:

        return {
            "Status": "NO_DATA",
            "Reason": "No elements selected."
        }

    result_name = get_result_group_name(
        group
    )

    output = {

        "Group": group,

        "Variables": variables,

        "Selected_Elements": elements,

        "Scenarios": {}

    }

    all_scenarios = simulation_data.get(
        "Scenarios",
        {}
    )

    for scenario_name in selected_scenarios:

        scenario = all_scenarios.get(
            scenario_name,
            {}
        )

        result_group = scenario.get(
            result_name,
            {}
        )

        scenario_output = {}

        for variable in variables:

            dataframe = restore_dataframe(
                result_group.get(variable)
            )

            if not dataframe:
                continue

            variable_output = {}

            for element in elements:

                series = get_element_series(
                    dataframe,
                    element
                )

                if series is None:
                    continue

                element_output = {}

                if "Element-Level" in detail_levels:

                    element_output["Element"] = (
                        element
                    )

                if "Time-Series" in detail_levels:

                    element_output["Time_Series"] = (
                        series
                    )

                if "Statistical Summary" in detail_levels:

                    numeric_values = [

                        item["Value"]

                        for item in series

                        if isinstance(
                            item["Value"],
                            (int, float)
                        )

                        and not isinstance(
                            item["Value"],
                            bool
                        )

                    ]

                    element_output["Statistics"] = (
                        calculate_statistics(
                            numeric_values
                        )
                    )

                variable_output[element] = (
                    element_output
                )

            if variable_output:

                scenario_output[variable] = (
                    variable_output
                )

        output["Scenarios"][scenario_name] = (
            scenario_output
        )

    return output


# ============================================================
# 13. SCENARIO COMPARISON
# ============================================================

def build_scenario_comparison(
    comparison_data,
    selected_scenarios,
    detail_levels
):

    comparisons = comparison_data.get(
        "Scenario_Comparisons",
        {}
    )

    project_information = comparison_data.get(
        "Project_Information",
        {}
    )

    output = {

        "Reference_Scenario": (
            project_information.get(
                "Reference_Scenario"
            )
        ),

        "Scenarios": {},

        "Notice": (
            "This report uses the reference-based "
            "comparisons already generated by ComparisonEngine."
        )

    }

    for scenario_name in selected_scenarios:

        scenario_data = comparisons.get(
            scenario_name
        )

        if not scenario_data:
            continue

        scenario_output = {

            "Reference_Scenario": (
                scenario_data.get(
                    "Reference_Scenario"
                )
            ),

            "Node_Comparison": {},

            "Link_Comparison": {},

            "Missing_Variables": (
                scenario_data.get(
                    "Missing_Variables",
                    []
                )
            )

        }

        for group_name in (
            "Node_Comparison",
            "Link_Comparison"
        ):

            variables = scenario_data.get(
                group_name,
                {}
            )

            for variable, elements in variables.items():

                selected_elements = {}

                for element, data in elements.items():

                    element_output = {}

                    if (
                        "Statistical Summary"
                        in detail_levels
                    ):

                        for key in (

                            "Valid_Time_Steps",

                            "Reference_Statistics",

                            "Scenario_Statistics",

                            "Difference_Statistics",

                            "Percentage_Change_Statistics"

                        ):

                            if key in data:

                                element_output[key] = (
                                    data[key]
                                )

                    if "Element-Level" in detail_levels:

                        element_output["Element"] = (
                            element
                        )

                    if "Time-Series" in detail_levels:

                        if "Time_Series" in data:

                            element_output["Time_Series"] = (
                                data["Time_Series"]
                            )

                    selected_elements[element] = (
                        element_output
                    )

                if selected_elements:

                    scenario_output[group_name][
                        variable
                    ] = selected_elements

        output["Scenarios"][scenario_name] = (
            scenario_output
        )

    if not output["Scenarios"]:

        output["Notice"] = (
            "No reference-based comparison records "
            "were found for the selected scenarios. "
            "The reference scenario is not stored as "
            "a compared scenario."
        )

    return output


# ============================================================
# 14. NETWORK PERFORMANCE
# ============================================================

def build_network_performance(
    comparison_data,
    selected_scenarios,
    detail_levels
):

    performance = comparison_data.get(
        "Network_Performance",
        {}
    )

    output = {}

    for scenario_name in selected_scenarios:

        scenario_performance = performance.get(
            scenario_name
        )

        if not scenario_performance:
            continue

        if "Statistical Summary" in detail_levels:

            output[scenario_name] = (
                scenario_performance
            )

        else:

            output[scenario_name] = {

                "Available_Metrics": list(
                    scenario_performance.keys()
                ),

                "Notice": (
                    "Network_Performance currently stores "
                    "network-level statistics. For element "
                    "and time-series results, use Element Analysis."
                )

            }

    return {

        "Scenarios": output,

        "Notice": (
            "Network performance indicators are taken "
            "from ComparisonEngine."
        )

    }


# ============================================================
# 15. SENSITIVITY ANALYSIS
# ============================================================

def build_sensitivity_analysis(
    comparison_data,
    scenario_data,
    selected_scenarios
):

    sensitivity = comparison_data.get(
        "Sensitivity_Analysis",
        {}
    )

    scenario_parameters = (
        extract_scenario_parameters(
            scenario_data
        )
    )

    selected_parameters = sorted({

        key

        for scenario_name in selected_scenarios

        for key in scenario_parameters.get(
            scenario_name,
            {}
        )

    })

    comparison_inputs = comparison_data.get(
        "Scenario_Inputs",
        {}
    )

    output = {}

    for input_name, metrics in sensitivity.items():

        if selected_parameters:

            # ComparisonEngine uses INPUT::<input_name>
            # internally. Its JSON sensitivity section
            # uses the input name without the prefix.

            if input_name not in selected_parameters:
                continue

        output[input_name] = metrics

    missing_from_engine = []

    for parameter in selected_parameters:

        found = any(

            parameter == key

            for key in comparison_inputs.get(
                selected_scenarios[0],
                {}
            )

        ) if selected_scenarios else False

        if not found:

            missing_from_engine.append(
                parameter
            )

    return {

        "Sensitivity": output,

        "Selected_Scenarios": selected_scenarios,

        "Selected_Input_Parameters": selected_parameters,

        "Input_Parameters_Not_Processed_By_ComparisonEngine": (
            missing_from_engine
        ),

        "Interpretation": (
            "Sensitivity values are based on the linear "
            "input-output calculations already performed "
            "by ComparisonEngine. They describe observed "
            "relationships and do not establish causation."
        ),

        "Important_Limitation": (
            "When several input parameters vary together, "
            "their individual effects may be confounded. "
            "Demand values stored as nested lists in the "
            "scenario definitions are recognized by this "
            "report generator, but the current "
            "ComparisonEngine does not extract those nested "
            "values for sensitivity calculations."
        )

    }


# ============================================================
# 16. CORRELATION ANALYSIS
# ============================================================

def build_correlation_analysis(
    comparison_data,
    selected_scenarios
):

    correlation = comparison_data.get(
        "Correlation_Analysis",
        {}
    )

    observations = correlation.get(
        "Scenario_Observations",
        {}
    )

    correlations = correlation.get(
        "Correlations",
        {}
    )

    selected_observations = {

        name: observations[name]

        for name in selected_scenarios

        if name in observations

    }

    return {

        "Methods": correlation.get(
            "Method",
            []
        ),

        "Sample_Unit": correlation.get(
            "Sample_Unit"
        ),

        "Scenario_Observations": (
            selected_observations
        ),

        "Correlations": correlations,

        "Notice": (
            "Correlation coefficients were calculated "
            "by ComparisonEngine using all successful "
            "scenarios. The selected scenarios filter "
            "the displayed observations only. The "
            "coefficients are not recalculated here."
        ),

        "Available_Analysis_Level": (
            "Scenario-Level"
        ),

        "Unavailable_Analysis_Levels": [

            "Element-Level",

            "Time-Series"

        ],

        "Warning": (
            "Correlation does not establish causation. "
            "P-values should be interpreted carefully "
            "because the observations come from "
            "deterministic simulation scenarios."
        )

    }


# ============================================================
# 17. SCENARIO RANKING
# ============================================================

def build_scenario_ranking(
    comparison_data,
    selected_scenarios
):

    rankings = comparison_data.get(
        "Scenario_Rankings",
        {}
    )

    output = {}

    for metric_name, ranking_data in rankings.items():

        records = ranking_data.get(
            "Ranking",
            []
        )

        selected_records = [

            item

            for item in records

            if item.get(
                "Scenario"
            ) in selected_scenarios

        ]

        # Preserve the original ranking order.
        output[metric_name] = {

            "Ranking_Direction": (
                ranking_data.get(
                    "Ranking_Direction"
                )
            ),

            "Ranking": selected_records

        }

    return {

        "Rankings": output,

        "Notice": (
            "The rankings are inherited from "
            "ComparisonEngine. Filtering selected "
            "scenarios does not recalculate their "
            "relative rank."
        ),

        "Ranking_Limitation": (
            "Current ranking is a mathematical ordering "
            "of individual metrics, not a validated "
            "engineering optimum."
        ),

        "Unavailable_Options": [

            "Overall weighted network ranking",

            "Custom ranking with user-defined weights",

            "Target-range velocity ranking",

            "Ranking against engineering limits"

        ]

    }


# ============================================================
# 18. REPORT BUILDER
# ============================================================

def build_report(
    report_key,
    simulation_data,
    comparison_data,
    scenario_data,
    selected_scenarios,
    detail_levels
):

    report_name = REPORT_TYPES[
        report_key
    ]

    report = {

        "Report_Name": report_name,

        "Generated_At": timestamp(),

        "Selected_Scenarios": (
            selected_scenarios
        ),

        "Selected_Detail_Levels": (
            detail_levels
        ),

        "Data_Sources": {

            "Simulation": (
                "Simulation_Results.json"
            ),

            "Comparison": (
                "Comparison_Results.json"
            ),

            "Scenario_Definitions": (
                "Scenario_Definitions.json"
            )

        }

    }

    if report_key == "1":

        report["Results"] = (
            build_scenario_comparison(
                comparison_data,
                selected_scenarios,
                detail_levels
            )
        )

    elif report_key == "2":

        report["Results"] = (
            build_element_analysis(
                simulation_data,
                selected_scenarios,
                detail_levels
            )
        )

    elif report_key == "3":

        report["Results"] = (
            build_network_performance(
                comparison_data,
                selected_scenarios,
                detail_levels
            )
        )

    elif report_key == "4":

        report["Results"] = (
            build_sensitivity_analysis(
                comparison_data,
                scenario_data,
                selected_scenarios
            )
        )

    elif report_key == "5":

        report["Results"] = (
            build_correlation_analysis(
                comparison_data,
                selected_scenarios
            )
        )

    elif report_key == "6":

        report["Results"] = (
            build_scenario_ranking(
                comparison_data,
                selected_scenarios
            )
        )

    return report


# ============================================================
# 19. OUTPUT MODE
# ============================================================

def select_output_mode():

    print_section(
        "STEP 6 - OUTPUT FORMAT"
    )

    print(
        "Choose how the generated reports should be saved."
    )

    print_line()

    print(
        "1. One combined JSON file"
    )

    print(
        "   All selected reports are stored in Reports.json."
    )

    print(
        "\n2. Separate JSON files"
    )

    print(
        "   Each report is saved in its own JSON file."
    )

    print(
        "\n3. Both"
    )

    print(
        "   Creates the combined file and separate files."
    )

    print_line()

    choice = ask_choice(
        "\nSelect output format: ",
        {"1", "2", "3"}
    )

    return {

        "1": "combined",

        "2": "separate",

        "3": "both"

    }[choice]


# ============================================================
# 20. SAVE REPORTS
# ============================================================

def save_reports(
    reports,
    output_directory,
    output_mode
):

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # COMBINED FILE
    # --------------------------------------------------------

    if output_mode in (
        "combined",
        "both"
    ):

        combined_data = {

            "Generated_At": timestamp(),

            "Report_Count": len(reports),

            "Reports": reports

        }

        output_file = (
            output_directory / "Reports.json"
        )

        save_json(
            combined_data,
            output_file
        )

        print(
            "\n[OK] Combined report saved:"
        )

        print(output_file)

    # --------------------------------------------------------
    # SEPARATE FILES
    # --------------------------------------------------------

    if output_mode in (
        "separate",
        "both"
    ):

        for report_name, report_data in reports.items():

            safe_name = (
                report_name.replace(
                    " ",
                    "_"
                )
            )

            output_file = (
                output_directory
                / f"{safe_name}.json"
            )

            save_json(
                report_data,
                output_file
            )

            print(
                "\n[OK] Report saved:"
            )

            print(output_file)


# ============================================================
# 21. REVIEW SELECTIONS
# ============================================================

def review_selections(
    selected_reports,
    selected_scenarios,
    detail_levels,
    output_mode
):

    print_section(
        "REPORT GENERATION REVIEW"
    )

    print(
        "Please review your selections before generation."
    )

    print_line()

    print("\nSelected reports:")

    for key in selected_reports:

        print(
            "-",
            REPORT_TYPES[key]
        )

    print("\nSelected scenarios:")

    for scenario in selected_scenarios:

        print(
            "-",
            scenario
        )

    print("\nDetail levels:")

    for level in detail_levels:

        print(
            "-",
            level
        )

    print("\nOutput format:")

    print(
        "-",
        output_mode
    )

    print_line()

    return ask_yes_no(
        "\nGenerate reports using these selections?",
        default=True
    )


# ============================================================
# 22. GUIDED REPORT GENERATION
# ============================================================

def generate_reports_interactively(
    simulation_data,
    comparison_data,
    scenario_data,
    scenario_names,
    output_directory
):

    print_section(
        "NEW REPORT GENERATION SESSION"
    )

    print(
        "This guided process will help you configure"
    )

    print(
        "the reports step by step."
    )

    # --------------------------------------------------------
    # STEP 1 - REPORT SELECTION
    # --------------------------------------------------------

    selected_reports = select_report_types()

    # --------------------------------------------------------
    # STEP 2 - SCENARIO SELECTION
    # --------------------------------------------------------

    selected_scenarios = select_scenarios(
        scenario_names,
        scenario_data
    )

    if not selected_scenarios:

        print(
            "\nNo scenarios were selected."
        )

        return

    # --------------------------------------------------------
    # STEP 3 - DETAIL LEVEL
    # --------------------------------------------------------

    detail_levels = select_detail_levels()

    # --------------------------------------------------------
    # STEP 4 - OUTPUT MODE
    # --------------------------------------------------------

    output_mode = select_output_mode()

    # --------------------------------------------------------
    # STEP 5 - REVIEW
    # --------------------------------------------------------

    confirmed = review_selections(
        selected_reports,
        selected_scenarios,
        detail_levels,
        output_mode
    )

    if not confirmed:

        print(
            "\nReport generation cancelled."
        )

        return

    # --------------------------------------------------------
    # STEP 6 - BUILD REPORTS
    # --------------------------------------------------------

    reports = {}

    for report_key in selected_reports:

        report_name = REPORT_TYPES[
            report_key
        ]

        print_section(
            f"GENERATING: {report_name}"
        )

        try:

            report_data = build_report(
                report_key=report_key,
                simulation_data=simulation_data,
                comparison_data=comparison_data,
                scenario_data=scenario_data,
                selected_scenarios=selected_scenarios,
                detail_levels=detail_levels
            )

            reports[report_name] = (
                report_data
            )

            print(
                f"[OK] {report_name} prepared."
            )

        except Exception as error:

            print(
                f"[ERROR] Could not generate {report_name}."
            )

            print(error)

    # --------------------------------------------------------
    # STEP 7 - SAVE
    # --------------------------------------------------------

    if not reports:

        print(
            "\nNo reports were generated."
        )

        return

    save_reports(
        reports=reports,
        output_directory=output_directory,
        output_mode=output_mode
    )

    print_section(
        "REPORT GENERATION COMPLETED"
    )

    print(
        "Generated reports:",
        len(reports)
    )

    print(
        "Output directory:",
        output_directory
    )


# ============================================================
# 23. MAIN MENU
# ============================================================

def show_main_menu():

    print_section(
        "EPANET REPORT GENERATOR"
    )

    print(
        "Welcome to the interactive report generator."
    )

    print(
        "Use this menu to create and manage report sessions."
    )

    print_line()

    print(
        "1. Generate new reports"
    )

    print(
        "2. Show available scenarios"
    )

    print(
        "3. Show available input parameters"
    )

    print(
        "4. Show report guide"
    )

    print(
        "0. Exit"
    )

    print_line()

    return ask_choice(
        "\nSelect an option: ",
        {"0", "1", "2", "3", "4"}
    )


def show_report_guide():

    print_section(
        "REPORT GENERATOR - USER GUIDE"
    )

    print(
        "1. Scenario Comparison"
    )

    print(
        "   Compares scenario results against the reference."
    )

    print(
        "   Available data includes differences, percentage"
    )

    print(
        "   changes and time-series comparisons."
    )

    print_line()

    print(
        "2. Element Analysis"
    )

    print(
        "   Select Nodes or Links, hydraulic variables and"
    )

    print(
        "   individual elements. Then choose statistics,"
    )

    print(
        "   element-level information or time-series."
    )

    print_line()

    print(
        "3. Network Performance"
    )

    print(
        "   Displays network-level performance metrics"
    )

    print(
        "   already calculated by ComparisonEngine."
    )

    print_line()

    print(
        "4. Sensitivity Analysis"
    )

    print(
        "   Displays linear sensitivity indicators for"
    )

    print(
        "   numeric inputs recognized by ComparisonEngine."
    )

    print_line()

    print(
        "5. Correlation Analysis"
    )

    print(
        "   Displays Pearson, Spearman and Kendall results."
    )

    print(
        "   Current implementation is scenario-level."
    )

    print_line()

    print(
        "6. Scenario Ranking"
    )

    print(
        "   Displays existing metric-specific rankings."
    )

    print(
        "   It does not calculate an overall engineering score."
    )

    print_line()

    print(
        "Important:"
    )

    print(
        "The report generator does not rerun hydraulic"
    )

    print(
        "simulations or recalculate ComparisonEngine metrics."
    )

    print(
        "It organizes and filters the existing results."
    )

    pause()


# ============================================================
# 24. REPORT GENERATOR APPLICATION
# ============================================================

def run_report_generator(
    simulation_file,
    comparison_file,
    scenario_file,
    output_directory
):

    print("\n")

    print("#" * 70)

    print(
        "EPANET INTERACTIVE REPORT GENERATOR"
    )

    print("#" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    (
        simulation_data,
        comparison_data,
        scenario_data
    ) = initialize_report_data(
        simulation_file,
        comparison_file,
        scenario_file
    )

    # --------------------------------------------------------
    # SCENARIO AVAILABILITY
    # --------------------------------------------------------

    scenario_names = get_available_scenarios(
        simulation_data,
        scenario_data
    )

    if not scenario_names:

        print(
            "\n[ERROR] No successful scenarios are available."
        )

        return

    print_section(
        "PROJECT SUMMARY"
    )

    print(
        "Defined scenarios:",
        len(
            get_scenario_names(
                scenario_data
            )
        )
    )

    print(
        "Successful scenarios:",
        len(scenario_names)
    )

    print(
        "Available input parameters:",
        len(
            get_available_input_parameters(
                scenario_data
            )
        )
    )

    # --------------------------------------------------------
    # MAIN INTERACTIVE LOOP
    # --------------------------------------------------------

    while True:

        choice = show_main_menu()

        if choice == "0":

            print(
                "\nReport generator closed."
            )

            break

        elif choice == "2":

            display_scenarios(
                scenario_names
            )

            pause()

        elif choice == "3":

            print_section(
                "AVAILABLE INPUT PARAMETERS"
            )

            parameters = (
                get_available_input_parameters(
                    scenario_data
                )
            )

            if parameters:

                for index, parameter in enumerate(
                    parameters,
                    start=1
                ):

                    print(
                        f"{index}. {parameter}"
                    )

            else:

                print(
                    "No numeric input parameters found."
                )

            pause()

        elif choice == "4":

            show_report_guide()

        elif choice == "1":

            generate_reports_interactively(
                simulation_data=simulation_data,
                comparison_data=comparison_data,
                scenario_data=scenario_data,
                scenario_names=scenario_names,
                output_directory=output_directory
            )

            if not ask_yes_no(
                "\nReturn to the main menu?",
                default=True
            ):

                print(
                    "\nReport generator closed."
                )

                break


# ============================================================
# 25. STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":

    project_directory = Path(
        __file__
    ).resolve().parent

    results_directory = (
        project_directory
        / "network_information_result"
    )

    try:

        run_report_generator(

            simulation_file=(
                results_directory
                / "Simulation_Results.json"
            ),

            comparison_file=(
                results_directory
                / "Comparison_Results.json"
            ),

            scenario_file=(
                results_directory
                / "Scenario_Definitions.json"
            ),

            output_directory=(
                results_directory
                / "Reports"
            )

        )

    except Exception as error:

        print_section(
            "REPORT GENERATOR ERROR"
        )

        print(error)

        raise
