"""Centralized paths for the EPANET project; independent of terminal CWD."""
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_DIR / "inputs"
RESULTS_DIR = PROJECT_DIR / "network_information_result"
REPORTS_DIR = RESULTS_DIR / "Reports"
LOGS_DIR = RESULTS_DIR / "Logs"

@dataclass(frozen=True)
class ProjectPaths:
    project_dir: Path = PROJECT_DIR
    input_dir: Path = INPUT_DIR
    results_dir: Path = RESULTS_DIR
    network_original: Path = RESULTS_DIR / "Network_Original.json"
    network_si: Path = RESULTS_DIR / "Network_SI.json"
    network_inspection: Path = RESULTS_DIR / "Network_Inspection.json"
    scenario_definitions: Path = RESULTS_DIR / "Scenario_Definitions.json"
    scenario_backup: Path = RESULTS_DIR / "Scenario_Backup.json"
    scenario_temp: Path = RESULTS_DIR / "Scenario_Temp.json"
    simulation_results: Path = RESULTS_DIR / "Simulation_Results.json"
    comparison_results: Path = RESULTS_DIR / "Comparison_Results.json"
    inspection_report: Path = RESULTS_DIR / "Comparison_JSON_Inspection.txt"
    validation_report: Path = RESULTS_DIR / "Comparison_Validation_Report.txt"
    reports_dir: Path = REPORTS_DIR
    logs_dir: Path = LOGS_DIR

PATHS = ProjectPaths()

def ensure_project_directories():
    for folder in (RESULTS_DIR, REPORTS_DIR, LOGS_DIR):
        folder.mkdir(parents=True, exist_ok=True)

def resolve_input_file(user_input, extensions=(".inp",)):
    raw = str(user_input).strip().strip('"').strip("'")
    if not raw:
        raise ValueError("Input file name cannot be empty.")
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Input file not found: {resolved}")
        if extensions and resolved.suffix.lower() not in extensions:
            raise ValueError(f"Unsupported extension: {resolved.suffix}")
        return resolved
    project_candidate = (PROJECT_DIR / candidate).resolve()
    if project_candidate.is_file():
        if extensions and project_candidate.suffix.lower() not in extensions:
            raise ValueError(f"Unsupported extension: {project_candidate.suffix}")
        return project_candidate
    matches = []
    for folder in (PROJECT_DIR, INPUT_DIR):
        path = folder / candidate.name
        if path.is_file() and (not extensions or path.suffix.lower() in extensions):
            resolved = path.resolve()
            if resolved not in matches:
                matches.append(resolved)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print("\nMultiple matching files:")
        for i, path in enumerate(matches, 1):
            print(f"{i}. {path}")
        while True:
            choice = input("Choose file number (0 to cancel): ").strip()
            if choice == "0":
                raise RuntimeError("File selection cancelled.")
            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                return matches[int(choice) - 1]
            print("Invalid selection.")
    raise FileNotFoundError(
        f"'{raw}' not found. Checked project folder and {INPUT_DIR}. "
        "Enter an absolute path or place the file in inputs/."
    )

def ask_input_file(prompt="Enter EPANET input file name (.inp): "):
    while True:
        value = input(prompt).strip()
        if value.lower() in {"q", "quit", "exit"}:
            raise SystemExit("Input selection cancelled.")
        try:
            selected = resolve_input_file(value, extensions=(".inp",))
            print(f"\n[OK] Selected: {selected}")
            return selected
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"\n[ERROR] {exc}\nTry again, or enter Q to exit.")

def show_project_paths():
    print("\nPROJECT PATHS")
    for label, path in (
        ("Project", PROJECT_DIR), ("Inputs", INPUT_DIR),
        ("Results", RESULTS_DIR), ("Reports", REPORTS_DIR),
        ("Logs", LOGS_DIR)
    ):
        print(f"{label:10}: {path}")

ensure_project_directories()

if __name__ == "__main__":
    show_project_paths()
    try:
        print("Resolved:", ask_input_file())
    except SystemExit:
        print("Cancelled.")
