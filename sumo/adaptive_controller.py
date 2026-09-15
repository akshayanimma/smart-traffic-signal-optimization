
import os
import json
import time
import traci
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================
CURRENT_STATE = {
    "simulation_time": 0,
    "intersection": "center",
    "priority": "",
    "phase": 0,
    "green_time": 0,
    "prediction": {
    "ns": 0,
    "ew": 0
},
"actual": {
    "ns": 0,
    "ew": 0
},
"final": {
    "ns": 0,
    "ew": 0
}
}


def write_state():
    state_file = os.path.join(SCRIPT_DIR, "state.json")
    with open(state_file, "w") as f:
        json.dump(CURRENT_STATE, f, indent=2)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Prediction CSV
CSV_FILE = os.path.join(SCRIPT_DIR, "traffic_prediction.csv")
# SUMO configuration
SUMO_CONFIG = os.path.join(
    SCRIPT_DIR,
    "traffic.sumocfg"
)
SUMO_BINARY = "sumo-gui"
# Traffic light
TRAFFIC_LIGHT_ID = "center"

# Traffic signal phases
# Based on traffic.net.xml
PHASE_NS = 0
PHASE_EW = 2

# Adaptive timing limits
MIN_GREEN = 20
MAX_GREEN = 90

# How often controller makes a new decision
CONTROL_INTERVAL = 20

# Simulation duration
SIMULATION_END = 218


# ============================================================
# LOAD PREDICTION DATA
# ============================================================

def load_predictions():

    print("\nLoading prediction data...")

    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"Prediction CSV not found:\n{CSV_FILE}"
        )

    df = pd.read_csv(CSV_FILE)

    required_columns = [
        "timestamp",
        "road_id",
        "predicted_congestion",
        "congestion_score"
    ]

    for column in required_columns:

        if column not in df.columns:
            raise ValueError(
                f"CSV is missing required column: {column}\n"
                f"Available columns: {list(df.columns)}"
            )

    # Convert values to numeric
    df["timestamp"] = pd.to_numeric(
        df["timestamp"],
        errors="coerce"
    )

    df["congestion_score"] = pd.to_numeric(
        df["congestion_score"],
        errors="coerce"
    )

    # Clean road IDs
    df["road_id"] = (
        df["road_id"]
        .astype(str)
        .str.strip()
    )

    # Remove invalid rows
    df = df.dropna(
        subset=[
            "timestamp",
            "congestion_score"
        ]
    )

    # Sort by timestamp
    df = df.sort_values("timestamp")

    if df.empty:
        raise ValueError(
            "Prediction CSV contains no valid data."
        )

    prediction_start = float(
        df["timestamp"].min()
    )

    prediction_end = float(
        df["timestamp"].max()
    )

    prediction_duration = (
        prediction_end - prediction_start
    )

    print("Prediction data loaded successfully.")

    print(
        f"Prediction start : {prediction_start}"
    )

    print(
        f"Prediction end   : {prediction_end}"
    )

    print(
        f"Prediction span  : {prediction_duration} seconds"
    )

    print(
        f"Rows             : {len(df)}"
    )

    return df


# ============================================================
# GET CURRENT PREDICTION
# ============================================================

def get_current_scores(
    df,
    simulation_time
):

    prediction_start = float(
        df["timestamp"].min()
    )

    prediction_end = float(
        df["timestamp"].max()
    )

    # Convert SUMO time into prediction time
    target_prediction_time = (
        prediction_start + simulation_time
    )

    # Available timestamps
    timestamps = df["timestamp"].unique()

    # Find closest prediction timestamp
    closest_timestamp = min(
        timestamps,
        key=lambda x: abs(
            float(x) - target_prediction_time
        )
    )

    current_data = df[
        df["timestamp"] == closest_timestamp
    ]

    scores = {}

    for _, row in current_data.iterrows():

        road_id = row["road_id"]

        score = float(
            row["congestion_score"]
        )

        scores[road_id] = score

    return (
        scores,
        float(closest_timestamp),
        target_prediction_time,
        prediction_end
    )


# ============================================================
# CALCULATE DIRECTION SCORES
# ============================================================

def calculate_direction_scores(scores):

    # Incoming and outgoing roads

    north_roads = [
        "north_to_center",
        "center_to_north"
    ]

    south_roads = [
        "south_to_center",
        "center_to_south"
    ]

    east_roads = [
        "east_to_center",
        "center_to_east"
    ]

    west_roads = [
        "west_to_center",
        "center_to_west"
    ]

    def average_score(road_list):

        values = []

        for road in road_list:

            if road in scores:
                values.append(
                    scores[road]
                )

        if not values:
            return 0.0

        return sum(values) / len(values)

    north_score = average_score(
        north_roads
    )

    south_score = average_score(
        south_roads
    )

    east_score = average_score(
        east_roads
    )

    west_score = average_score(
        west_roads
    )

    # Combine opposite directions

    north_south_score = (
        north_score + south_score
    ) / 2

    east_west_score = (
        east_score + west_score
    ) / 2

    return (
        north_south_score,
        east_west_score
    )


