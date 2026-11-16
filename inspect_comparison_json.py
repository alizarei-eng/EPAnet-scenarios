
import json
from pathlib import Path
from collections import Counter


def inspect_value(value, path="$", depth=0, max_depth=5):
    """
    بررسی بازگشتی ساختار JSON بدون چاپ تمام داده‌ها.
    """
    result = []

    if isinstance(value, dict):
        keys = list(value.keys())

        result.append({
            "path": path,
            "type": "dict",
            "count": len(keys),
            "keys": keys[:30]
        })

        if depth < max_depth:
            for key, item in value.items():
                result.extend(
                    inspect_value(
                        item,
                        path=f"{path}.{key}",
                        depth=depth + 1,
                        max_depth=max_depth
                    )
                )

    elif isinstance(value, list):
        result.append({
            "path": path,
            "type": "list",
            "count": len(value),
            "sample_type": type(value[0]).__name__ if value else "empty"
        })

        if value and depth < max_depth:
            result.extend(
                inspect_value(
                    value[0],
                    path=f"{path}[0]",
                    depth=depth + 1,
                    max_depth=max_depth
                )
            )

    else:
        result.append({
            "path": path,
            "type": type(value).__name__,
            "count": 1
        })

    return result


def inspect_comparison_json(json_file, report_file=None):
    """
    بارگذاری و بررسی Comparison_Results.json
    """

    json_file = Path(json_file)

    if not json_file.exists():
        raise FileNotFoundError(
            f"Comparison JSON not found: {json_file}"
        )

    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    structure = inspect_value(data)

    top_level_keys = (
        list(data.keys()) if isinstance(data, dict) else []
    )

    scenario_count = None

    if isinstance(data, dict):
        for key in ("Scenario_Count", "Scenario count"):
            if key in data:
                scenario_count = data[key]
                break

    report = {
        "File": str(json_file),
        "Top_Level_Keys": top_level_keys,
        "Scenario_Count": scenario_count,
        "Structure": structure
    }

    print("\n" + "=" * 65)
    print("COMPARISON JSON INSPECTION")
    print("=" * 65)

    print(f"File: {json_file.name}")
    print(f"Top-level sections: {len(top_level_keys)}")

    if scenario_count is not None:
        print(f"Scenario count: {scenario_count}")

    print("\nTop-level keys:")

    for key in top_level_keys:
        value = data[key]

        if isinstance(value, dict):
            description = f"Dictionary ({len(value)} keys)"
        elif isinstance(value, list):
            description = f"List ({len(value)} items)"
        else:
            description = type(value).__name__

        print(f"  - {key}: {description}")

    print("\nStructure details:")

    for item in structure:
        if item["type"] in ("dict", "list"):
            print(
                f"  {item['path']} | "
                f"{item['type']} | "
                f"count={item['count']}"
            )

    if report_file:
        report_file = Path(report_file)

        with open(report_file, "w", encoding="utf-8") as file:
            file.write("COMPARISON JSON INSPECTION REPORT\n")
            file.write("=" * 65 + "\n\n")
            file.write(f"Source: {json_file}\n")
            file.write(f"Top-level keys: {top_level_keys}\n")
            file.write(f"Scenario count: {scenario_count}\n\n")

            for item in structure:
                file.write(
                    f"{item['path']} | "
                    f"{item['type']} | "
                    f"count={item['count']}\n"
                )

        print(f"\nInspection report saved: {report_file}")

    print("=" * 65)

    return report


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent

    comparison_file = (
        BASE_DIR
        / "network_information_result"
        / "Comparison_Results.json"
    )

    report_file = (
        BASE_DIR
        / "network_information_result"
        / "Comparison_JSON_Inspection.txt"
    )

    inspect_comparison_json(
        comparison_file,
        report_file
    )
