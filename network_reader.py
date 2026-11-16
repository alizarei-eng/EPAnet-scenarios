import os
import json
import math
import pandas as pd
import wntr

from wntr.epanet.util import (
    FlowUnits,
    HydParam,
    QualParam,
    from_si,
    MassUnits
)


# ============================================================
# 1. USER SETTINGS
# ============================================================

INPUT_FILE = "flow.inp"

OUTPUT_FOLDER = "network_information_result"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ============================================================
# 2. LOAD NETWORK
# ============================================================

print("\nLoading EPANET network...")

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

wn = wntr.network.WaterNetworkModel(INPUT_FILE)

print("Network loaded successfully.")


# ============================================================
# 3. READ EPANET SETTINGS
# ============================================================

flow_unit_name = str(
    wn.options.hydraulic.inpfile_units
).upper()

try:
    FLOW_UNIT = FlowUnits[flow_unit_name]

except KeyError:
    raise ValueError(
        f"Unsupported flow unit: {flow_unit_name}"
    )


HEADLOSS_FORMULA = str(
    wn.options.hydraulic.headloss
).upper()


IS_DARCY = HEADLOSS_FORMULA in (
    "D-W",
    "DARCY-WEISBACH"
)


print("\nEPANET SETTINGS")
print("--------------------------------")
print("Flow units:", FLOW_UNIT.name)
print("Headloss formula:", HEADLOSS_FORMULA)
print("Darcy-Weisbach:", IS_DARCY)


# ============================================================
# 4. GENERAL FUNCTIONS
# ============================================================

def safe_number(value):

    if value is None:
        return None

    try:

        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value

    except (TypeError, ValueError):

        return value


def convert_from_si(value, parameter, darcy=False):

    if value is None:
        return None

    try:

        result = from_si(
            FLOW_UNIT,
            value,
            parameter,
            darcy_weisbach=darcy
        )

        return safe_number(result)

    except Exception as error:

        print(
            f"Conversion warning: {parameter} - {error}"
        )

        return safe_number(value)


def get_pattern_name(pattern):

    if pattern is None:
        return None

    return getattr(pattern, "name", None)


def get_curve_name(curve):

    if curve is None:
        return None

    return getattr(curve, "name", None)


def convert_curve_point(x, y, curve_type):

    curve_type = str(curve_type).upper()

    if curve_type == "HEAD":

        return {
            "X": safe_number(x),
            "Y": safe_number(y)
        }, {
            "X": convert_from_si(x, HydParam.Flow),
            "Y": convert_from_si(
                y,
                HydParam.HydraulicHead
            )
        }

    elif curve_type == "VOLUME":

        return {
            "X": safe_number(x),
            "Y": safe_number(y)
        }, {
            "X": convert_from_si(
                x,
                HydParam.Length
            ),
            "Y": convert_from_si(
                y,
                HydParam.Volume
            )
        }

    elif curve_type == "HEADLOSS":

        return {
            "X": safe_number(x),
            "Y": safe_number(y)
        }, {
            "X": convert_from_si(x, HydParam.Flow),
            "Y": convert_from_si(
                y,
                HydParam.HydraulicHead
            )
        }

    elif curve_type == "EFFICIENCY":

        return {
            "X": safe_number(x),
            "Y": safe_number(y)
        }, {
            "X": convert_from_si(x, HydParam.Flow),
            "Y": safe_number(y)
        }

    else:

        return {
            "X": safe_number(x),
            "Y": safe_number(y)
        }, {
            "X": safe_number(x),
            "Y": safe_number(y)
        }


# ============================================================
# 5. UNIT INFORMATION
# ============================================================

if FLOW_UNIT.is_traditional:

    ORIGINAL_UNITS = {

        "Flow": FLOW_UNIT.name,
        "Demand": FLOW_UNIT.name,

        "Length": "ft",
        "Diameter": "inch",

        "Elevation": "ft",
        "Head": "ft",
        "Headloss": "ft",

        "Velocity": "ft/s",
        "Volume": "ft3",

        "Pressure": "psi",

        "Power": "hp",
        "Energy": "kWh",

        "Concentration": "mg/L",
        "Mass": "mg"
    }