# ============================================================
# GET ACTUAL TRAFFIC SCORES FROM SUMO
# ============================================================

def get_actual_traffic_scores():

    ns_vehicles = 0
    ew_vehicles = 0

    # Incoming roads
    ns_roads = [
        "north_to_center",
        "south_to_center"
    ]

    ew_roads = [
        "east_to_center",
        "west_to_center"
    ]

    # Count stopped vehicles
    for road in ns_roads:

        ns_vehicles += (
            traci.edge.getLastStepHaltingNumber(
                road
            )
        )

    for road in ew_roads:

        ew_vehicles += (
            traci.edge.getLastStepHaltingNumber(
                road
            )
        )

    total = (
        ns_vehicles +
        ew_vehicles
    )

    # No stopped vehicles
    if total == 0:

        return 0.0, 0.0

    # Convert to normalized scores
    ns_score = (
        ns_vehicles / total
    )

    ew_score = (
        ew_vehicles / total
    )

    return (
        ns_score,
        ew_score
    )


# ============================================================
# CALCULATE GREEN TIME
# ============================================================

def calculate_green_time(score):

    # Keep score between 0 and 1
    score = max(
        0.0,
        min(1.0, score)
    )

    # Convert congestion score
    # into green time

    green_time = (
        MIN_GREEN
        + score * (
            MAX_GREEN - MIN_GREEN
        )
    )

    return round(
        green_time,
        1
    )


# ============================================================
# UPDATE TRAFFIC LIGHT
# ============================================================

def update_traffic_light(
    ns_score,
    ew_score
):

    # Decide priority
    if ns_score >= ew_score:

        priority = "NORTH-SOUTH"

        phase = PHASE_NS

        green_time = calculate_green_time(
            ns_score
        )

    else:

        priority = "EAST-WEST"

        phase = PHASE_EW

        green_time = calculate_green_time(
            ew_score
        )

    print(
        "\n======================================="
    )

    print(
        " ADAPTIVE TRAFFIC DECISION"
    )

    print(
        "======================================="
    )

    print(
        f"North-South score : {ns_score:.3f}"
    )

    print(
        f"East-West score   : {ew_score:.3f}"
    )

    print(
        f"Priority          : {priority}"
    )

    print(
        f"Phase             : {phase}"
    )

    print(
        f"Green time        : {green_time:.1f} seconds"
    )

    # Get current SUMO phase
    current_phase = (
        traci.trafficlight.getPhase(
            TRAFFIC_LIGHT_ID
        )
    )

    # --------------------------------------------------------
    # NORTH-SOUTH GREEN -> EAST-WEST
    # --------------------------------------------------------

    if (
        current_phase == PHASE_NS
        and phase == PHASE_EW
    ):

        # NS green -> NS yellow
        traci.trafficlight.setPhase(
            TRAFFIC_LIGHT_ID,
            1
        )

        traci.trafficlight.setPhaseDuration(
            TRAFFIC_LIGHT_ID,
            3
        )

        print(
            "Transition: "
            "NORTH-SOUTH -> YELLOW -> EAST-WEST"
        )

    # --------------------------------------------------------
    # EAST-WEST GREEN -> NORTH-SOUTH
    # --------------------------------------------------------

    elif (
        current_phase == PHASE_EW
        and phase == PHASE_NS
    ):

        # EW green -> EW yellow
        traci.trafficlight.setPhase(
            TRAFFIC_LIGHT_ID,
            3
        )

        traci.trafficlight.setPhaseDuration(
            TRAFFIC_LIGHT_ID,
            3
        )

        print(
            "Transition: "
            "EAST-WEST -> YELLOW -> NORTH-SOUTH"
        )

    # --------------------------------------------------------
    # SAME DIRECTION
    # --------------------------------------------------------

    else:

        # Apply adaptive green time
        traci.trafficlight.setPhase(
            TRAFFIC_LIGHT_ID,
            phase
        )

        traci.trafficlight.setPhaseDuration(
            TRAFFIC_LIGHT_ID,
            green_time
        )

    print(
        "Traffic light updated."
    )
    CURRENT_STATE["priority"] = priority
    CURRENT_STATE["phase"] = phase
    CURRENT_STATE["green_time"] = green_time

# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n======================================="
    )

    print(
        " SMART TRAFFIC ADAPTIVE CONTROLLER"
    )

    print(
        "======================================="
    )

    # --------------------------------------------------------
    # Load prediction data
    # --------------------------------------------------------

    df = load_predictions()

    prediction_start = float(
        df["timestamp"].min()
    )

    prediction_end = float(
        df["timestamp"].max()
    )

    prediction_duration = (
        prediction_end - prediction_start
    )

    # --------------------------------------------------------
    # Check SUMO configuration
    # --------------------------------------------------------

    if not os.path.exists(
        SUMO_CONFIG
    ):

        raise FileNotFoundError(
            f"SUMO configuration not found:\n"
            f"{SUMO_CONFIG}"
        )

    print(
        f"\nSUMO configuration found:\n"
        f"{SUMO_CONFIG}"
    )

    # --------------------------------------------------------
    # Start SUMO
    # --------------------------------------------------------

    print(
        "\nStarting SUMO..."
    )

    traci.start([SUMO_BINARY, "-c", SUMO_CONFIG])    
    print(
        "TraCI connected."
    )

    try:

        # ----------------------------------------------------
        # Check traffic lights
        # ----------------------------------------------------

        traffic_lights = (
            traci.trafficlight.getIDList()
        )

        print(
            f"Traffic lights detected: "
            f"{traffic_lights}"
        )

        if (
            TRAFFIC_LIGHT_ID
            not in traffic_lights
        ):

            raise RuntimeError(
                f"Traffic light "
                f"'{TRAFFIC_LIGHT_ID}' "
                f"was not found in SUMO."
            )

        print(
            f"Traffic light "
            f"'{TRAFFIC_LIGHT_ID}' found."
        )

        # ----------------------------------------------------
        # Run simulation
        # ----------------------------------------------------

        last_control_time = (
            -CONTROL_INTERVAL
        )

        while (
            traci.simulation.getMinExpectedNumber() > 0
            and traci.simulation.getTime()
            < SIMULATION_END
        ):

            
# Advance SUMO in real time
            traci.simulationStep()
            time.sleep(1)
            traci.simulation.setScale(1.0)
            simulation_time = (
                traci.simulation.getTime()
            )

            CURRENT_STATE["simulation_time"] = simulation_time
            write_state()
            # ------------------------------------------------
            # Adaptive control
            # ------------------------------------------------

            if (
                simulation_time
                - last_control_time
                >= CONTROL_INTERVAL
            ):

                # Get prediction
                (
                    scores,
                    prediction_timestamp,
                    target_prediction_time,
                    prediction_end
                ) = get_current_scores(
                    df,
                    simulation_time
                )

                print(
                    f"\nSimulation time: "
                    f"{simulation_time:.1f}s"
                )

                print(
                    f"Target prediction time: "
                    f"{target_prediction_time:.1f}"
                )

                print(
                    f"Prediction timestamp used: "
                    f"{prediction_timestamp:.1f}"
                )

                # ------------------------------------------------
                # Calculate predicted congestion
                # ------------------------------------------------

                (
                    predicted_ns,
                    predicted_ew
                ) = calculate_direction_scores(
                    scores
                )

                # ------------------------------------------------
                # Get actual SUMO traffic
                # ------------------------------------------------

                (
                    actual_ns,
                    actual_ew
                ) = get_actual_traffic_scores()

                print(
                    f"Predicted NS score : "
                    f"{predicted_ns:.3f}"
                )

                print(
                    f"Predicted EW score : "
                    f"{predicted_ew:.3f}"
                )

                CURRENT_STATE["prediction"]["ns"] = predicted_ns
                CURRENT_STATE["prediction"]["ew"] = predicted_ew

                print(
                    f"Actual NS score    : "
                    f"{actual_ns:.3f}"
                )

                print(
                    f"Actual EW score    : "
                    f"{actual_ew:.3f}"
                )
                CURRENT_STATE["actual"]["ns"] = actual_ns
                CURRENT_STATE["actual"]["ew"] = actual_ew
                # ------------------------------------------------
                # Combine prediction + actual traffic
                #
                # 60% prediction
                # 40% actual traffic
                # ------------------------------------------------

                ns_score = (
                    0.6 * predicted_ns
                    + 0.4 * actual_ns
                )

                ew_score = (
                    0.6 * predicted_ew
                    + 0.4 * actual_ew
                )

                print(
                    f"Final NS score     : "
                    f"{ns_score:.3f}"
                )

                print(
                    f"Final EW score     : "
                    f"{ew_score:.3f}"
                )
                CURRENT_STATE["final"]["ns"] = ns_score
                CURRENT_STATE["final"]["ew"] = ew_score
                # ------------------------------------------------
                # Update traffic signal
                # ------------------------------------------------

                update_traffic_light(
                    ns_score,
                    ew_score
                )
                write_state()
                last_control_time = (
                    simulation_time
                )

    finally:

        print(
            "\nClosing SUMO..."
        )

        traci.close()

        print(
            "SUMO closed."
        )

        print(
            "Adaptive controller finished."
        )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()





