import json
from pathlib import Path
from datetime import datetime

from project_paths import PATHS


# =========================================================
# 1. PATH CONFIGURATION
# =========================================================

BASE_DIR = PATHS.project_dir
INPUT_FILE = PATHS.network_si
OUTPUT_DIR = PATHS.results_dir
OUTPUT_FILE = PATHS.network_inspection


# =========================================================
# 2. COMPONENT DEFINITIONS
# =========================================================

COMPONENTS = {
    "Junctions": {
        "parameters": {
            "Elevation": {
                "label": "Elevation",
                "category": "Hydraulic",
                "candidate": True
            },
            "Demands": {
                "label": "Demand",
                "category": "Hydraulic",
                "candidate": True
            }
        }
    },

    "Reservoirs": {
        "parameters": {
            "Head": {
                "label": "Head",
                "category": "Hydraulic",
                "candidate": True
            },
            "Pattern": {
                "label": "Pattern",
                "category": "Hydraulic",
                "candidate": True
            }
        }
    },

    "Tanks": {
        "parameters": {
            "Elevation": {
                "label": "Elevation",
                "category": "Hydraulic",
                "candidate": True
            },
            "Initial level": {
                "label": "Initial level",
                "category": "Hydraulic",
                "candidate": True
            },
            "Minimum level": {
                "label": "Minimum level",
                "category": "Hydraulic",
                "candidate": True
            },
            "Maximum level": {
                "label": "Maximum level",
                "category": "Hydraulic",
                "candidate": True
            },
            "Diameter": {
                "label": "Diameter",
                "category": "Hydraulic",
                "candidate": True
            },
            "Minimum volume": {
                "label": "Minimum volume",
                "category": "Hydraulic",
                "candidate": True
            }
        }
    },

    "Pipes": {
        "parameters": {
            "Length": {
                "label": "Length",
                "category": "Hydraulic",
                "candidate": True
            },
            "Diameter": {
                "label": "Diameter",
                "category": "Hydraulic",
                "candidate": True
            },
            "Roughness": {
                "label": "Roughness",
                "category": "Hydraulic",
                "candidate": True
            },
            "Status": {
                "label": "Status",
                "category": "Operational",
                "candidate": True
            },
            "Check valve": {
                "label": "Check valve",
                "category": "Operational",
                "candidate": True
            }
        }
    },

    "Pumps": {
        "parameters": {
            "Type": {
                "label": "Pump type",
                "category": "Hydraulic",
                "candidate": True
            },
            "Power": {
                "label": "Power",
                "category": "Hydraulic",
                "candidate": True
            },
            "Curve": {
                "label": "Pump curve",
                "category": "Hydraulic",
                "candidate": True
            },
            "Speed": {
                "label": "Speed",
                "category": "Operational",
                "candidate": True
            }
        }
    },

    "Valves": {
        "parameters": {
            "Diameter": {
                "label": "Diameter",
                "category": "Hydraulic",
                "candidate": True
            },
            "Type": {
                "label": "Valve type",
                "category": "Hydraulic",
                "candidate": True
            },
            "Setting": {
                "label": "Setting",
                "category": "Hydraulic",
                "candidate": True
            },
            "Minor loss": {
                "label": "Minor loss",
                "category": "Hydraulic",
                "candidate": True
            }
        }
    }
}


# =========================================================
# 3. LOAD NETWORK INFORMATION
# =========================================================

def load_network_information(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Network information file not found:\n{file_path}"
        )

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Invalid network JSON structure."
        )

    return data


# =========================================================
# 4. GENERAL HELPER FUNCTIONS
# =========================================================

def get_component_list(data, component_name):

    components = data.get(component_name, [])

    if isinstance(components, dict):
        return list(components.values())

    if isinstance(components, list):
        return components

    return []


def extract_parameter(record, parameter_name):

    if parameter_name not in record:
        return False, None

    return True, record[parameter_name]


# =========================================================
# 5. INSPECT COMPONENTS
# =========================================================

def inspect_component(component_name, records):

    component_result = {
        "Component type": component_name,
        "Count": len(records),
        "Elements": [],
        "Available parameters": [],
        "Scenario candidates": []
    }

    parameter_definitions = COMPONENTS[
        component_name
    ]["parameters"]

    available_parameters = set()

    for record in records:

        if not isinstance(record, dict):
            continue

        element_name = record.get("Name", "Unknown")

        element_result = {
            "Name": element_name,
            "Parameters": {}
        }

        for parameter_name, definition in parameter_definitions.items():

            exists, value = extract_parameter(
                record,
                parameter_name
            )

            if exists:

                element_result["Parameters"][
                    parameter_name
                ] = value

                available_parameters.add(
                    parameter_name
                )

                if parameter_name not in component_result[
                    "Scenario candidates"
                ]:

                    component_result[
                        "Scenario candidates"
                    ].append(parameter_name)

        component_result["Elements"].append(
            element_result
        )

    component_result["Available parameters"] = sorted(
        available_parameters
    )

    return component_result


# =========================================================
# 6. INSPECT ALL NETWORK COMPONENTS
# =========================================================

def inspect_network(network_data, source_file=None):

    inspection = {
        "Inspection information": {
            "Created at": datetime.now().isoformat(),
            "Source file": Path(source_file).name if source_file else INPUT_FILE.name
        },

        "Network summary": network_data.get(
            "Summary", {}
        ),

        "Unit information": network_data.get(
            "Unit Information", {}
        ),

        "Components": {},

        "Total elements": 0
    }

    for component_name in COMPONENTS:

        records = get_component_list(
            network_data,
            component_name
        )

        result = inspect_component(
            component_name,
            records
        )

        inspection["Components"][
            component_name
        ] = result

        inspection["Total elements"] += result["Count"]

    # Preserve network-level information
    inspection["Patterns"] = network_data.get(
        "Patterns", []
    )

    inspection["Curves"] = network_data.get(
        "Curves", []
    )

    inspection["Connectivity"] = network_data.get(
        "Connectivity", {}
    )

    return inspection


# =========================================================
# 7. DISPLAY INSPECTION RESULTS
# =========================================================

def display_inspection(inspection):

    print("\n" + "=" * 60)
    print("             NETWORK INSPECTION REPORT")
    print("=" * 60)

    print(
        f"\nTotal network elements: "
        f"{inspection['Total elements']}"
    )

    for component_name, component in inspection[
        "Components"
    ].items():

        print("\n" + "-" * 60)

        print(
            f"{component_name}: "
            f"{component['Count']} elements"
        )

        print(
            "Available parameters:",
            ", ".join(
                component["Available parameters"]
            )
        )

        print(
            "Scenario candidates:",
            ", ".join(
                component["Scenario candidates"]
            )
        )

        for element in component["Elements"]:

            print(
                f"   - {element['Name']}"
            )


# =========================================================
# 8. SAVE INSPECTION REPORT
# =========================================================

def save_inspection(inspection, output_file):

    Path(output_file).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            inspection,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nInspection report saved:")
    print(output_file)


# PUBLIC API

def run_network_inspector(input_file=None, output_file=None):
    input_file = Path(input_file or INPUT_FILE).resolve()
    output_file = Path(output_file or OUTPUT_FILE).resolve()
    network_data = load_network_information(input_file)
    inspection = inspect_network(network_data, source_file=input_file)
    display_inspection(inspection)
    save_inspection(inspection, output_file)
    return inspection


def main():
    run_network_inspector()


if __name__ == "__main__":
    main()