else:

    ORIGINAL_UNITS = {

        "Flow": FLOW_UNIT.name,
        "Demand": FLOW_UNIT.name,

        "Length": "m",
        "Diameter": "mm",

        "Elevation": "m",
        "Head": "m",
        "Headloss": "m",

        "Velocity": "m/s",
        "Volume": "m3",

        "Pressure": "m",
        "Power": "kW",
        "Energy": "kWh",

        "Concentration": "mg/L",
        "Mass": "mg"
    }


SI_UNITS = {

    "Flow": "m3/s",
    "Demand": "m3/s",

    "Length": "m",
    "Diameter": "m",

    "Elevation": "m",
    "Head": "m",
    "Headloss": "m",

    "Velocity": "m/s",
    "Volume": "m3",

    "Pressure": "m water column",

    "Power": "W",
    "Energy": "J",

    "Concentration": "kg/m3",
    "Mass": "kg",

    "Time": "s"
}


# ============================================================
# 6. SUMMARY
# ============================================================

summary = {

    "Input file": INPUT_FILE,

    "Flow units": FLOW_UNIT.name,

    "Headloss formula": HEADLOSS_FORMULA,

    "Darcy-Weisbach": IS_DARCY,

    "Junction count": len(wn.junction_name_list),

    "Reservoir count": len(wn.reservoir_name_list),

    "Tank count": len(wn.tank_name_list),

    "Pipe count": len(wn.pipe_name_list),

    "Pump count": len(wn.pump_name_list),

    "Valve count": len(wn.valve_name_list),

    "Pattern count": len(wn.pattern_name_list),

    "Curve count": len(wn.curve_name_list)
}


# ============================================================
# 7. JUNCTIONS
# ============================================================

junctions = []

for name, node in wn.junctions():

    demands_si = []
    demands_original = []

    for demand in node.demand_timeseries_list:

        demands_si.append({

            "Base demand": safe_number(
                demand.base_value
            ),

            "Pattern": get_pattern_name(
                demand.pattern
            )
        })

        demands_original.append({

            "Base demand": convert_from_si(
                demand.base_value,
                HydParam.Demand
            ),

            "Pattern": get_pattern_name(
                demand.pattern
            )
        })


    junctions.append({

        "Name": name,

        "Elevation": {
            "SI": safe_number(node.elevation),

            "Original": convert_from_si(
                node.elevation,
                HydParam.Elevation
            )
        },

        "Demands": {
            "SI": demands_si,

            "Original": demands_original
        },

        "Emitter coefficient": {
            "SI": safe_number(
                node.emitter_coefficient
            ),

            "Original": convert_from_si(
                node.emitter_coefficient,
                HydParam.EmitterCoeff
            )
        }
    })


# ============================================================
# 8. RESERVOIRS
# ============================================================

reservoirs = []

for name, node in wn.reservoirs():

    head = node.head_timeseries.base_value

    reservoirs.append({

        "Name": name,

        "Head": {

            "SI": safe_number(head),

            "Original": convert_from_si(
                head,
                HydParam.HydraulicHead
            )
        },

        "Pattern": get_pattern_name(
            node.head_timeseries.pattern
        )
    })


# ============================================================
# 9. TANKS
# ============================================================

tanks = []

for name, node in wn.tanks():

    tanks.append({

        "Name": name,

        "Elevation": {

            "SI": safe_number(node.elevation),

            "Original": convert_from_si(
                node.elevation,
                HydParam.Elevation
            )
        },

        "Initial level": {

            "SI": safe_number(node.init_level),

            "Original": convert_from_si(
                node.init_level,
                HydParam.HydraulicHead
            )
        },

        "Minimum level": {

            "SI": safe_number(node.min_level),

            "Original": convert_from_si(
                node.min_level,
                HydParam.HydraulicHead
            )
        },

        "Maximum level": {

            "SI": safe_number(node.max_level),

            "Original": convert_from_si(
                node.max_level,
                HydParam.HydraulicHead
            )
        },

        "Diameter": {

            "SI": safe_number(node.diameter),

            "Original": convert_from_si(
                node.diameter,
                HydParam.TankDiameter
            )
        },

        "Minimum volume": {

            "SI": safe_number(node.min_vol),

            "Original": convert_from_si(
                node.min_vol,
                HydParam.Volume
            )
        },

        "Volume curve": get_curve_name(
            node.vol_curve
        ),

        "Mixing model": str(node.mixing_model),

        "Mixing fraction": safe_number(
            node.mixing_fraction
        ),

        "Overflow": bool(node.overflow)
    })


