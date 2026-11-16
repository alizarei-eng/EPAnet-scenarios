
import json
import sys
import subprocess
import traceback
from pathlib import Path

from simulation.model_manager import ModelManager
from simulation.simulation_engine import SimulationEngine
from results_manager import ResultsManager
from comparison_engine import ComparisonEngine
from inspect_comparison_json import inspect_comparison_json


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

RESULTS_DIR = PROJECT_DIR / "network_information_result"

INP_FILE = PROJECT_DIR / "flow.inp"

NETWORK_ORIGINAL_JSON = RESULTS_DIR / "Network_Original.json"
NETWORK_SI_JSON = RESULTS_DIR / "Network_SI.json"
SCENARIO_JSON = RESULTS_DIR / "Scenario_Definitions.json"

SIMULATION_RESULTS_JSON = RESULTS_DIR / "Simulation_Results.json"
COMPARISON_RESULTS_JSON = RESULTS_DIR / "Comparison_Results.json"

INSPECTION_REPORT_FILE = RESULTS_DIR / "Comparison_JSON_Inspection.txt"

REPORT_GENERATOR_FILE = PROJECT_DIR / "report_generator.py"


# ============================================================
# 2. CHECK REQUIRED FILES
# ============================================================

def validate_input_files():

    print("\n" + "=" * 65)
    print("CHECKING PROJECT FILES")
    print("=" * 65)

    required_files = {
        "EPANET INP file": INP_FILE,
        "Original Network JSON": NETWORK_ORIGINAL_JSON,
        "SI Network JSON": NETWORK_SI_JSON,
        "Scenario Definitions JSON": SCENARIO_JSON,
    }

    all_files_exist = True

    for file_description, file_path in required_files.items():

        if file_path.is_file():
            print(f"[OK]      {file_description}")
            print(f"          {file_path}")

        else:
            print(f"[MISSING] {file_description}")
            print(f"          {file_path}")
            all_files_exist = False

    print("=" * 65)

    if not all_files_exist:
        raise FileNotFoundError(
            "One or more required input files are missing. "
            "Check the paths printed above."
        )

    if not REPORT_GENERATOR_FILE.is_file():
        print(
            "[WARNING] report_generator.py was not found. "
            "The dashboard cannot be launched."
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3. LOAD PROJECT JSON FILES
# ============================================================

def load_json_file(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_project_data():

    print("\n" + "=" * 65)
    print("LOADING PROJECT DATA")
    print("=" * 65)

    network_original_data = load_json_file(
        NETWORK_ORIGINAL_JSON
    )

    network_si_data = load_json_file(
        NETWORK_SI_JSON
    )

    scenario_data = load_json_file(
        SCENARIO_JSON
    )

    print("[OK] Original network data loaded.")
    print("[OK] SI network data loaded.")
    print("[OK] Scenario definitions loaded.")

    return (
        network_original_data,
        network_si_data,
        scenario_data
    )


# ============================================================
# 4. PREPARE SCENARIO MODELS
# ============================================================


def prepare_models(scenario_data):

    print("\n" + "=" * 65)
    print("PREPARING SCENARIO MODELS")
    print("=" * 65)

    model_manager = ModelManager(
        inp_file=str(INP_FILE),
        network_original_json=str(NETWORK_ORIGINAL_JSON),
        network_si_json=str(NETWORK_SI_JSON),
        scenario_json=str(SCENARIO_JSON)
    )

    model_manager.show_network_inventory()

    model_manager.prepare_all_scenarios()

    model_manager.show_prepared_scenarios()

    # Extract scenario names from Scenario_Definitions.json
    scenarios = scenario_data.get("Scenarios", [])

    scenario_names = [
        scenario["Scenario name"]
        for scenario in scenarios
        if "Scenario name" in scenario
    ]

    if not scenario_names:
        raise RuntimeError(
            "No scenario names found in Scenario_Definitions.json"
        )

    print(f"\nDefined scenarios: {len(scenario_names)}")

    return model_manager, scenario_names


# ============================================================
# 5. RUN SIMULATIONS
# ============================================================

def run_simulations(model_manager, scenario_names):

    print("\n" + "=" * 65)
    print("RUNNING HYDRAULIC SIMULATIONS")
    print("=" * 65)

    simulation_engine = SimulationEngine()

    simulation_output = simulation_engine.run_all(
        model_manager=model_manager,
        scenario_names=scenario_names
    )

    print("\n[OK] Simulation stage completed.")

    return simulation_output


# ============================================================
# 6. COLLECT SIMULATION RESULTS
# ============================================================

def collect_simulation_results(
    simulation_output,
    scenario_data,
    network_si_data
):

    print("\n" + "=" * 65)
    print("COLLECTING SIMULATION RESULTS")
    print("=" * 65)

    results_manager = ResultsManager(
        output_file=str(SIMULATION_RESULTS_JSON)
    )

    results_manager.collect_all(
        simulation_output=simulation_output,
        scenario_definitions=scenario_data,
        network_si_data=network_si_data
    )

    results_manager.show_summary()

    results_manager.save_json()

    print(
        f"\n[OK] Simulation results saved:\n"
        f"{SIMULATION_RESULTS_JSON}"
    )

    return results_manager


# ============================================================
# 7. COMPARE SCENARIOS
# ============================================================

def compare_scenarios():

    print("\n" + "=" * 65)
    print("COMPARING SCENARIOS")
    print("=" * 65)

    comparison_engine = ComparisonEngine(
        results_file=str(SIMULATION_RESULTS_JSON),
        scenario_file=str(SCENARIO_JSON),
        output_file=str(COMPARISON_RESULTS_JSON)
    )

    comparison_engine.run()

    comparison_engine.show_summary()

    comparison_engine.save_json()

    print(
        f"\n[OK] Comparison results saved:\n"
        f"{COMPARISON_RESULTS_JSON}"
    )

    return comparison_engine


# ============================================================
# 8. INSPECT COMPARISON JSON
# ============================================================

def inspect_comparison_results():

    print("\n" + "=" * 65)
    print("INSPECTING COMPARISON JSON")
    print("=" * 65)

    inspect_comparison_json(
        json_file=COMPARISON_RESULTS_JSON,
        report_file=INSPECTION_REPORT_FILE
    )

    print(
        f"\n[OK] Inspection report saved:\n"
        f"{INSPECTION_REPORT_FILE}"
    )


# ============================================================
# 9. LAUNCH STREAMLIT DASHBOARD
# ============================================================

def launch_dashboard():

    print("\n" + "=" * 65)
    print("LAUNCHING DASHBOARD")
    print("=" * 65)

    if not REPORT_GENERATOR_FILE.is_file():

        print(
            "[WARNING] report_generator.py not found. "
            "Dashboard was not launched."
        )

        return

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(REPORT_GENERATOR_FILE),
        "--",
        str(COMPARISON_RESULTS_JSON)
    ]

    try:

        subprocess.Popen(
            command,
            cwd=str(PROJECT_DIR)
        )

        print("[OK] Streamlit dashboard process started.")

    except OSError as error:

        print("[ERROR] Could not launch dashboard.")
        print(error)


# ============================================================
# 10. MAIN PIPELINE
# ============================================================

def main():

    print("\n")
    print("#" * 65)
    print("EPANET PYTHON ANALYSIS SYSTEM")
    print("#" * 65)

    print(f"\nProject directory:\n{PROJECT_DIR}")

    try:

        # Step 1: Validate files
        validate_input_files()

        # Step 2: Load JSON data
        (
            network_original_data,
            network_si_data,
            scenario_data
        ) = load_project_data()

        # Step 3: Prepare models
        model_manager, scenario_names = prepare_models(
            scenario_data
        )

        # Step 4: Run simulations
        simulation_output = run_simulations(
            model_manager,
            scenario_names
        )

        # Step 5: Collect results
        collect_simulation_results(
            simulation_output=simulation_output,
            scenario_data=scenario_data,
            network_si_data=network_si_data
        )

        # Step 6: Compare scenarios
        compare_scenarios()

        # Step 7: Inspect comparison JSON
        inspect_comparison_results()

        # Step 8: Launch dashboard
        launch_dashboard()

        print("\n" + "#" * 65)
        print("PROJECT EXECUTION COMPLETED")
        print("#" * 65)

    except Exception as error:

        print("\n" + "!" * 65)
        print("PROJECT EXECUTION FAILED")
        print("!" * 65)

        print(f"\nError: {error}")

        print("\nDetailed traceback:")
        traceback.print_exc()


# ============================================================
# 11. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
