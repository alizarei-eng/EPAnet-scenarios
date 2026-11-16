import json
import math
import statistics
from pathlib import Path
from datetime import datetime


# ============================================================
# 1. REPORT CONFIGURATION
# ============================================================

REPORT_TYPES = {
    "1": {
        "name": "Scenario Comparison",
        "keywords": [
            "comparison", "scenario", "reference",
            "difference", "change", "variation"
        ],
        "source": "comparison"
    },
    "2": {
        "name": "Element Analysis",
        "keywords": [
            "element", "node", "junction", "pipe",
            "link", "reservoir", "tank", "pump", "valve"
        ],
        "source": "simulation"
    },
    "3": {
        "name": "Network Performance",
        "keywords": [
            "network", "performance", "pressure",
            "head", "flow", "velocity", "headloss",
            "demand", "status"
        ],
        "source": "simulation"
    },
    "4": {
        "name": "Sensitivity Analysis",
        "keywords": [
            "sensitivity", "demand", "diameter",
            "parameter", "effect", "influence"
        ],
        "source": "comparison"
    },
    "5": {
        "name": "Correlation Analysis",
        "keywords": [
            "correlation", "pearson", "spearman", "kendall"
        ],
        "source": "comparison"
    },
    "6": {
        "name": "Scenario Ranking",
        "keywords": [
            "ranking", "rank", "score", "best",
            "worst", "performance"
        ],
        "source": "comparison"
    }
}


DETAIL_LEVELS = {
    "1": "Statistical Summary",
    "2": "Element-Level Data",
    "3": "Time-Series Data"
}


# ============================================================
# 2. JSON UTILITIES
# ============================================================

def load_json(file_path):

    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"JSON file not found: {file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, file_path):

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False
        )


def normalize_text(value):

    return str(value).strip().lower().replace("_", " ").replace("-", " ")


# ============================================================
# 3. SCENARIO INFORMATION
# ============================================================

def get_scenario_names(scenario_data):

    scenarios = scenario_data.get("Scenarios", [])

    names = []

    for scenario in scenarios:

        if not isinstance(scenario, dict):
            continue

        name = scenario.get("Scenario name")

        if name:
            names.append(str(name))

    return names


def select_scenarios(scenario_names):

    print("\nSCENARIO SELECTION")
    print("-" * 50)

    print("1. One scenario")
    print("2. Multiple scenarios")
    print("3. All scenarios")
    print("4. Filter by input parameters")

    choice = input("\nSelect option: ").strip()

    if choice == "1":

        for index, name in enumerate(scenario_names, 1):
            print(f"{index}. {name}")

        selected = input("Enter scenario number: ").strip()

        try:
            return [scenario_names[int(selected) - 1]]
        except (ValueError, IndexError):
            print("[WARNING] Invalid selection.")
            return []

    elif choice == "2":

        for index, name in enumerate(scenario_names, 1):
            print(f"{index}. {name}")

        selected = input(
            "Enter scenario numbers separated by commas: "
        ).strip()

        result = []

        try:
            for item in selected.split(","):
                index = int(item.strip()) - 1

                if 0 <= index < len(scenario_names):
                    result.append(scenario_names[index])

        except ValueError:
            print("[WARNING] Invalid selection.")
            return []

        return list(dict.fromkeys(result))

    elif choice == "3":
        return list(scenario_names)

    elif choice == "4":

        print(
            "\nParameter-based filtering requires the parameter "
            "values to be available in the scenario definitions."
        )

        parameter = input(
            "Enter parameter name (e.g. Demand, Diameter): "
        ).strip()

        value = input("Enter exact value to search: ").strip()

        return {
            "filter_type": "parameter",
            "parameter": parameter,
            "value": value
        }

    else:
        print("[WARNING] Invalid selection.")
        return []


# ============================================================
# 4. ELEMENT SELECTION
# ============================================================

def select_elements():

    print("\nELEMENT SELECTION")
    print("-" * 50)

    print("1. One element")
    print("2. Multiple elements")
    print("3. All elements")
    print("4. Filter elements")

    choice = input("\nSelect option: ").strip()

    if choice == "1":

        element = input("Enter element ID: ").strip()

        return {
            "selection": "one",
            "elements": [element]
        }

    elif choice == "2":

        elements = input(
            "Enter element IDs separated by commas: "
        ).strip()

        return {
            "selection": "multiple",
            "elements": [
                item.strip()
                for item in elements.split(",")
                if item.strip()
            ]
        }

    elif choice == "3":

        return {
            "selection": "all",
            "elements": []
        }

    elif choice == "4":

        field = input("Enter element property: ").strip()
        value = input("Enter property value: ").strip()

        return {
            "selection": "filter",
            "field": field,
            "value": value
        }

    return None


