
"""
Simulation Engine
-----------------
Runs prepared EPANET network models using WNTR.

Responsibilities:
1. Receive prepared models from Model Manager.
2. Run hydraulic simulation for each scenario.
3. Store simulation results.
4. Record success or failure for each scenario.

This module does not modify network parameters
and does not compare scenarios.
"""

import wntr


class SimulationEngineError(Exception):
    """Custom exception for Simulation Engine errors."""
    pass


class SimulationEngine:

    def __init__(self):
        self.results = {}
        self.execution_summary = {}

    def run_scenario(self, model, scenario_name):
        """
        Run one prepared network model.

        Parameters
        ----------
        model : wntr.network.WaterNetworkModel
            Prepared independent network model.

        scenario_name : str
            Scenario name.

        Returns
        -------
        dict
            Simulation result and execution status.
        """

        print("\n" + "=" * 50)
        print(f"Running scenario: {scenario_name}")
        print("=" * 50)

        try:
            simulator = wntr.sim.WNTRSimulator(model)

            simulation_results = simulator.run_sim()

            self.results[scenario_name] = simulation_results

            self.execution_summary[scenario_name] = {
                "Status": "SUCCESS",
                "Error": None
            }

            print(f"Status: SUCCESS")

            return {
                "Scenario name": scenario_name,
                "Status": "SUCCESS",
                "Results": simulation_results,
                "Error": None
            }

        except Exception as error:

            error_message = str(error)

            self.execution_summary[scenario_name] = {
                "Status": "FAILED",
                "Error": error_message
            }

            print("Status: FAILED")
            print(f"Error: {error_message}")

            return {
                "Scenario name": scenario_name,
                "Status": "FAILED",
                "Results": None,
                "Error": error_message
            }

    def run_all(self, model_manager, scenario_names):
        """
        Run all prepared scenarios.

        Parameters
        ----------
        model_manager : ModelManager
            Instance of ModelManager.

        scenario_names : list
            Names of prepared scenarios.

        Returns
        -------
        dict
            Results and execution summary for all scenarios.
        """

        print("\n")
        print("#" * 50)
        print("SIMULATION ENGINE")
        print("#" * 50)

        self.results = {}
        self.execution_summary = {}

        total = len(scenario_names)

        for index, scenario_name in enumerate(scenario_names, start=1):

            print(f"\n[{index}/{total}] {scenario_name}")

            try:
                model = model_manager.get_model(scenario_name)

                if model is None:
                    raise SimulationEngineError(
                        f"Model not found for scenario: {scenario_name}"
                    )

                self.run_scenario(model, scenario_name)

            except Exception as error:

                error_message = str(error)

                self.execution_summary[scenario_name] = {
                    "Status": "FAILED",
                    "Error": error_message
                }

                print("Status: FAILED")
                print(f"Error: {error_message}")

        return {
            "Results": self.results,
            "Execution Summary": self.execution_summary
        }

    def show_summary(self):

        total = len(self.execution_summary)

        successful = sum(
            1 for item in self.execution_summary.values()
            if item["Status"] == "SUCCESS"
        )

        failed = total - successful

        print("\n")
        print("=" * 50)
        print("SIMULATION SUMMARY")
        print("=" * 50)

        print(f"Total scenarios : {total}")
        print(f"Successful      : {successful}")
        print(f"Failed          : {failed}")

        print("\nSCENARIO STATUS")
        print("-" * 50)

        for name, info in self.execution_summary.items():
            print(f"{name}")
            print(f"Status: {info['Status']}")

            if info["Error"]:
                print(f"Error: {info['Error']}")

            print("-" * 50)
