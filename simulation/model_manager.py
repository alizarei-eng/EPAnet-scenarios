
from pathlib import Path
import json
import wntr


class ModelManagerError(Exception):
    pass


class ModelManager:

    def __init__(
        self,
        inp_file,
        network_original_json,
        network_si_json,
        scenario_json
    ):

        self.inp_file = Path(inp_file)
        self.network_original_json = Path(network_original_json)
        self.network_si_json = Path(network_si_json)
        self.scenario_json = Path(scenario_json)

        self.network_original = None
        self.network_si = None
        self.scenario_data = None

        self.base_model = None
        self.prepared_models = {}

        self.validate_files()
        self.load_json_files()
        self.load_base_model()

    # --------------------------------------------------
    # 1. File validation
    # --------------------------------------------------

    def validate_files(self):

        files = {
            "INP": self.inp_file,
            "Network Original JSON": self.network_original_json,
            "Network SI JSON": self.network_si_json,
            "Scenario JSON": self.scenario_json
        }

        for name, path in files.items():

            if not path.exists() or not path.is_file():
                raise ModelManagerError(
                    f"{name} file not found: {path}"
                )

    # --------------------------------------------------
    # 2. JSON loading
    # --------------------------------------------------

    @staticmethod
    def read_json(path):

        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)

        except (json.JSONDecodeError, OSError) as error:
            raise ModelManagerError(
                f"Cannot read JSON file {path}: {error}"
            )

    def load_json_files(self):

        self.network_original = self.read_json(
            self.network_original_json
        )

        self.network_si = self.read_json(
            self.network_si_json
        )

        self.scenario_data = self.read_json(
            self.scenario_json
        )

        for name, data in [
            ("Network Original", self.network_original),
            ("Network SI", self.network_si),
            ("Scenario", self.scenario_data)
        ]:

            if not isinstance(data, dict):
                raise ModelManagerError(
                    f"{name} JSON must contain an object."
                )

        if not isinstance(
            self.scenario_data.get("Scenarios"), list
        ):
            raise ModelManagerError(
                "Scenario JSON does not contain a valid Scenarios list."
            )

        print("All JSON files loaded successfully.")

    # --------------------------------------------------
    # 3. Load base model
    # --------------------------------------------------

    def load_base_model(self):

        try:
            self.base_model = wntr.network.WaterNetworkModel(
                str(self.inp_file)
            )

        except Exception as error:
            raise ModelManagerError(
                f"Failed to load INP model: {error}"
            )

        print("Base WNTR model loaded successfully.")

    # --------------------------------------------------
    # 4. Create independent model
    # --------------------------------------------------

    def create_independent_model(self):

        try:
            return wntr.network.WaterNetworkModel(
                str(self.inp_file)
            )

        except Exception as error:
            raise ModelManagerError(
                f"Failed to create independent model: {error}"
            )

    # --------------------------------------------------
    # 5. Find element in SI JSON
    # --------------------------------------------------

    def find_network_element(self, component, element_name):

        component_map = {
            "junctions": "Junctions",
            "pipes": "Pipes",
            "reservoirs": "Reservoirs",
            "tanks": "Tanks",
            "pumps": "Pumps",
            "valves": "Valves"
        }

        section = component_map.get(
            component.strip().lower()
        )

        if section is None:
            raise ModelManagerError(
                f"Unsupported component: {component}"
            )

        elements = self.network_si.get(section)

        if not isinstance(elements, list):
            raise ModelManagerError(
                f"Invalid or missing section: {section}"
            )

        for item in elements:

            if item.get("Name") == element_name:
                return item

        raise ModelManagerError(
            f"{element_name} not found in Network SI JSON."
        )

    # --------------------------------------------------
    # 6. Apply pipe diameter
    # --------------------------------------------------

    def set_pipe_diameter(self, model, element_name, value):

        if value <= 0:
            raise ModelManagerError(
                "Pipe diameter must be greater than zero."
            )

        self.find_network_element(
            "Pipes", element_name
        )

        try:
            pipe = model.get_link(element_name)

        except Exception:
            raise ModelManagerError(
                f"Pipe not found in WNTR model: {element_name}"
            )

        if not isinstance(
            pipe, wntr.network.elements.Pipe
        ):
            raise ModelManagerError(
                f"{element_name} is not a Pipe."
            )

        pipe.diameter = value

        print(
            f"Pipe {element_name}: Diameter = {value} m"
        )

    # --------------------------------------------------
    # 7. Apply junction demands
    # --------------------------------------------------

    def set_junction_demands(
        self,
        model,
        element_name,
        new_demands
    ):

        if not isinstance(new_demands, list):
            raise ModelManagerError(
                "Junction Demands must be a list."
            )

        if not new_demands:
            raise ModelManagerError(
                "Junction Demands list is empty."
            )

        self.find_network_element(
            "Junctions", element_name
        )

        try:
            junction = model.get_node(element_name)

        except Exception:
            raise ModelManagerError(
                f"Junction not found in WNTR: {element_name}"
            )

        if not isinstance(
            junction,
            wntr.network.elements.Junction
        ):
            raise ModelManagerError(
                f"{element_name} is not a Junction."
            )

        current_demands = junction.demand_timeseries_list

        if len(current_demands) != len(new_demands):
            raise ModelManagerError(
                f"Demand category count mismatch at {element_name}. "
                f"INP: {len(current_demands)}, "
                f"Scenario: {len(new_demands)}"
            )

        for index, demand_data in enumerate(new_demands):

            if not isinstance(demand_data, dict):
                raise ModelManagerError(
                    "Invalid Demand data structure."
                )

            if "Base demand" not in demand_data:
                raise ModelManagerError(
                    "Missing 'Base demand' in Demand data."
                )

            try:
                base_value = float(
                    demand_data["Base demand"]
                )

            except (TypeError, ValueError):
                raise ModelManagerError(
                    "Invalid Base demand value."
                )

            if base_value < 0:
                raise ModelManagerError(
                    "Base demand cannot be negative."
                )

            current_demands[index].base_value = base_value

            pattern_name = demand_data.get("Pattern")

            if pattern_name is not None:
                if pattern_name not in model.pattern_name_list:
                    raise ModelManagerError(
                        f"Pattern not found: {pattern_name}"
                    )

            current_demands[index].pattern_name = pattern_name

        print(
            f"Junction {element_name}: "
            f"{len(new_demands)} demand category/categories updated."
        )

    # --------------------------------------------------
    # 8. Apply one change
    # --------------------------------------------------

    def apply_change(self, model, change):

        required = [
            "Component",
            "Element",
            "Parameter",
            "New SI Value"
        ]

        for field in required:

            if field not in change:
                raise ModelManagerError(
                    f"Missing field in change: {field}"
                )

        component = change["Component"].strip().lower()
        parameter = change["Parameter"].strip().lower()
        element = change["Element"]
        new_value = change["New SI Value"]

        if component == "pipes" and parameter == "diameter":

            self.set_pipe_diameter(
                model,
                element,
                float(new_value)
            )

        elif component == "junctions" and parameter == "demands":

            self.set_junction_demands(
                model,
                element,
                new_value
            )

        else:
            raise ModelManagerError(
                f"Unsupported change: {component}, {parameter}"
            )

    # --------------------------------------------------
    # 9. Apply one scenario
    # --------------------------------------------------

    def apply_scenario(self, scenario):

        scenario_name = scenario.get(
            "Scenario name", "Unnamed Scenario"
        )

        changes = scenario.get("Changes")

        if not isinstance(changes, list):
            raise ModelManagerError(
                f"Invalid Changes in {scenario_name}"
            )

        model = self.create_independent_model()

        try:

            for change in changes:
                self.apply_change(model, change)

        except Exception as error:

            del model

            raise ModelManagerError(
                f"Scenario failed: {scenario_name}\n{error}"
            )

        return model

    # --------------------------------------------------
    # 10. Prepare all scenarios
    # --------------------------------------------------

    def prepare_all_scenarios(self):

        scenarios = self.scenario_data["Scenarios"]

        declared_count = self.scenario_data.get(
            "Scenario count"
        )

        if declared_count is not None:
            if declared_count != len(scenarios):
                raise ModelManagerError(
                    "Scenario count does not match "
                    "the number of scenario records."
                )

        self.prepared_models = {}

        successful = 0
        failed = 0

        print("\n================================")
        print("MODEL MANAGER - SCENARIO PREPARATION")
        print("================================")

        for index, scenario in enumerate(scenarios, start=1):

            name = scenario.get(
                "Scenario name",
                f"Scenario_{index}"
            )

            print(f"\n[{index}/{len(scenarios)}] {name}")

            if name in self.prepared_models:
                print("ERROR: Duplicate scenario name.")
                failed += 1
                continue

            try:

                model = self.apply_scenario(scenario)

                self.prepared_models[name] = model

                successful += 1

                print("Status: SUCCESS")

            except Exception as error:

                failed += 1

                print(f"Status: FAILED\n{error}")

        print("\n================================")
        print("PREPARATION SUMMARY")
        print("================================")
        print(f"Total scenarios : {len(scenarios)}")
        print(f"Successful      : {successful}")
        print(f"Failed          : {failed}")

        return self.prepared_models

    # --------------------------------------------------
    # 11. Get prepared model
    # --------------------------------------------------

    def get_model(self, scenario_name):

        if scenario_name not in self.prepared_models:
            raise ModelManagerError(
                f"Model not found: {scenario_name}"
            )

        return self.prepared_models[scenario_name]

    # --------------------------------------------------
    # 12. Network inventory
    # --------------------------------------------------

    def get_network_inventory(self):

        return {
            "Junctions": list(self.base_model.junction_name_list),
            "Reservoirs": list(self.base_model.reservoir_name_list),
            "Tanks": list(self.base_model.tank_name_list),
            "Pipes": list(self.base_model.pipe_name_list),
            "Pumps": list(self.base_model.pump_name_list),
            "Valves": list(self.base_model.valve_name_list)
        }

    def show_network_inventory(self):

        inventory = self.get_network_inventory()

        print("\n================================")
        print("NETWORK INVENTORY")
        print("================================")

        for component, elements in inventory.items():

            print(f"\n{component}: {len(elements)}")

            for element in elements:
                print(f"  - {element}")

    # --------------------------------------------------
    # 13. Show prepared scenarios
    # --------------------------------------------------

    def show_prepared_scenarios(self):

        print("\n================================")
        print("PREPARED SCENARIOS")
        print("================================")

        if not self.prepared_models:
            print("No prepared models.")
            return

        for name in self.prepared_models:
            print(name)
