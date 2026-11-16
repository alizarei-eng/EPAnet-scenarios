
import os
import json
import math
from datetime import datetime


# ============================================================
# PATHS
# ============================================================

PROJECT_DIR = (
    r"D:\desalination_lengeh"
    r"\EPAnet_lahestan_project"
    r"\examle_learning"
)

RESULTS_DIR = os.path.join(
    PROJECT_DIR,
    "network_information_result"
)

COMPARISON_FILE = os.path.join(
    RESULTS_DIR,
    "Comparison_Results.json"
)

SCENARIO_FILE = os.path.join(
    RESULTS_DIR,
    "Scenario_Definitions.json"
)

REPORT_FILE = os.path.join(
    RESULTS_DIR,
    "Comparison_Validation_Report.txt"
)


# ============================================================
# EXPECTED MAIN SECTIONS
# ============================================================

EXPECTED_SECTIONS = [
    "Scenario_Comparisons",
    "Network_Performance",
    "Correlation_Analysis",
    "Sensitivity_Analysis",
    "Scenario_Rankings"
]


# ============================================================
# VALIDATION CLASS
# ============================================================

class ComparisonValidator:

    def __init__(self, comparison_file, scenario_file):

        self.comparison_file = comparison_file
        self.scenario_file = scenario_file

        self.data = None
        self.scenario_data = None

        self.errors = []
        self.warnings = []
        self.passed = []

        self.numeric_count = 0
        self.invalid_numeric_count = 0

    # --------------------------------------------------------
    # LOAD FILES
    # --------------------------------------------------------

    def load_files(self):

        print("\n" + "=" * 65)
        print("STEP 1: LOADING JSON FILES")
        print("=" * 65)

        if not os.path.isfile(self.comparison_file):
            raise FileNotFoundError(
                f"Comparison file not found:\n"
                f"{self.comparison_file}"
            )

        with open(
            self.comparison_file,
            "r",
            encoding="utf-8"
        ) as file:

            self.data = json.load(file)

        self.passed.append(
            "Comparison_Results.json loaded successfully"
        )

        print("[OK] Comparison_Results.json")

        if os.path.isfile(self.scenario_file):

            with open(
                self.scenario_file,
                "r",
                encoding="utf-8"
            ) as file:

                self.scenario_data = json.load(file)

            self.passed.append(
                "Scenario_Definitions.json loaded successfully"
            )

            print("[OK] Scenario_Definitions.json")

        else:

            self.warnings.append(
                "Scenario_Definitions.json not found"
            )

            print("[WARNING] Scenario file not found")

    # --------------------------------------------------------
    # CHECK JSON ROOT
    # --------------------------------------------------------

    def validate_root(self):

        print("\n" + "=" * 65)
        print("STEP 2: ROOT STRUCTURE VALIDATION")
        print("=" * 65)

        if not isinstance(self.data, dict):

            self.errors.append(
                "JSON root must be a dictionary/object"
            )

            return

        print("[OK] JSON root is an object")

        for section in EXPECTED_SECTIONS:

            if section not in self.data:

                self.errors.append(
                    f"Missing main section: {section}"
                )

                print(f"[ERROR] Missing: {section}")

            elif not isinstance(self.data[section], (dict, list)):

                self.errors.append(
                    f"Invalid data type for section: {section}"
                )

                print(f"[ERROR] Invalid type: {section}")

            elif not self.data[section]:

                self.warnings.append(
                    f"Section is empty: {section}"
                )

                print(f"[WARNING] Empty: {section}")

            else:

                self.passed.append(
                    f"Main section exists: {section}"
                )

                print(f"[OK] {section}")

    # --------------------------------------------------------
    # SHOW STRUCTURE
    # --------------------------------------------------------

    def show_structure(self, obj=None, prefix="ROOT", depth=0):

        if obj is None:
            obj = self.data

        if depth > 3:
            return

        if isinstance(obj, dict):

            for key, value in obj.items():

                path = f"{prefix}.{key}"

                if isinstance(value, dict):

                    print(
                        f"{path} -> DICTIONARY "
                        f"({len(value)} items)"
                    )

                    self.show_structure(
                        value,
                        path,
                        depth + 1
                    )

                elif isinstance(value, list):

                    print(
                        f"{path} -> LIST "
                        f"({len(value)} items)"
                    )

                    if value:

                        self.show_structure(
                            value[0],
                            path + "[0]",
                            depth + 1
                        )

                else:

                    print(
                        f"{path} -> {type(value).__name__}"
                    )

        elif isinstance(obj, list) and obj:

            self.show_structure(
                obj[0],
                prefix + "[0]",
                depth + 1
            )

    # --------------------------------------------------------
    # SCENARIO COUNT VALIDATION
    # --------------------------------------------------------

    def validate_scenario_count(self):

        print("\n" + "=" * 65)
        print("STEP 3: SCENARIO COUNT VALIDATION")
        print("=" * 65)

        if self.scenario_data is None:
            return

        expected_scenarios = self.scenario_data.get(
            "Scenarios",
            []
        )

        expected_count = len(expected_scenarios)

        comparisons = self.data.get(
            "Scenario_Comparisons"
        )

        if isinstance(comparisons, dict):

            actual_count = len(comparisons)

        elif isinstance(comparisons, list):

            actual_count = len(comparisons)

        else:

            self.warnings.append(
                "Cannot determine comparison scenario count"
            )

            return

        print(
            f"Defined scenarios: {expected_count}"
        )

        print(
            f"Compared scenarios: {actual_count}"
        )

        # Reference scenario may be excluded from comparisons.
        if actual_count == expected_count:

            self.passed.append(
                "Scenario count matches definitions"
            )

            print("[OK] Scenario counts match")

        elif actual_count == expected_count - 1:

            self.passed.append(
                "Comparison count is one less than definitions; "
                "this may be due to excluding the reference scenario"
            )

            print(
                "[OK] One reference scenario may be excluded"
            )

        else:

            self.warnings.append(
                f"Scenario count mismatch: "
                f"{expected_count} defined, "
                f"{actual_count} compared"
            )

            print("[WARNING] Scenario counts differ")

    # --------------------------------------------------------
    # NUMERIC VALIDATION
    # --------------------------------------------------------

    
    # --------------------------------------------------------
    # NUMERIC VALIDATION - ITERATIVE VERSION
    # --------------------------------------------------------

    def validate_numeric_values(self, obj=None, path="ROOT"):

        if obj is None:
            obj = self.data

        stack = [(obj, path)]

        while stack:

            current_obj, current_path = stack.pop()

            if isinstance(current_obj, dict):

                for key, value in current_obj.items():

                    new_path = f"{current_path}.{key}"

                    stack.append((value, new_path))

            elif isinstance(current_obj, list):

                for index, value in enumerate(current_obj):

                    new_path = f"{current_path}[{index}]"

                    stack.append((value, new_path))

            elif isinstance(current_obj, bool):

                continue

            elif isinstance(current_obj, (int, float)):

                self.numeric_count += 1

                if not math.isfinite(current_obj):

                    self.invalid_numeric_count += 1

                    self.errors.append(
                        f"Invalid numeric value at "
                        f"{current_path}: {current_obj}"
                    )


    # --------------------------------------------------------
    # EMPTY VALUE CHECK
    # --------------------------------------------------------

    def check_empty_sections(self):

        print("\n" + "=" * 65)
        print("STEP 4: EMPTY VALUE CHECK")
        print("=" * 65)

        for section in EXPECTED_SECTIONS:

            value = self.data.get(section)

            if value is None:

                continue

            if isinstance(value, (dict, list)) and len(value) == 0:

                self.warnings.append(
                    f"Empty section: {section}"
                )

                print(
                    f"[WARNING] {section} is empty"
                )

            else:

                print(
                    f"[OK] {section} contains data"
                )

    # --------------------------------------------------------
    # CORRELATION CHECK
    # --------------------------------------------------------

    def validate_correlations(self):

        print("\n" + "=" * 65)
        print("STEP 5: CORRELATION ANALYSIS CHECK")
        print("=" * 65)

        correlation_data = self.data.get(
            "Correlation_Analysis"
        )

        if not isinstance(correlation_data, dict):

            self.warnings.append(
                "Correlation analysis is not a dictionary"
            )

            return

        if not correlation_data:

            self.warnings.append(
                "Correlation analysis contains no data"
            )

            return

        print("[OK] Correlation section exists")

        text = json.dumps(
            correlation_data,
            ensure_ascii=False
        ).lower()

        methods = [
            "pearson",
            "spearman",
            "kendall"
        ]

        for method in methods:

            if method in text:

                self.passed.append(
                    f"{method.title()} method found"
                )

                print(
                    f"[OK] {method.title()} found"
                )

            else:

                self.warnings.append(
                    f"{method.title()} not found in correlation output"
                )

                print(
                    f"[WARNING] {method.title()} not found"
                )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    def show_results(self):

        print("\n" + "=" * 65)
        print("FINAL VALIDATION SUMMARY")
        print("=" * 65)

        print(
            f"\nPassed checks: {len(self.passed)}"
        )

        print(
            f"Warnings: {len(self.warnings)}"
        )

        print(
            f"Errors: {len(self.errors)}"
        )

        print(
            f"Numeric values checked: {self.numeric_count}"
        )

        print(
            f"Invalid numeric values: "
            f"{self.invalid_numeric_count}"
        )

        if self.errors:

            print("\nERRORS:")

            for item in self.errors:
                print(f"[ERROR] {item}")

        if self.warnings:

            print("\nWARNINGS:")

            for item in self.warnings:
                print(f"[WARNING] {item}")

        if not self.errors:

            print("\nVALIDATION RESULT: PASSED")

        else:

            print("\nVALIDATION RESULT: FAILED")

    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    def save_report(self):

        lines = []

        lines.append(
            "COMPARISON ENGINE VALIDATION REPORT"
        )

        lines.append(
            f"Date: {datetime.now().isoformat()}"
        )

        lines.append("=" * 60)

        lines.append(
            f"Passed: {len(self.passed)}"
        )

        lines.append(
            f"Warnings: {len(self.warnings)}"
        )

        lines.append(
            f"Errors: {len(self.errors)}"
        )

        lines.append(
            f"Numeric values checked: {self.numeric_count}"
        )

        lines.append(
            f"Invalid numeric values: "
            f"{self.invalid_numeric_count}"
        )

        lines.append("\nPASSED CHECKS:")

        for item in self.passed:
            lines.append(f"[OK] {item}")

        lines.append("\nWARNINGS:")

        for item in self.warnings:
            lines.append(f"[WARNING] {item}")

        lines.append("\nERRORS:")

        for item in self.errors:
            lines.append(f"[ERROR] {item}")

        with open(
            REPORT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            file.write("\n".join(lines))

        print(
            f"\nValidation report saved:\n{REPORT_FILE}"
        )

    # --------------------------------------------------------
    # RUN ALL CHECKS
    # --------------------------------------------------------

    def run(self):

        self.load_files()

        self.validate_root()

        if isinstance(self.data, dict):

            print("\n" + "=" * 65)
            print("JSON STRUCTURE OVERVIEW")
            print("=" * 65)

            self.show_structure()

            self.validate_scenario_count()

            self.check_empty_sections()

            self.validate_correlations()

            self.validate_numeric_values()

        self.show_results()

        self.save_report()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    validator = ComparisonValidator(
        comparison_file=COMPARISON_FILE,
        scenario_file=SCENARIO_FILE
    )

    validator.run()