# ============================================================
# 5. DETAIL LEVEL SELECTION
# ============================================================

def select_detail_levels():

    print("\nREPORT DETAIL LEVEL")
    print("-" * 50)

    for key, value in DETAIL_LEVELS.items():
        print(f"{key}. {value}")

    print("4. All detail levels")

    selected = input(
        "\nEnter choices separated by commas: "
    ).strip()

    if selected == "4":
        return list(DETAIL_LEVELS.values())

    result = []

    for item in selected.split(","):

        item = item.strip()

        if item in DETAIL_LEVELS:
            result.append(DETAIL_LEVELS[item])

    return result


# ============================================================
# 6. RECURSIVE JSON SEARCH
# ============================================================

def find_matching_sections(data, keywords, current_path="$"):

    matches = []

    if isinstance(data, dict):

        for key, value in data.items():

            key_text = normalize_text(key)
            child_path = f"{current_path}.{key}"

            if any(
                keyword in key_text
                for keyword in keywords
            ):

                matches.append({
                    "path": child_path,
                    "data": value
                })

            matches.extend(
                find_matching_sections(
                    value,
                    keywords,
                    child_path
                )
            )

    elif isinstance(data, list):

        for index, value in enumerate(data):

            child_path = f"{current_path}[{index}]"

            matches.extend(
                find_matching_sections(
                    value,
                    keywords,
                    child_path
                )
            )

    return matches


# ============================================================
# 7. NUMERIC DATA EXTRACTION
# ============================================================

def collect_numeric_values(data, path="$"):

    values = []

    if isinstance(data, bool):
        return values

    if isinstance(data, (int, float)):

        if math.isfinite(float(data)):
            values.append({
                "path": path,
                "value": float(data)
            })

    elif isinstance(data, dict):

        for key, value in data.items():

            values.extend(
                collect_numeric_values(
                    value,
                    f"{path}.{key}"
                )
            )

    elif isinstance(data, list):

        for index, value in enumerate(data):

            values.extend(
                collect_numeric_values(
                    value,
                    f"{path}[{index}]"
                )
            )

    return values


# ============================================================
# 8. STATISTICAL SUMMARY
# ============================================================

def calculate_statistics(numeric_values):

    values = [
        item["value"]
        for item in numeric_values
    ]

    if not values:
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "standard_deviation": None
        }

    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "standard_deviation": (
            statistics.stdev(values)
            if len(values) > 1
            else 0.0
        )
    }


# ============================================================
# 9. SCENARIO FILTER
# ============================================================

def filter_data_by_scenarios(data, selected_scenarios):

    if not isinstance(selected_scenarios, list):
        return data

    if not selected_scenarios:
        return data

    selected = set(selected_scenarios)

    def recursive_filter(value):

        if isinstance(value, dict):

            scenario_name = (
                value.get("Scenario name")
                or value.get("scenario_name")
                or value.get("Scenario")
                or value.get("scenario")
            )

            if scenario_name is not None:
                if str(scenario_name) not in selected:
                    return None

            result = {}

            for key, child in value.items():

                filtered = recursive_filter(child)

                if filtered is not None:
                    result[key] = filtered

            return result

        if isinstance(value, list):

            result = []

            for child in value:

                filtered = recursive_filter(child)

                if filtered is not None:
                    result.append(filtered)

            return result

        return value

    return recursive_filter(data)


# ============================================================
# 10. REPORT SECTION BUILDER
# ============================================================

def build_report_section(
    report_key,
    report_config,
    simulation_data,
    comparison_data,
    selected_scenarios,
    detail_levels
):

    source_name = report_config["source"]

    source_data = (
        comparison_data
        if source_name == "comparison"
        else simulation_data
    )

    if isinstance(selected_scenarios, list):
        source_data = filter_data_by_scenarios(
            source_data,
            selected_scenarios
        )

    keywords = report_config["keywords"]

    matching_sections = find_matching_sections(
        source_data,
        keywords
    )

    numeric_values = collect_numeric_values(source_data)

    report = {
        "report_name": report_config["name"],
        "source_file": (
            "Comparison_Results.json"
            if source_name == "comparison"
            else "Simulation_Results.json"
        ),
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "selected_scenarios": selected_scenarios,
        "selected_detail_levels": detail_levels,
        "matched_sections_count": len(matching_sections)
    }

    if "Statistical Summary" in detail_levels:

        report["statistical_summary"] = calculate_statistics(
            numeric_values
        )

    if "Element-Level Data" in detail_levels:

        report["element_level_data"] = matching_sections

    if "Time-Series Data" in detail_levels:

        report["time_series_data"] = find_matching_sections(
            source_data,
            ["time", "time series", "timestamp", "period"]
        )

    if not matching_sections:

        report["notice"] = (
            "No matching section was found using the available "
            "JSON keys. Inspect the source JSON structure before "
            "interpreting this report."
        )

    return report