# ============================================================
# 10. PIPES
# ============================================================

pipes = []

for name, link in wn.pipes():

    pipes.append({

        "Name": name,

        "Start node": link.start_node_name,

        "End node": link.end_node_name,

        "Length": {

            "SI": safe_number(link.length),

            "Original": convert_from_si(
                link.length,
                HydParam.Length
            )
        },

        "Diameter": {

            "SI": safe_number(link.diameter),

            "Original": convert_from_si(
                link.diameter,
                HydParam.PipeDiameter
            )
        },

        "Roughness": {

            "SI": safe_number(link.roughness),

            "Original": convert_from_si(
                link.roughness,
                HydParam.RoughnessCoeff,
                darcy=IS_DARCY
            )
        },

        "Roughness formula": HEADLOSS_FORMULA,

        "Roughness unit": (
            "m"
            if IS_DARCY
            else "dimensionless"
        ),

        "Minor loss coefficient": safe_number(
            link.minor_loss
        ),

        "Status": str(link.initial_status),

        "Check valve": bool(link.check_valve)
    })


# ============================================================
# 11. PUMPS
# ============================================================

pumps = []

for name, pump in wn.pumps():

    power_si = None
    power_original = None

    if pump.pump_type == "POWER":

        power_si = safe_number(pump.power)

        power_original = convert_from_si(
            pump.power,
            HydParam.Power
        )


    pumps.append({

        "Name": name,

        "Start node": pump.start_node_name,

        "End node": pump.end_node_name,

        "Pump type": pump.pump_type,

        "Power": {

            "SI": power_si,

            "Original": power_original
        },

        "Head curve": pump.pump_curve_name,

        "Speed": safe_number(
            pump.speed_timeseries.base_value
        ),

        "Speed pattern": get_pattern_name(
            pump.speed_timeseries.pattern
        )
    })


# ============================================================
# 12. VALVES
# ============================================================

valves = []

for name, valve in wn.valves():

    valve_type = valve.valve_type

    setting = safe_number(
        valve.initial_setting
    )

    if valve_type in ("PRV", "PSV", "PBV"):

        setting_si = setting

        setting_original = convert_from_si(
            setting,
            HydParam.Pressure
        )

    elif valve_type == "FCV":

        setting_si = setting

        setting_original = convert_from_si(
            setting,
            HydParam.Flow
        )

    else:

        setting_si = setting
        setting_original = setting


    valves.append({

        "Name": name,

        "Start node": valve.start_node_name,

        "End node": valve.end_node_name,

        "Diameter": {

            "SI": safe_number(valve.diameter),

            "Original": convert_from_si(
                valve.diameter,
                HydParam.PipeDiameter
            )
        },

        "Valve type": valve_type,

        "Setting": {

            "SI": setting_si,

            "Original": setting_original
        },

        "Minor loss coefficient": safe_number(
            valve.minor_loss
        )
    })


# ============================================================
# 13. PATTERNS
# ============================================================

patterns = []

for name, pattern in wn.patterns():

    patterns.append({

        "Name": name,

        "Multipliers": [
            safe_number(x)
            for x in pattern.multipliers
        ]
    })


# ============================================================
# 14. CURVES
# ============================================================

curves = []

for name, curve in wn.curves():

    if curve is None:
        continue

    curve_type = str(
        curve.curve_type
    ).upper()

    points_si = []
    points_original = []

    for x, y in curve.points:

        si_point, original_point = convert_curve_point(
            x,
            y,
            curve_type
        )

        points_si.append(si_point)

        points_original.append(original_point)


    curves.append({

        "Name": name,

        "Curve type": curve_type,

        "Points": {

            "SI": points_si,

            "Original": points_original
        }
    })


