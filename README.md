# Smart Traffic Signal Optimization

A simulation-based smart traffic project that compares fixed-time and adaptive traffic-signal control at an intersection. The repository includes a SUMO traffic simulation, a Python controller, a Flask API, and a browser-based dashboard.

## Project Overview

Fixed-time signals use preset timings even when traffic conditions change. This project explores an adaptive approach that uses congestion scores to choose which direction receives priority and how long its green phase should last.

The project is built around **SUMO** for traffic simulation and **TraCI** for Python-to-SUMO control.

## Components

- **SUMO simulation:** Network and trip/queue output files for fixed-time and adaptive runs.
- **Adaptive controller:** `sumo/adaptive_controller.py` reads prediction data, combines road-level congestion scores into north–south and east–west scores, and selects a priority direction.
- **Adaptive green timing:** The controller maps the selected congestion score to a green duration bounded by 20 and 90 seconds.
- **Flask API:** `backend/app.py` exposes endpoints to read simulation state and start, stop, reset, or check the controller status.
- **Browser dashboard:** The `frontend/` folder contains the HTML, CSS, and JavaScript interface.

## Simulation Results

The committed `sumo/results.md` reports the following comparison between fixed-time and adaptive control:

| Metric | Fixed-time | Adaptive | Reported change |
|---|---:|---:|---:|
| Average waiting time | 8.61 | 4.96 | 42.40% lower |
| Average queue length | 13.19 | 7.42 | 43.73% lower |
| Average travel time | 91.60 | 87.84 | 4.11% lower |
| Throughput | 70 | 79 | 12.86% higher |

These figures are the values recorded in the repository's results file. They describe this simulation run and should not be interpreted as guaranteed real-world improvements.

## Tech Stack

- Python
- SUMO and TraCI
- pandas
- Flask
- HTML, CSS, and JavaScript
- XML-based SUMO network and simulation files

## Repository Structure

- `backend/app.py` — Flask API for simulation state and controller lifecycle
- `frontend/` — browser interface
- `sumo/adaptive_controller.py` — adaptive traffic controller
- `sumo/evaluate.py` — parses SUMO trip and queue outputs and calculates comparison metrics
- `sumo/results.md` — recorded simulation comparison

## Running Notes

The controller expects SUMO to be installed and configured, and it reads a prediction CSV at `sumo/traffic_prediction.csv`. Its SUMO configuration path is `sumo/traffic.sumocfg`. Before running, verify that the required CSV and SUMO configuration/network files are present in your local checkout and that the SUMO executable is available on your system.

The Flask backend can be started from the repository root with:

```bash
python backend/app.py
```

It listens on `127.0.0.1:5000` by default. The controller and dashboard require the relevant simulation dependencies and local files to be configured.

## Scope

This repository demonstrates adaptive signal logic and evaluation in a simulated intersection. It is a simulation project, not a deployed traffic-control system.