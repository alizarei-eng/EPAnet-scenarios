"""
EPANET Scenario Setup
Version: 2.0

Purpose:
Create manual scenarios and parameter sweep scenarios
for EPANET hydraulic network analysis.

Features:
- Manual scenario creation
- Multi-parameter Cartesian Parameter Sweep
- Automatic saving
- Resume unfinished work
- Scenario review and management
- Backup and temporary files
"""

import json
import os
import copy
import itertools
from datetime import datetime


# ============================================================
# FILE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULT_DIR = os.path.join(
    BASE_DIR,
    "network_information_result"
)

INPUT_FILE = os.path.join(
    RESULT_DIR,
    "Network_Inspection.json"
)

OUTPUT_FILE = os.path.join(
    RESULT_DIR,
    "Scenario_Definitions.json"
)

BACKUP_FILE = os.path.join(
    RESULT_DIR,
    "Scenario_Backup.json"
)

TEMP_FILE = os.path.join(
    RESULT_DIR,
    "Scenario_Temp.json"
)


# ============================================================
# GLOBAL DATA
# ============================================================

inspection_data = {}
scenarios = []
draft_scenario = None

session_created_at = None


# ============================================================
# GENERAL UTILITIES
# ============================================================

def timestamp():

    return datetime.now().isoformat(timespec="seconds")


def print_line():

    print("-" * 65)


def pause():

    input("\nPress Enter to continue...")


def load_json(path):

    with open(path, "r", encoding="utf-8") as file:

        return json.load(file)