# ============================================================
# 15. CONNECTIVITY
# ============================================================

connectivity = []

for name, link in wn.links():

    connectivity.append({

        "Link": name,

        "Link type": link.__class__.__name__,

        "Start node": link.start_node_name,

        "End node": link.end_node_name
    })


# ============================================================
# 16. ALL NODES
# ============================================================

all_nodes = []

for name, node in wn.nodes():

    all_nodes.append({

        "Name": name,

        "Type": node.__class__.__name__
    })


# ============================================================
# 17. ALL LINKS
# ============================================================

all_links = []

for name, link in wn.links():

    all_links.append({

        "Name": name,

        "Type": link.__class__.__name__,

        "Start node": link.start_node_name,

        "End node": link.end_node_name
    })


# ============================================================
# 18. BUILD DATASETS
# ============================================================

data = {

    "Summary": [summary],

    "Junctions": junctions,

    "Reservoirs": reservoirs,

    "Tanks": tanks,

    "Pipes": pipes,

    "Pumps": pumps,

    "Valves": valves,

    "Patterns": patterns,

    "Curves": curves,

    "Connectivity": connectivity,

    "All Nodes": all_nodes,

    "All Links": all_links
}


# ============================================================
# 19. RECURSIVE DATA SEPARATION
# ============================================================

def separate_data(obj, target):

    """
    target:
        SI
        Original

    Every parameter containing SI and Original
    is separated into an independent dataset.
    """

    if isinstance(obj, list):

        return [
            separate_data(item, target)
            for item in obj
        ]


    if isinstance(obj, dict):

        result = {}

        for key, value in obj.items():

            if key == "SI" or key == "Original":

                if key == target:

                    result = separate_data(
                        value,
                        target
                    )

                continue


            result[key] = separate_data(
                value,
                target
            )


        return result


    return obj


si_data = separate_data(data, "SI")

original_data = separate_data(data, "Original")


# ============================================================
# 20. ADD UNIT INFORMATION
# ============================================================

si_data["Unit Information"] = [{

    "Unit system": "SI",

    "Units": SI_UNITS,

    "Flow unit in source INP": FLOW_UNIT.name,

    "Headloss formula": HEADLOSS_FORMULA
}]


original_data["Unit Information"] = [{

    "Unit system": "Original EPANET",

    "Flow unit": FLOW_UNIT.name,

    "Headloss formula": HEADLOSS_FORMULA,

    "Units": ORIGINAL_UNITS
}]


# ============================================================
# 21. SAVE JSON
# ============================================================

def save_json(dataset, filename):

    path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dataset,
            file,
            ensure_ascii=False,
            indent=4,
            default=str
        )

    print("JSON saved:", path)


save_json(
    si_data,
    "Network_SI.json"
)

save_json(
    original_data,
    "Network_Original.json"
)


# ============================================================
# 22. SAVE EXCEL
# ============================================================

def save_excel(dataset, filename):

    path = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    with pd.ExcelWriter(
        path,
        engine="openpyxl"
    ) as writer:

        for sheet_name, rows in dataset.items():

            df = pd.json_normalize(rows)

            if df.empty:

                df = pd.DataFrame()

            df.to_excel(
                writer,
                sheet_name=sheet_name[:31],
                index=False
            )


    print("Excel saved:", path)


save_excel(
    si_data,
    "Network_SI.xlsx"
)

save_excel(
    original_data,
    "Network_Original.xlsx"
)


# ============================================================
# 23. FINISH
# ============================================================

print("\n")
print("=" * 55)

print("NETWORK READER COMPLETED SUCCESSFULLY")

print("=" * 55)

print("Input file:", INPUT_FILE)

print("Flow units:", FLOW_UNIT.name)

print("Headloss formula:", HEADLOSS_FORMULA)

print("\nOutput folder:")

print(os.path.abspath(OUTPUT_FOLDER))

print("\nGenerated files:")

print("1. Network_SI.xlsx")
print("2. Network_SI.json")
print("3. Network_Original.xlsx")
print("4. Network_Original.json")

print("\nAll operations completed.")