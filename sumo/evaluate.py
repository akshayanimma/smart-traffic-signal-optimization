import xml.etree.ElementTree as ET


# --------------------------------------------------
# Read TripInfo XML
# --------------------------------------------------

def read_tripinfo(filename):

    tree = ET.parse(filename)
    root = tree.getroot()

    travel_times = []
    waiting_times = []

    for trip in root.findall("tripinfo"):

        travel_time = float(trip.get("duration", 0))
        waiting_time = float(trip.get("waitingTime", 0))

        travel_times.append(travel_time)
        waiting_times.append(waiting_time)

    if len(travel_times) == 0:
        return 0, 0, 0

    avg_travel_time = sum(travel_times) / len(travel_times)
    avg_waiting_time = sum(waiting_times) / len(waiting_times)

    throughput = len(travel_times)

    return avg_waiting_time, avg_travel_time, throughput


# --------------------------------------------------
# Read Queue XML
# --------------------------------------------------

def read_queue(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    queue_values = []

    for lane in root.findall(".//lane"):
        queue = float(lane.get("queueing_length", 0))
        queue_values.append(queue)

    if not queue_values:
        return 0

    return sum(queue_values) / len(queue_values)

# --------------------------------------------------
# Calculate percentage improvement
# --------------------------------------------------

def improvement(old, new):

    if old == 0:
        return 0

    return ((old - new) / old) * 100


def throughput_improvement(old, new):

    if old == 0:
        return 0

    return ((new - old) / old) * 100


# --------------------------------------------------
# Fixed-Time results
# --------------------------------------------------

fixed_waiting, fixed_travel, fixed_throughput = \
    read_tripinfo("fixed_tripinfo.xml")

fixed_queue = read_queue("fixed_queue.xml")


# --------------------------------------------------
# Adaptive results
# --------------------------------------------------

adaptive_waiting, adaptive_travel, adaptive_throughput = \
    read_tripinfo("adaptive_tripinfo.xml")

adaptive_queue = read_queue("adaptive_queue.xml")


# --------------------------------------------------
# Calculate improvements
# --------------------------------------------------

waiting_improvement = improvement(
    fixed_waiting,
    adaptive_waiting
)

queue_improvement = improvement(
    fixed_queue,
    adaptive_queue
)

travel_improvement = improvement(
    fixed_travel,
    adaptive_travel
)

throughput_improvement_value = throughput_improvement(
    fixed_throughput,
    adaptive_throughput
)


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\n==============================================")
print("      FIXED-TIME vs ADAPTIVE SIGNAL")
print("==============================================\n")

print(f"{'Metric':<25}{'Fixed-Time':>15}{'Adaptive':>15}{'Improvement':>15}")
print("-" * 70)

print(
    f"{'Average Waiting Time':<25}"
    f"{fixed_waiting:>15.2f}"
    f"{adaptive_waiting:>15.2f}"
    f"{waiting_improvement:>14.2f}%"
)

print(
    f"{'Average Queue Length':<25}"
    f"{fixed_queue:>15.2f}"
    f"{adaptive_queue:>15.2f}"
    f"{queue_improvement:>14.2f}%"
)

print(
    f"{'Average Travel Time':<25}"
    f"{fixed_travel:>15.2f}"
    f"{adaptive_travel:>15.2f}"
    f"{travel_improvement:>14.2f}%"
)

print(
    f"{'Throughput':<25}"
    f"{fixed_throughput:>15}"
    f"{adaptive_throughput:>15}"
    f"{throughput_improvement_value:>14.2f}%"
)

print("\n==============================================")