def save_json(path, data):

    with open(path, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def read_json_value(message):

    while True:

        raw_value = input(message).strip()

        try:

            return json.loads(raw_value)

        except json.JSONDecodeError:

            print("Invalid JSON format.")
            print("Please enter a valid JSON value.")


def unique_name(name, existing_names):

    if name not in existing_names:

        return name

    counter = 2

    while True:

        new_name = f"{name}_{counter}"

        if new_name not in existing_names:

            return new_name

        counter += 1


# ============================================================
# DATA INITIALIZATION
# ============================================================

def initialize_project():

    global inspection_data
    global scenarios

    if not os.path.exists(INPUT_FILE):

        print("ERROR: Network_Inspection.json was not found.")

        return False

    try:

        inspection_data = load_json(INPUT_FILE)

    except Exception as error:

        print("Unable to read inspection file:")
        print(error)

        return False

    if os.path.exists(OUTPUT_FILE):

        try:

            saved_data = load_json(OUTPUT_FILE)

            scenarios = saved_data.get(
                "Scenarios",
                []
            )

        except Exception:

            scenarios = []

    return True


# ============================================================
# PROJECT INFORMATION
# ============================================================

def project_information():

    return {

        "Source file": INPUT_FILE,

        "Created at": session_created_at or timestamp(),

        "Last updated": timestamp(),

        "Unit system": "SI"

    }


# ============================================================
# SAVE SYSTEM
# ============================================================

def save_all():

    global scenarios

    data = {

        "Project information": project_information(),

        "Scenario count": len(scenarios),

        "Scenarios": scenarios,

        "Session": {

            "Draft": draft_scenario

        }

    }

    try:

        if os.path.exists(OUTPUT_FILE):

            save_json(
                BACKUP_FILE,
                data
            )

        save_json(
            TEMP_FILE,
            data
        )

        os.replace(
            TEMP_FILE,
            OUTPUT_FILE
        )

        print("\nAuto Save completed.")

    except Exception as error:

        print("\nERROR while saving:")
        print(error)


# ============================================================
# RESUME SYSTEM
# ============================================================

def resume_session():

    global scenarios
    global draft_scenario
    global session_created_at

    if not os.path.exists(OUTPUT_FILE):

        print("No previous session was found.")

        return False

    try:

        data = load_json(OUTPUT_FILE)

        scenarios = data.get(
            "Scenarios",
            []
        )

        session_data = data.get(
            "Session",
            {}
        )

        draft_scenario = session_data.get(
            "Draft"
        )

        session_created_at = data.get(
            "Project information",
            {}
        ).get(
            "Created at"
        )

        print("\nPrevious session loaded.")

        print(
            "Saved scenarios:",
            len(scenarios)
        )

        if draft_scenario:

            print("An unfinished draft was also recovered.")

        return True

    except Exception as error:

        print("Unable to resume session:")
        print(error)

        return False


# ============================================================
# INSPECTION DATA ACCESS
# ============================================================

def get_components():

    return inspection_data.get(
        "Components",
        {}
    )


def get_component_names():

    return list(get_components().keys())


def get_elements(component_name):

    component_data = get_components().get(
        component_name,
        {}
    )

    return component_data.get(
        "Elements",
        []
    )


def get_element_names(component_name):

    return [
        element.get("Name")
        for element in get_elements(component_name)
    ]


def get_element_data(component_name, element_name):

    for element in get_elements(component_name):

        if element.get("Name") == element_name:

            return element

    return None


def get_parameters(component_name, element_name):

    element = get_element_data(
        component_name,
        element_name
    )

    if not element:

        return {}

    return element.get(
        "Parameters",
        {}
    )


# ============================================================
# SELECTION MENUS
# ============================================================

def numbered_selection(title, options):

    if not options:

        print("No available options.")

        return None

    while True:

        print_line()

        print(title)

        print_line()

        for index, option in enumerate(options, start=1):

            print(f"{index}. {option}")

        print("\n0. Back")

        choice = input("\nEnter your choice: ").strip()

        if choice == "0":

            return None

        if choice.isdigit():

            number = int(choice)

            if 1 <= number <= len(options):

                return options[number - 1]

        print("Invalid selection. Try again.")


def select_component():

    return numbered_selection(
        "SELECT COMPONENT",
        get_component_names()
    )


def select_element(component_name):

    return numbered_selection(
        "SELECT ELEMENT",
        get_element_names(component_name)
    )


def select_parameter(component_name, element_name):

    parameters = get_parameters(
        component_name,
        element_name
    )

    return numbered_selection(
        "SELECT PARAMETER",
        list(parameters.keys())
    )


# ============================================================
# CHANGE DATA CREATION
# ============================================================

def create_change():

    print("\nCREATE A NEW PARAMETER CHANGE")

    while True:

        component = select_component()

        if component is None:

            return None

        while True:

            element = select_element(component)

            if element is None:

                break

            while True:

                parameter = select_parameter(
                    component,
                    element
                )

                if parameter is None:

                    break

                parameters = get_parameters(
                    component,
                    element
                )

                original_value = parameters.get(
                    parameter
                )

                print("\nSelected parameter:")
                print(component, "/", element, "/", parameter)

                print("\nOriginal SI Value:")

                print(
                    json.dumps(
                        original_value,
                        indent=4,
                        ensure_ascii=False
                    )
                )

                print("\nEnter the new value as JSON.")

                new_value = read_json_value(
                    "New SI Value: "
                )

                return {

                    "Component": component,

                    "Element": element,

                    "Parameter": parameter,

                    "Original SI Value": original_value,

                    "New SI Value": new_value

                }


# ============================================================
# DUPLICATE CHANGE VALIDATION
# ============================================================

def is_duplicate_change(change, change_list):

    for existing in change_list:

        if (

            existing["Component"] == change["Component"]

            and existing["Element"] == change["Element"]

            and existing["Parameter"] == change["Parameter"]

        ):

            return True

    return False


# ============================================================
# MANUAL SCENARIO
# ============================================================

def create_manual_scenario():

    global draft_scenario

    print_line()

    print("MANUAL SCENARIO CREATION")

    print_line()

    scenario_name = input(
        "Enter scenario name: "
    ).strip()

    if not scenario_name:

        print("Scenario name cannot be empty.")

        return

    existing_names = [
        item["Scenario name"]
        for item in scenarios
    ]

    scenario_name = unique_name(
        scenario_name,
        existing_names
    )

    draft_scenario = {

        "Scenario name": scenario_name,

        "Creation time": timestamp(),

        "Changes": []

    }

    save_all()

    while True:

        change = create_change()

        if change is None:

            break

        if is_duplicate_change(
            change,
            draft_scenario["Changes"]
        ):

            print("\nThis parameter has already been changed.")

            continue

        draft_scenario["Changes"].append(
            change
        )

        save_all()

        print("\nChange added successfully.")

        answer = input(
            "\nAdd another change? (y/n): "
        ).strip().lower()

        if answer != "y":

            break

    if draft_scenario["Changes"]:

        scenarios.append(
            draft_scenario
        )

        draft_scenario = None

        save_all()

        print("\nManual scenario saved successfully.")

    else:

        print("\nNo changes were added.")

        draft_scenario = None

        save_all()


# ============================================================
# PARAMETER SWEEP INPUT
# ============================================================

def collect_sweep_parameter():

    """
    Collect one parameter and all its alternative values.

    Important:
    The user enters only the sweep values.
    No unnecessary single-value prompt is used.
    """

    while True:

        component = select_component()

        if component is None:

            return None

        while True:

            element = select_element(component)

            if element is None:

                break

            while True:

                parameter = select_parameter(
                    component,
                    element
                )

                if parameter is None:

                    break

                parameters = get_parameters(
                    component,
                    element
                )

                original_value = parameters.get(
                    parameter
                )

                print("\nSelected parameter:")

                print(
                    f"{component} / {element} / {parameter}"
                )

                print("\nOriginal SI Value:")

                print(
                    json.dumps(
                        original_value,
                        indent=4,
                        ensure_ascii=False
                    )
                )

                print("\nEnter all alternative values.")

                print(
                    "Use a JSON array. Each item represents one alternative."
                )

                while True:

                    sweep_values = read_json_value(
                        "\nSweep values: "
                    )

                    if not isinstance(
                        sweep_values,
                        list
                    ):

                        print(
                            "ERROR: Input must be a JSON array."
                        )

                        continue

                    if len(sweep_values) == 0:

                        print(
                            "ERROR: At least one value is required."
                        )

                        continue

                    return {

                        "Component": component,

                        "Element": element,

                        "Parameter": parameter,

                        "Original SI Value": original_value,

                        "Sweep Values": sweep_values

                    }


# ============================================================
# PARAMETER SWEEP VALIDATION
# ============================================================

def validate_sweep_parameters(parameters):

    selected_keys = []

    for parameter in parameters:

        key = (

            parameter["Component"],

            parameter["Element"],

            parameter["Parameter"]

        )

        if key in selected_keys:

            print(
                "\nERROR: A parameter cannot be selected twice."
            )

            return False

        selected_keys.append(key)

        if not parameter["Sweep Values"]:

            print(
                "\nERROR: Empty sweep values."
            )

            return False

    return True


# ============================================================
# SCENARIO NAME GENERATION
# ============================================================

def value_to_name(value):

    text_value = str(value)

    text_value = text_value.replace(
        " ",
        ""
    )

    text_value = text_value.replace(
        ".",
        "_"
    )

    text_value = text_value.replace(
        "/",
        "_"
    )

    text_value = text_value.replace(
        "{",
        ""
    )

    text_value = text_value.replace(
        "}",
        ""
    )

    text_value = text_value.replace(
        "[",
        ""
    )

    text_value = text_value.replace(
        "]",
        ""
    )

    return text_value[:25]


def generate_scenario_name(index, parameters, combination):

    parts = []

    for parameter, value in zip(
        parameters,
        combination
    ):

        element = parameter["Element"]

        parameter_name = parameter["Parameter"]

        parts.append(
            f"{element}_{parameter_name}_{value_to_name(value)}"
        )

    name = (
        f"Sweep_{index:03d}_"
        + "_".join(parts)
    )

    return name[:150]


# ============================================================
# PARAMETER SWEEP ENGINE
# ============================================================

def create_parameter_sweep():

    global scenarios

    print_line()

    print("PARAMETER SWEEP")

    print_line()

    print(
        "\nThis tool generates every possible combination"
    )

    print(
        "of the selected parameter values."
    )

    print(
        "\nExample: 2 demand values x 5 diameter values = 10 scenarios."
    )

    sweep_parameters = []

    while True:

        print_line()

        print(
            f"Selected sweep parameters: {len(sweep_parameters)}"
        )

        if sweep_parameters:

            for index, parameter in enumerate(
                sweep_parameters,
                start=1
            ):

                print(
                    f"{index}. "
                    f"{parameter['Component']} / "
                    f"{parameter['Element']} / "
                    f"{parameter['Parameter']}"
                )

                print(
                    "   Number of values:",
                    len(parameter["Sweep Values"])
                )

        print_line()

        parameter = collect_sweep_parameter()

        if parameter is None:

            if not sweep_parameters:

                print("Sweep cancelled.")

                return

            break

        sweep_parameters.append(
            parameter
        )

        save_sweep_draft(
            sweep_parameters
        )

        answer = input(
            "\nAdd another parameter to this sweep? (y/n): "
        ).strip().lower()

        if answer != "y":

            break

    if not validate_sweep_parameters(
        sweep_parameters
    ):

        return

    # --------------------------------------------------------
    # Calculate total number of scenarios
    # --------------------------------------------------------

    value_lists = [

        parameter["Sweep Values"]

        for parameter in sweep_parameters

    ]

    total_scenarios = 1

    for values in value_lists:

        total_scenarios *= len(values)

    print_line()

    print("SWEEP SUMMARY")

    print_line()

    for parameter in sweep_parameters:

        print(
            f"{parameter['Element']} / "
            f"{parameter['Parameter']}: "
            f"{len(parameter['Sweep Values'])} values"
        )

    print(
        "\nTotal scenarios to generate:",
        total_scenarios
    )

    answer = input(
        "\nGenerate these scenarios? (y/n): "
    ).strip().lower()

    if answer != "y":

        print("Sweep cancelled.")

        return

    # --------------------------------------------------------
    # Cartesian Product
    # --------------------------------------------------------

    existing_names = {

        scenario["Scenario name"]

        for scenario in scenarios

    }

    generated_count = 0

    combinations = itertools.product(
        *value_lists
    )

    for combination in combinations:

        generated_count += 1

        changes = []

        for parameter, new_value in zip(
            sweep_parameters,
            combination
        ):

            changes.append({

                "Component": parameter["Component"],

                "Element": parameter["Element"],

                "Parameter": parameter["Parameter"],

                "Original SI Value": copy.deepcopy(
                    parameter["Original SI Value"]
                ),

                "New SI Value": copy.deepcopy(
                    new_value
                )

            })

        scenario_name = generate_scenario_name(
            generated_count,
            sweep_parameters,
            combination
        )

        scenario_name = unique_name(
            scenario_name,
            existing_names
        )

        existing_names.add(
            scenario_name
        )

        scenario = {

            "Scenario name": scenario_name,

            "Creation time": timestamp(),

            "Sweep": True,

            "Changes": changes

        }

        scenarios.append(
            scenario
        )

        # Auto-save after every generated scenario.
        save_all()

        print(
            f"Generated {generated_count}/{total_scenarios}: "
            f"{scenario_name}"
        )

    print_line()

    print("PARAMETER SWEEP COMPLETED")

    print_line()

    print(
        "Generated scenarios:",
        generated_count
    )

    print(
        "Total saved scenarios:",
        len(scenarios)
    )

    save_all()


# ============================================================
# SWEEP DRAFT SAVE
# ============================================================

def save_sweep_draft(parameters):

    global draft_scenario

    draft_scenario = {

        "Type": "Parameter Sweep",

        "Parameters": parameters,

        "Last updated": timestamp()

    }

    save_all()


# ============================================================
# VIEW SCENARIOS
# ============================================================

def view_scenarios():

    print_line()

    print("SAVED SCENARIOS")

    print_line()

    if not scenarios:

        print("No scenarios available.")

        pause()

        return

    for index, scenario in enumerate(
        scenarios,
        start=1
    ):

        print(
            f"\n{index}. {scenario['Scenario name']}"
        )

        for change in scenario.get(
            "Changes",
            []
        ):

            print(
                "   ",
                change["Component"],
                "/",
                change["Element"],
                "/",
                change["Parameter"]
            )

            print(
                "      New value:",
                json.dumps(
                    change["New SI Value"],
                    ensure_ascii=False
                )
            )

    pause()


# ============================================================
# RENAME SCENARIO
# ============================================================

def rename_scenario():

    if not scenarios:

        print("No scenarios available.")

        return

    names = [

        scenario["Scenario name"]

        for scenario in scenarios

    ]

    selected = numbered_selection(
        "SELECT SCENARIO TO RENAME",
        names
    )

    if selected is None:

        return

    new_name = input(
        "Enter new scenario name: "
    ).strip()

    if not new_name:

        print("Name cannot be empty.")

        return

    existing_names = [

        name for name in names

        if name != selected

    ]

    new_name = unique_name(
        new_name,
        existing_names
    )

    for scenario in scenarios:

        if scenario["Scenario name"] == selected:

            scenario["Scenario name"] = new_name

            break

    save_all()

    print("Scenario renamed successfully.")


# ============================================================
# DELETE CHANGE FROM SCENARIO
# ============================================================

def delete_change():

    if not scenarios:

        print("No scenarios available.")

        return

    names = [

        scenario["Scenario name"]

        for scenario in scenarios

    ]

    selected = numbered_selection(
        "SELECT SCENARIO",
        names
    )

    if selected is None:

        return

    scenario = next(

        item for item in scenarios

        if item["Scenario name"] == selected

    )

    changes = scenario.get(
        "Changes",
        []
    )

    if not changes:

        print("No changes available.")

        return

    labels = [

        f"{item['Component']} / "
        f"{item['Element']} / "
        f"{item['Parameter']}"

        for item in changes

    ]

    selected_change = numbered_selection(
        "SELECT CHANGE TO DELETE",
        labels
    )

    if selected_change is None:

        return

    index = labels.index(
        selected_change
    )

    del changes[index]

    if not changes:

        scenarios.remove(
            scenario
        )

    save_all()

    print("Change deleted successfully.")


# ============================================================
# DELETE SCENARIO
# ============================================================

def delete_scenario():

    if not scenarios:

        print("No scenarios available.")

        return

    names = [

        scenario["Scenario name"]

        for scenario in scenarios

    ]

    selected = numbered_selection(
        "SELECT SCENARIO TO DELETE",
        names
    )

    if selected is None:

        return

    answer = input(
        f"Delete '{selected}'? (y/n): "
    ).strip().lower()

    if answer != "y":

        return

    scenarios[:] = [

        item for item in scenarios

        if item["Scenario name"] != selected

    ]

    save_all()

    print("Scenario deleted successfully.")


# ============================================================
# SCENARIO MANAGEMENT MENU
# ============================================================

def scenario_management():

    while True:

        print_line()

        print("SCENARIO MANAGEMENT")

        print_line()

        print("1. View scenarios")

        print("2. Rename scenario")

        print("3. Delete a change")

        print("4. Delete scenario")

        print("0. Back")

        choice = input(
            "\nEnter choice: "
        ).strip()

        if choice == "1":

            view_scenarios()

        elif choice == "2":

            rename_scenario()

        elif choice == "3":

            delete_change()

        elif choice == "4":

            delete_scenario()

        elif choice == "0":

            break

        else:

            print("Invalid choice.")


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    while True:

        print_line()

        print("EPANET SCENARIO SETUP")

        print_line()

        print(
            "Saved scenarios:",
            len(scenarios)
        )

        print("\n1. Create Manual Scenario")

        print("2. Create Parameter Sweep")

        print("3. Scenario Management")

        print("4. Save Project")

        print("5. Resume Previous Session")

        print("0. Exit")

        choice = input(
            "\nEnter your choice: "
        ).strip()

        if choice == "1":

            create_manual_scenario()

        elif choice == "2":

            create_parameter_sweep()

        elif choice == "3":

            scenario_management()

        elif choice == "4":

            save_all()

        elif choice == "5":

            resume_session()

        elif choice == "0":

            save_all()

            print("\nProject saved. Goodbye.")

            break

        else:

            print("Invalid choice. Try again.")


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():

    global session_created_at
    global draft_scenario

    print_line()

    print("EPANET SCENARIO SETUP")

    print_line()

    if not initialize_project():

        return

    session_created_at = timestamp()

    print("\nNetwork inspection file loaded.")

    print(
        "Available components:",
        len(get_component_names())
    )

    if os.path.exists(OUTPUT_FILE):

        answer = input(
            "\nPrevious scenario file found. Resume? (y/n): "
        ).strip().lower()

        if answer == "y":

            resume_session()

        else:

            draft_scenario = None

    main_menu()


if __name__ == "__main__":

    main()