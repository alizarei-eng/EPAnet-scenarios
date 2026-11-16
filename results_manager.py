
"""
Results Manager
===============

Collects and stores all available WNTR simulation results.

Main responsibilities:
1. Collect node results.
2. Collect link results.
3. Preserve all available time steps.
4. Preserve DataFrame indexes, columns and values.
5. Store scenario definitions.
6. Store network unit information.
7. Record successful and failed simulations.
8. Export results into one JSON file.

The module does not perform hydraulic simulation.
"""


import json
import math

from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import wntr


class ResultsManagerError(Exception):
    """Custom exception for Results Manager."""
    pass


class ResultsManager:

    # ==========================================
    # 1. INITIALIZATION
    # ==========================================

    def __init__(self, output_file):

        self.output_file = Path(output_file)

        self.results_data = {}

    # ==========================================
    # 2. JSON SAFE CONVERSION
    # ==========================================

    def to_json_safe(self, value):
        """
        Convert Python, NumPy and Pandas values
        into JSON-compatible values.
        """

        if value is None or value is pd.NA or value is pd.NaT:
            return None

        if isinstance(value, dict):

            return {
                str(key): self.to_json_safe(val)
                for key, val in value.items()
            }

        if isinstance(value, (list, tuple)):

            return [
                self.to_json_safe(item)
                for item in value
            ]

        if isinstance(value, np.ndarray):

            return self.to_json_safe(
                value.tolist()
            )

        if isinstance(value, np.generic):

            return self.to_json_safe(
                value.item()
            )

        if isinstance(value, pd.Timestamp):

            return value.isoformat()

        if isinstance(value, pd.Timedelta):

            return value.total_seconds()

        if isinstance(value, datetime):

            return value.isoformat()

        if isinstance(value, float):

            if not math.isfinite(value):
                return None

            return value

        if isinstance(value, (str, int, bool)):

            return value

        if isinstance(value, Path):

            return str(value)

        return str(value)

    # ==========================================
    # 3. DATAFRAME SERIALIZATION
    # ==========================================

    def serialize_dataframe(self, dataframe):
        """
        Preserve all DataFrame rows, columns and values.

        Format:
        - Index
        - Columns
        - Data
        - Dtypes
        """

        if not isinstance(dataframe, pd.DataFrame):

            raise ResultsManagerError(
                "Expected a Pandas DataFrame."
            )

        column_dtypes = [
            str(dtype)
            for dtype in dataframe.dtypes
        ]

        return {

            "Format": "split",

            "Rows": len(dataframe.index),

            "Columns_Count": len(dataframe.columns),

            "Index": self.to_json_safe(
                dataframe.index.tolist()
            ),

            "Columns": self.to_json_safe(
                dataframe.columns.tolist()
            ),

            "Dtypes": column_dtypes,

            "Data": self.to_json_safe(
                dataframe.to_numpy(dtype=object).tolist()
            )
        }

    # ==========================================
    # 4. EXTRACT RESULT GROUP
    # ==========================================

    def extract_result_group(self, result_group):
        """
        Extract all DataFrames from a WNTR result group.

        Supports:
        - Dictionary of DataFrames
        - Single DataFrame
        """

        extracted = {}

        if result_group is None:
            return extracted

        if isinstance(result_group, pd.DataFrame):

            extracted["Result"] = (
                self.serialize_dataframe(result_group)
            )

            return extracted

        if isinstance(result_group, dict):

            for variable_name, dataframe in result_group.items():

                if isinstance(dataframe, pd.DataFrame):

                    extracted[str(variable_name)] = (
                        self.serialize_dataframe(dataframe)
                    )

        return extracted

    # ==========================================
    # 5. EXTRACT TIME STEPS
    # ==========================================

    def extract_time_steps(self, simulation_results):
        """
        Extract time index from available node/link results.
        """

        for group_name in ("node", "link"):

            result_group = getattr(
                simulation_results,
                group_name,
                None
            )

            if isinstance(result_group, pd.DataFrame):

                return self.to_json_safe(
                    result_group.index.tolist()
                )

            if isinstance(result_group, dict):

                for dataframe in result_group.values():

                    if isinstance(dataframe, pd.DataFrame):

                        return self.to_json_safe(
                            dataframe.index.tolist()
                        )

        return []

    # ==========================================
    # 6. EXTRACT ADDITIONAL RESULTS
    # ==========================================

    def extract_additional_results(self, simulation_results):
        """
        Extract additional public DataFrames and
        dictionaries of DataFrames from the result object.
        """

        extracted = {}

        try:

            attributes = vars(simulation_results)

        except TypeError:

            return extracted

        for attribute_name, value in attributes.items():

            if attribute_name.startswith("_"):
                continue

            if attribute_name in ("node", "link"):
                continue

            if isinstance(value, pd.DataFrame):

                extracted[attribute_name] = (
                    self.serialize_dataframe(value)
                )

            elif isinstance(value, dict):

                additional_group = (
                    self.extract_result_group(value)
                )

                if additional_group:

                    extracted[attribute_name] = (
                        additional_group
                    )

        return extracted

    # ==========================================
    # 7. COLLECT ONE SCENARIO
    # ==========================================

    def collect_scenario(
        self,
        scenario_name,
        simulation_results,
        execution_info,
        scenario_definition=None
    ):
        """
        Collect all available results for one scenario.
        """

        execution_status = execution_info.get(
            "Status",
            "UNKNOWN"
        )

        scenario_data = {

            "Scenario_Name": scenario_name,

            "Status": execution_status,

            "Execution": self.to_json_safe(
                execution_info
            ),

            "Scenario_Definition": self.to_json_safe(
                scenario_definition
            ),

            "Time_Steps": [],

            "Available_Result_Variables": {

                "Node": [],

                "Link": []
            },

            "Node_Results": {},

            "Link_Results": {},

            "Other_Results": {}
        }

        if (
            execution_status != "SUCCESS"
            or simulation_results is None
        ):

            scenario_data["Status"] = "FAILED"

            return scenario_data

        # --------------------------------------
        # NODE RESULTS
        # --------------------------------------

        node_results = getattr(
            simulation_results,
            "node",
            None
        )

        scenario_data["Node_Results"] = (
            self.extract_result_group(node_results)
        )

        # --------------------------------------
        # LINK RESULTS
        # --------------------------------------

        link_results = getattr(
            simulation_results,
            "link",
            None
        )

        scenario_data["Link_Results"] = (
            self.extract_result_group(link_results)
        )

        # --------------------------------------
        # TIME STEPS
        # --------------------------------------

        scenario_data["Time_Steps"] = (
            self.extract_time_steps(
                simulation_results
            )
        )

        # --------------------------------------
        # AVAILABLE VARIABLES
        # --------------------------------------

        scenario_data["Available_Result_Variables"] = {

            "Node": list(
                scenario_data["Node_Results"].keys()
            ),

            "Link": list(
                scenario_data["Link_Results"].keys()
            )
        }

        # --------------------------------------
        # ADDITIONAL RESULTS
        # --------------------------------------

        scenario_data["Other_Results"] = (
            self.extract_additional_results(
                simulation_results
            )
        )

        return scenario_data

    # ==========================================
    # 8. COLLECT ALL SCENARIOS
    # ==========================================

    def collect_all(
        self,
        simulation_output,
        scenario_definitions,
        network_si_data=None
    ):
        """
        Collect results of all simulation scenarios.
        """

        simulation_results = simulation_output.get(
            "Results",
            {}
        )

        execution_summary = simulation_output.get(
            "Execution Summary",
            {}
        )

        # --------------------------------------
        # SCENARIO DEFINITIONS
        # --------------------------------------

        definitions = {

            item["Scenario name"]: item

            for item in scenario_definitions.get(
                "Scenarios",
                []
            )
        }

        # Preserve the order of scenario definitions.
        scenario_names = list(definitions.keys())

        # Include any additional scenario in execution output.
        for name in execution_summary:

            if name not in scenario_names:
                scenario_names.append(name)

        for name in simulation_results:

            if name not in scenario_names:
                scenario_names.append(name)

        # --------------------------------------
        # COLLECT EACH SCENARIO
        # --------------------------------------

        all_scenarios = {}

        for scenario_name in scenario_names:

            result = simulation_results.get(
                scenario_name
            )

            execution_info = execution_summary.get(

                scenario_name,

                {
                    "Status": (
                        "SUCCESS"
                        if result is not None
                        else "FAILED"
                    ),

                    "Error": None
                }
            )

            scenario_data = self.collect_scenario(

                scenario_name=scenario_name,

                simulation_results=result,

                execution_info=execution_info,

                scenario_definition=definitions.get(
                    scenario_name
                )
            )

            all_scenarios[scenario_name] = scenario_data

        # --------------------------------------
        # SIMULATION SUMMARY
        # --------------------------------------

        successful = sum(

            1

            for item in all_scenarios.values()

            if item["Status"] == "SUCCESS"
        )

        failed = (
            len(all_scenarios) - successful
        )

        # --------------------------------------
        # NETWORK INFORMATION
        # --------------------------------------

        if network_si_data is not None:

            network_information = {

                "Summary": self.to_json_safe(
                    network_si_data.get(
                        "Summary",
                        []
                    )
                ),

                "Unit_Information": self.to_json_safe(
                    network_si_data.get(
                        "Unit Information",
                        []
                    )
                ),

                "Flow_Unit_In_Source_INP": (
                    network_si_data.get(
                        "Flow unit in source INP"
                    )
                ),

                "Headloss_Formula": (
                    network_si_data.get(
                        "Headloss formula"
                    )
                )
            }

        else:

            network_information = None

        # --------------------------------------
        # FINAL RESULTS STRUCTURE
        # --------------------------------------

        self.results_data = {

            "Project_Information": {

                "Results_Version": "1.0",

                "Created_At": datetime.now(
                    timezone.utc
                ).isoformat(),

                "Simulation_Engine": "WNTRSimulator",

                "WNTR_Version": getattr(
                    wntr,
                    "__version__",
                    "Unknown"
                ),

                "Pandas_Version": pd.__version__,

                "NumPy_Version": np.__version__,

                "Storage_Format": "JSON",

                "Data_Representation": (
                    "Pandas DataFrame split format"
                ),

                "Unit_Conversion_Applied": False,

                "Time_Index_Description": (
                    "Preserved as returned by WNTR"
                )
            },

            "Network_Information": network_information,

            "Simulation_Summary": {

                "Total_Scenarios": len(all_scenarios),

                "Successful": successful,

                "Failed": failed
            },

            "Scenarios": all_scenarios
        }

        return self.results_data

    # ==========================================
    # 9. SAVE RESULTS TO JSON
    # ==========================================

    def save_json(self):
        """
        Save all collected results into a JSON file.
        """

        if not self.results_data:

            raise ResultsManagerError(
                "No results available. "
                "Call collect_all() first."
            )

        self.output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            self.output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(

                self.results_data,

                file,

                ensure_ascii=False,

                indent=4,

                allow_nan=False
            )

        print("\n")
        print("=" * 55)
        print("RESULTS EXPORT")
        print("=" * 55)

        print("Status: SUCCESS")

        print(
            f"Output file: {self.output_file}"
        )

        print(
            "Scenarios saved:",
            len(self.results_data["Scenarios"])
        )

        print(
            "File size:",
            round(
                self.output_file.stat().st_size / 1024,
                2
            ),
            "KB"
        )

    # ==========================================
    # 10. DISPLAY RESULTS SUMMARY
    # ==========================================

    def show_summary(self):
        """
        Display a summary of collected results.
        """

        if not self.results_data:

            print("No results collected.")

            return

        summary = self.results_data[
            "Simulation_Summary"
        ]

        print("\n")
        print("=" * 55)
        print("RESULTS MANAGER SUMMARY")
        print("=" * 55)

        print(
            f"Total scenarios : {summary['Total_Scenarios']}"
        )

        print(
            f"Successful      : {summary['Successful']}"
        )

        print(
            f"Failed          : {summary['Failed']}"
        )

        print("\n")
        print("=" * 55)
        print("AVAILABLE RESULT VARIABLES")
        print("=" * 55)

        for name, scenario in (
            self.results_data["Scenarios"].items()
        ):

            print(f"\nScenario: {name}")

            print(
                f"Status: {scenario['Status']}"
            )

            print(
                "Time steps:",
                len(scenario["Time_Steps"])
            )

            print(
                "Node variables:",
                scenario[
                    "Available_Result_Variables"
                ]["Node"]
            )

            print(
                "Link variables:",
                scenario[
                    "Available_Result_Variables"
                ]["Link"]
            )