# ============================================================
# 11. REPORT TYPE SELECTION
# ============================================================

def select_report_types():

    print("\nREPORT SELECTION")
    print("-" * 50)

    for key, config in REPORT_TYPES.items():
        print(f"{key}. {config['name']}")

    print("7. All reports")

    selected = input(
        "\nEnter report numbers separated by commas: "
    ).strip()

    if selected == "7":
        return list(REPORT_TYPES.keys())

    result = []

    for item in selected.split(","):

        item = item.strip()

        if item in REPORT_TYPES:
            result.append(item)

    return list(dict.fromkeys(result))


# ============================================================
# 12. OUTPUT FORMAT SELECTION
# ============================================================

def select_output_mode():

    print("\nOUTPUT STRUCTURE")
    print("-" * 50)

    print("1. One combined JSON file")
    print("2. Separate JSON file for each report")

    choice = input("\nSelect option: ").strip()

    if choice == "1":
        return "combined"

    if choice == "2":
        return "separate"

    print("[WARNING] Invalid selection. Combined mode selected.")

    return "combined"


# ============================================================
# 13. SAVE REPORTS
# ============================================================

def save_reports(reports, output_directory, output_mode):

    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    if output_mode == "combined":

        output_file = output_directory / "Reports.json"

        save_json(
            {
                "generated_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "reports": reports
            },
            output_file
        )

        print(f"\n[OK] Combined report saved:\n{output_file}")

    else:

        for report_name, report_data in reports.items():

            safe_name = report_name.replace(" ", "_")

            output_file = (
                output_directory / f"{safe_name}.json"
            )

            save_json(report_data, output_file)

            print(
                f"\n[OK] Report saved:\n{output_file}"
            )


# ============================================================
# 14. MAIN REPORT GENERATOR
# ============================================================

def run_report_generator(
    simulation_file,
    comparison_file,
    scenario_file,
    output_directory
):

    print("\n")
    print("#" * 65)
    print("EPANET INTERACTIVE REPORT GENERATOR")
    print("#" * 65)

    simulation_data = load_json(simulation_file)
    comparison_data = load_json(comparison_file)
    scenario_data = load_json(scenario_file)

    scenario_names = get_scenario_names(scenario_data)

    if not scenario_names:
        print("[WARNING] No scenario names found.")
        return

    print(f"\nAvailable scenarios: {len(scenario_names)}")

    while True:

        print("\nMAIN MENU")
        print("-" * 50)

        print("1. Generate reports")
        print("2. Show available scenarios")
        print("0. Exit")

        main_choice = input("\nSelect option: ").strip()

        if main_choice == "0":
            print("\nReport generator closed.")
            break

        elif main_choice == "2":

            for index, name in enumerate(scenario_names, 1):
                print(f"{index}. {name}")

            continue

        elif main_choice != "1":

            print("[WARNING] Invalid option.")
            continue

        selected_report_keys = select_report_types()

        if not selected_report_keys:
            print("[WARNING] No report selected.")
            continue

        selected_scenarios = select_scenarios(
            scenario_names
        )

        if not selected_scenarios:
            print("[WARNING] No scenario selected.")
            continue

        if isinstance(selected_scenarios, dict):
            print(
                "[NOTICE] Parameter filter selection is recorded "
                "as a filter request, but automatic filtering by "
                "parameter values is not enabled in this version."
            )

        detail_levels = select_detail_levels()

        if not detail_levels:
            print("[WARNING] No detail level selected.")
            continue

        output_mode = select_output_mode()

        reports = {}

        for report_key in selected_report_keys:

            config = REPORT_TYPES[report_key]

            report_data = build_report_section(
                report_key=report_key,
                report_config=config,
                simulation_data=simulation_data,
                comparison_data=comparison_data,
                selected_scenarios=selected_scenarios,
                detail_levels=detail_levels
            )

            reports[config["name"]] = report_data

            print(
                f"[OK] Prepared: {config['name']}"
            )

        save_reports(
            reports=reports,
            output_directory=output_directory,
            output_mode=output_mode
        )

        print("\n[OK] Report generation process completed.")


# ============================================================
# 15. STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":

    project_dir = Path(__file__).resolve().parent
    results_dir = project_dir / "network_information_result"

    try:

        run_report_generator(
            simulation_file=(
                results_dir / "Simulation_Results.json"
            ),
            comparison_file=(
                results_dir / "Comparison_Results.json"
            ),
            scenario_file=(
                results_dir / "Scenario_Definitions.json"
            ),
            output_directory=results_dir / "Reports"
        )

    except Exception as error:

        print("\n[ERROR] Report generator failed.")
        print(error)