"""
EPANET Python Analysis System
Central terminal interface. Run: python main.py
"""
import json
import traceback
from pathlib import Path

from project_paths import PATHS, ask_input_file, ensure_project_directories

CURRENT_INP_FILE = None


def section(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def require_file(path, description):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{description} was not found: {path}")
    return path


def run_network_reader_stage():
    import network_reader
    section("NETWORK INFORMATION")
    result = network_reader.run_network_reader(CURRENT_INP_FILE, PATHS.results_dir)
    print("\n[OK] Network information generated.")
    return result


def run_network_inspection_stage():
    import network_inspector
    section("NETWORK INSPECTION")
    return network_inspector.run_network_inspector(PATHS.network_si, PATHS.network_inspection)


def run_scenario_stage():
    import scenario_setup
    section("SCENARIO SETUP")
    require_file(PATHS.network_inspection, "Network inspection file")
    scenario_setup.run_scenario_setup(
        inspection_file=PATHS.network_inspection,
        scenario_file=PATHS.scenario_definitions,
        backup_file=PATHS.scenario_backup,
        temp_file=PATHS.scenario_temp
    )


def run_simulation_stage():
    from simulation.model_manager import ModelManager
    from simulation.simulation_engine import SimulationEngine
    from results_manager import ResultsManager

    section("HYDRAULIC SIMULATION")
    require_file(CURRENT_INP_FILE, "EPANET INP file")
    for path, label in (
        (PATHS.network_original, "Original network JSON"),
        (PATHS.network_si, "SI network JSON"),
        (PATHS.scenario_definitions, "Scenario definitions")
    ):
        require_file(path, label)

    with open(PATHS.scenario_definitions, "r", encoding="utf-8") as f:
        scenario_data = json.load(f)
    with open(PATHS.network_si, "r", encoding="utf-8") as f:
        network_si_data = json.load(f)

    scenario_names = [
        item.get("Scenario name")
        for item in scenario_data.get("Scenarios", [])
        if isinstance(item, dict) and item.get("Scenario name")
    ]
    if not scenario_names:
        raise RuntimeError("No scenarios are defined. Create scenarios first.")

    model_manager = ModelManager(
        inp_file=CURRENT_INP_FILE,
        network_original_json=PATHS.network_original,
        network_si_json=PATHS.network_si,
        scenario_json=PATHS.scenario_definitions
    )
    model_manager.show_network_inventory()
    model_manager.prepare_all_scenarios()
    model_manager.show_prepared_scenarios()

    engine = SimulationEngine()
    simulation_output = engine.run_all(model_manager=model_manager, scenario_names=scenario_names)

    manager = ResultsManager(output_file=PATHS.simulation_results)
    manager.collect_all(
        simulation_output=simulation_output,
        scenario_definitions=scenario_data,
        network_si_data=network_si_data
    )
    manager.show_summary()
    manager.save_json()
    print(f"\n[OK] Results saved: {PATHS.simulation_results}")
    return manager


def run_comparison_stage():
    from comparison_engine import ComparisonEngine
    section("SCENARIO COMPARISON")
    require_file(PATHS.simulation_results, "Simulation results")
    require_file(PATHS.scenario_definitions, "Scenario definitions")
    engine = ComparisonEngine(
        results_file=PATHS.simulation_results,
        scenario_file=PATHS.scenario_definitions,
        output_file=PATHS.comparison_results
    )
    engine.run()
    engine.show_summary()
    engine.save_json()
    return engine


def run_report_stage():
    import report_generator
    section("INTERACTIVE REPORT GENERATOR")
    for path, label in (
        (PATHS.simulation_results, "Simulation results"),
        (PATHS.comparison_results, "Comparison results"),
        (PATHS.scenario_definitions, "Scenario definitions")
    ):
        require_file(path, label)
    report_generator.run_report_generator(
        simulation_file=PATHS.simulation_results,
        comparison_file=PATHS.comparison_results,
        scenario_file=PATHS.scenario_definitions,
        output_directory=PATHS.reports_dir
    )


def run_validation_stage():
    import validate_comparison
    section("RESULT VALIDATION")
    require_file(PATHS.comparison_results, "Comparison results")
    require_file(PATHS.scenario_definitions, "Scenario definitions")
    validate_comparison.run_validation(
        comparison_file=PATHS.comparison_results,
        scenario_file=PATHS.scenario_definitions,
        report_file=PATHS.validation_report
    )


def run_complete_workflow():
    run_network_reader_stage()
    run_network_inspection_stage()
    run_scenario_stage()
    run_simulation_stage()
    run_comparison_stage()
    run_report_stage()
    run_validation_stage()


def execute_action(action):
    try:
        action()
    except KeyboardInterrupt:
        print("\n[INFO] Operation interrupted by user.")
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        traceback.print_exc()
    input("\nPress Enter to return to the main menu...")


def main_menu():
    actions = {
        "1": ("Network Information", run_network_reader_stage),
        "2": ("Network Inspection", run_network_inspection_stage),
        "3": ("Scenario Setup", run_scenario_stage),
        "4": ("Run Hydraulic Simulations", run_simulation_stage),
        "5": ("Compare Scenarios", run_comparison_stage),
        "6": ("Report Generator", run_report_stage),
        "7": ("Validate Results", run_validation_stage),
        "8": ("Run Complete Workflow", run_complete_workflow),
    }
    while True:
        section("EPANET PYTHON ANALYSIS SYSTEM")
        print(f"Project : {PATHS.project_dir}")
        print(f"INP file: {CURRENT_INP_FILE}")
        print("\nMAIN MENU")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        print("9. Change INP File")
        print("10. Show Project Paths")
        print("0. Exit")
        choice = input("\nSelect an operation: ").strip()
        if choice == "0":
            print("\nExiting.")
            break
        if choice == "9":
            global CURRENT_INP_FILE
            try:
                CURRENT_INP_FILE = ask_input_file()
            except SystemExit:
                pass
            continue
        if choice == "10":
            from project_paths import show_project_paths
            show_project_paths()
            input("\nPress Enter to continue...")
            continue
        if choice in actions:
            execute_action(actions[choice][1])
        else:
            print("Invalid choice. Please try again.")


def main():
    global CURRENT_INP_FILE
    ensure_project_directories()
    section("EPANET PYTHON ANALYSIS SYSTEM")
    print("Choose the EPANET network file.")
    CURRENT_INP_FILE = ask_input_file()
    main_menu()


if __name__ == "__main__":
    main()
