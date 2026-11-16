# EPANET Scenarios — Python-based Hydraulic Scenario Analysis

A Python application for preparing and analyzing EPANET water-distribution network scenarios. The project uses **WNTR** to read EPANET `.inp` models and prepare/run hydraulic simulations, then organizes, compares, validates, and reports scenario results.

The current user interface is a **terminal-based CLI**. The intended entry point is `main.py`.

> **Project status:** This repository is under active development. A successful program run or generated report does not, by itself, establish that a model is hydraulically valid or that a scenario is suitable for design or operation. Verify important results independently before using them for engineering decisions.

## Contents

- [Overview](#overview)
- [Current capabilities](#current-capabilities)
- [Project structure](#project-structure)
- [Requirements and installation](#requirements-and-installation)
- [Getting started](#getting-started)
- [Main menu](#main-menu)
- [Recommended analysis workflow](#recommended-analysis-workflow)
- [Scenario creation](#scenario-creation)
- [Input and output files](#input-and-output-files)
- [Units and hydraulic interpretation](#units-and-hydraulic-interpretation)
- [Current limitations](#current-limitations-and-validation-notes)
- [Troubleshooting](#troubleshooting)
- [Development roadmap](#development-roadmap)
- [Contributing](#contributing)

---

## Overview

The application is organized as a set of focused Python modules coordinated by a central terminal menu. The main processing sequence is:

1. Read an EPANET INP model.
2. Export network information in original and SI-oriented forms.
3. Inspect network components and available parameters.
4. Define manual scenarios or parameter sweeps.
5. Prepare a separate hydraulic model for each scenario.
6. Run hydraulic simulations.
7. Collect and compare scenario results.
8. Generate selected JSON reports.
9. Validate the comparison output structure and numerical data.

The modules remain separate so that network reading, scenario setup, simulation, comparison, reporting, and validation can be developed independently.

## Current capabilities

### 1. Network Reader

Reads an EPANET `.inp` file through WNTR and exports network information in two representations:

- **Original:** values in the model's original EPANET units.
- **SI:** values converted to SI units where the relevant conversion is supported by the reader.

The reader generates JSON and Excel outputs for both representations. It also reads hydraulic settings such as the flow unit and selected headloss formula.

### 2. Network Inspector

Organizes information for the main EPANET component groups:

- Junctions
- Reservoirs
- Tanks
- Pipes
- Pumps
- Valves

It produces an inspection JSON containing component inventories, element information, available parameters, and parameters that can be considered during scenario setup.

### 3. Scenario Setup

Supports two main scenario creation approaches:

- **Manual Scenario:** create a scenario and define changes to selected network elements and parameters.
- **Parameter Sweep:** provide multiple values for one or more input parameters and generate combinations of those values.

Scenario management includes reviewing scenarios, renaming or deleting scenarios, saving work, creating backups, and resuming a previously saved scenario session.

### 4. Model Manager and Hydraulic Simulation

The Model Manager prepares scenario-specific network models from the base INP model and applies the scenario definitions. The Simulation Engine runs the prepared scenarios and records successful and failed executions.

### 5. Results Manager

Collects simulation outputs into a structured JSON file. The result structure includes project information, simulation summary, scenario status, time steps, available result variables, node results, link results, and other available results.

### 6. Comparison Engine

Builds comparison results from the simulation outputs and scenario definitions. Current analysis areas include:

- Scenario comparisons against the reference scenario
- Network performance statistics for available variables
- Pearson, Spearman, and Kendall correlation analysis
- Scenario-level sensitivity analysis
- Scenario ranking using implemented ranking metrics

### 7. Interactive Report Generator

The report generator is a guided terminal workflow. Its report categories are:

1. Scenario Comparison
2. Element Analysis
3. Network Performance
4. Sensitivity Analysis
5. Correlation Analysis
6. Scenario Ranking

Depending on the selected report and available data, the generator can provide statistical summaries, element-level information, and time-series information. Reports are saved as JSON; the output workflow supports aggregate and separate report files.

### 8. Comparison Validation

Checks the comparison JSON structure, expected sections, scenario information, and numerical values. A text validation report is written to the results directory.

---

## Project structure

The main repository files are:

```text
EPAnet-scenarios/
|
|-- main.py
|-- project_paths.py
|-- network_reader.py
|-- network_inspector.py
|-- scenario_setup.py
|-- results_manager.py
|-- comparison_engine.py
|-- report_generator.py
|-- validate_comparison.py
|-- inspect_comparison_json.py
|
|-- simulation/
|   |-- __init__.py
|   |-- model_manager.py
|   |-- simulation_engine.py
|
|-- inputs/                         # Recommended location for INP files
|
|-- network_information_result/     # Generated analysis data and reports
```

The results directory is created/used by the application. Its generated files can include:

```text
network_information_result/
|-- Network_Original.json
|-- Network_Original.xlsx
|-- Network_SI.json
|-- Network_SI.xlsx
|-- Network_Inspection.json
|-- Scenario_Definitions.json
|-- Scenario_Backup.json
|-- Scenario_Temp.json
|-- Simulation_Results.json
|-- Comparison_Results.json
|-- Comparison_JSON_Inspection.txt
|-- Comparison_Validation_Report.txt
|-- Reports/
    |-- Reports.json
    |-- ...separate report JSON files, depending on selections
```

### Module responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Central CLI menu and coordination of workflow stages |
| `project_paths.py` | Project paths, input-file resolution, and output-directory setup |
| `network_reader.py` | Read INP and export original/SI network information |
| `network_inspector.py` | Inspect network components and parameters |
| `scenario_setup.py` | Create and manage scenarios |
| `simulation/model_manager.py` | Prepare independent models for scenarios |
| `simulation/simulation_engine.py` | Execute hydraulic simulations |
| `results_manager.py` | Collect and save simulation results |
| `comparison_engine.py` | Compare scenarios and calculate implemented analyses |
| `report_generator.py` | Generate interactive JSON reports |
| `validate_comparison.py` | Validate comparison output |
| `inspect_comparison_json.py` | Inspect the comparison JSON structure |

### Path handling

Project paths are centralized in `project_paths.py`. The project root is based on the location of that file:

```python
Path(__file__).resolve().parent
```

This avoids relying on a particular Windows drive letter or the terminal's current working directory for project output paths. The recommended location for input INP files is the `inputs/` folder. If an input file is not found in the project locations, provide its full path when prompted.

---

## Requirements and installation

### Requirements

- Python (use a currently supported Python version compatible with the installed WNTR release).
- An EPANET `.inp` model file.
- WNTR and the data/export libraries used by the project.

### Install dependencies

From the repository directory:

```bash
python -m pip install --upgrade pip
python -m pip install wntr pandas numpy openpyxl
```

If your environment reports a dependency or Python-version conflict, record the exact Python version and complete error message before changing package versions.

### Optional: create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install wntr pandas numpy openpyxl
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install wntr pandas numpy openpyxl
```

---

## Getting started

### Clone the repository

```bash
git clone https://github.com/alizarei-eng/EPAnet-scenarios.git
cd EPAnet-scenarios
```

To update the local main branch:

```bash
git checkout main
git pull origin main
```

### Add an EPANET model

Place the model file in the recommended `inputs/` directory, for example:

```text
inputs/flow.inp
```

You can also enter an absolute path when the program asks for the input file.

### Run the application

```bash
python main.py
```

At startup, enter the INP filename (for example, `flow.inp`). The path resolver checks the project locations and asks again if it cannot resolve the file. Enter `Q` to cancel input selection.

---

## Main menu

The current central menu in `main.py` provides these actions:

| Menu option | Action |
|---:|---|
| 1 | Network Information |
| 2 | Network Inspection |
| 3 | Scenario Setup |
| 4 | Run Hydraulic Simulations |
| 5 | Compare Scenarios |
| 6 | Report Generator |
| 7 | Validate Results |
| 8 | Run Complete Workflow |
| 9 | Change INP File |
| 10 | Show Project Paths |
| 0 | Exit |

Individual stages can be run separately. After an operation, the CLI returns to the main menu. The complete workflow runs the stages in sequence and therefore requires the prerequisite data for each stage to be available.

## Recommended analysis workflow

For a new network or a changed INP model, use this sequence:

```text
EPANET INP model
      |
      v
Network Reader
      |
      +--> Network_Original.json / .xlsx
      |
      +--> Network_SI.json / .xlsx
      |
      v
Network Inspector
      |
      v
Network_Inspection.json
      |
      v
Scenario Setup
      |
      v
Scenario_Definitions.json
      |
      v
Model Manager
      |
      v
Simulation Engine
      |
      v
Results Manager
      |
      v
Simulation_Results.json
      |
      v
Comparison Engine
      |
      v
Comparison_Results.json
      |
      +--> Report Generator
      |
      +--> Comparison Validation
```

For the first run, executing stages individually is recommended. Inspect each generated file before proceeding to the next stage. Once the process is established for the model, the **Run Complete Workflow** option can be used.

If a stage reports that a prerequisite file is missing, run the stage responsible for generating that file first.

## Scenario creation

### Manual scenarios

Use Manual Scenario to define a named scenario and apply selected changes to network elements. Keep a clear reference scenario and use distinct names for modified scenarios so that comparison results remain interpretable.

### Parameter Sweep

Parameter Sweep generates combinations from the values supplied for each selected input parameter.

Example:

| Parameter | Values |
|---|---|
| Demand | 250, 300 |
| Pipe Diameter | 8, 10, 12, 14, 16 |

The number of combinations is:

```text
2 x 5 = 10 scenarios
```

Each combination is treated as a separate scenario for model preparation and simulation.

**Engineering note:** A generated parameter combination is not automatically a feasible design. Check input ranges against physical constraints, equipment limits, pressure requirements, velocity criteria, and actual operating conditions before interpreting the results.

---

## Input and output files

### Input

| File | Purpose |
|---|---|
| EPANET `.inp` | Base network model used for network reading and scenario model preparation |

### Main generated files

| File | Purpose |
|---|---|
| `Network_Original.json` | Network data in original model units |
| `Network_SI.json` | Network data converted to SI where supported |
| `Network_Original.xlsx` | Excel export of original network information |
| `Network_SI.xlsx` | Excel export of SI network information |
| `Network_Inspection.json` | Network component and parameter inspection |
| `Scenario_Definitions.json` | Scenario definitions |
| `Scenario_Backup.json` | Scenario backup |
| `Scenario_Temp.json` | Temporary scenario-session data |
| `Simulation_Results.json` | Collected simulation results |
| `Comparison_Results.json` | Scenario comparison and implemented analyses |
| `Comparison_JSON_Inspection.txt` | Comparison JSON inspection output |
| `Comparison_Validation_Report.txt` | Validation report |
| `Reports/Reports.json` | Aggregate report, when selected |
| `Reports/` | Separate report JSON files, depending on report selections |

Generated results may be overwritten by later runs. Archive or copy the results directory before rerunning an analysis that must be retained.

## Units and hydraulic interpretation

EPANET models can use different flow-unit systems. Always check the model's hydraulic options and the unit metadata associated with exported data.

1. Do not assume that values in the Original export are SI values.
2. Confirm that compared scenarios use consistent units and compatible model assumptions.
3. A unit label does not prove that a conversion has been correctly applied; check the parameter's physical definition and conversion.
4. Report values with their units when using them in engineering calculations.
5. The headloss formula selected in the INP file is a model setting. It is not itself a computed headloss result for every link.

---

## Current limitations and validation notes

This repository is actively evolving. The following distinctions are important when interpreting its output:

- The validation module checks defined data-structure and numerical consistency conditions. It is not a substitute for independent hydraulic verification.
- Correlation does not establish causation. Scenario-level correlation and sensitivity calculations depend on the number, range, independence, and quality of the scenarios supplied.
- A numerical scenario ranking is not necessarily an engineering optimum. A meaningful engineering ranking needs explicit objective directions, target ranges, constraints, and (where appropriate) criterion weights.
- Time-series analysis requires simulation results containing enough valid time steps.
- Engineering acceptance limits for pressure, velocity, headloss, and other quantities must be defined from applicable standards, project specifications, and operating requirements.
- The project reads the selected headloss formula from the model. A complete, independently checked headloss result pipeline across result collection, comparison, sensitivity analysis, ranking, and reporting remains a development item. Do not assume that headloss is fully implemented merely because the model's headloss formula is present in the network metadata.

Always compare critical results against EPANET or another trusted hydraulic calculation and review model assumptions, boundary conditions, units, and warnings.

## Troubleshooting

### The INP file cannot be found

- Place the file in the repository's `inputs/` folder, or in the project root.
- Check the spelling and extension.
- Alternatively, enter the full absolute path.
- Avoid relying on a path that exists only on another computer.

### A stage reports a missing JSON file

Run the prerequisite stage first. For example, Network Inspection requires the Network Reader output, and simulation requires network exports and scenario definitions.

### A Python module cannot be imported

- Confirm that the terminal is in the repository directory.
- Activate the intended virtual environment.
- Install the required dependencies in that same environment.
- Run the application using `python main.py` from the project directory.

### A simulation fails for one or more scenarios

Review the execution error printed for each scenario. Check the INP model, element identifiers, scenario parameter names and values, pump curves, control rules, units, and hydraulic feasibility. A failed scenario should not be interpreted as a successful result.

### Results appear inconsistent

Check that the correct INP file was selected, that the network exports and scenario definitions belong to that model, that no stale output files are being reused, and that units and reference-scenario selection are consistent.

---

## Development roadmap

The longer-term direction is to evolve the repository from a collection of analysis scripts into a more integrated engineering environment.

Potential development areas include:

- Stronger workflow orchestration and project/run history
- Expanded hydraulic diagnostics and data-quality checks
- Complete headloss calculation, storage, comparison, and reporting
- Network visualization
- Improved time-series exploration
- More advanced scenario management
- Sensitivity visualization and multi-criteria ranking
- Batch and parallel simulation
- Calibration and optimization workflows
- Uncertainty and what-if analysis
- Engineering recommendations based on explicitly defined criteria

These items are roadmap directions, not claims that every feature is already available in the current code.

## Contributing

When changing the project:

1. Keep modules focused on their own responsibilities.
2. Use centralized project paths rather than machine-specific absolute paths.
3. Avoid running a full workflow as a side effect of importing a module.
4. Preserve existing scenario and result formats unless a deliberate migration is included.
5. Add validation for new result variables and report sections.
6. Test with a known INP model and compare important hydraulic outputs against a trusted reference.
7. Document new assumptions, units, limitations, and dependencies.

For bugs or feature requests, include the Python version, package versions, selected INP model characteristics, the exact command/menu stage, and the complete error message. Do not include credentials or sensitive project data in public issue reports.

---

## License

No license information is specified in this README. Unless a license file is added to the repository, do not assume that the source code is released under an open-source license.
