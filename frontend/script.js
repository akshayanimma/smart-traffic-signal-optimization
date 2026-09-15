/* ============================================================
   SMART TRAFFIC SIGNAL OPTIMIZATION
   Frontend Simulation Controller
============================================================ */


/* ============================================================
   CONFIGURATION
============================================================ */

const SIMULATION_END = 218;


/*
    Recorded outputs from the adaptive controller.

    ns / ew      = predicted traffic intensity
    priority     = controller-selected direction
    green        = selected green duration
*/

const snapshots = [

    {
        time: 1,
        ns: 0.348,
        ew: 0.469,
        priority: "EW",
        green: 39.7
    },

    {
        time: 21,
        ns: 0.265,
        ew: 0.471,
        priority: "EW",
        green: 39.8
    },

    {
        time: 41,
        ns: 0.629,
        ew: 0.380,
        priority: "NS",
        green: 46.4
    },

    {
        time: 61,
        ns: 0.502,
        ew: 0.143,
        priority: "EW",
        green: 54.0
    },

    {
        time: 81,
        ns: 0.605,
        ew: 0.316,
        priority: "NS",
        green: 73.4
    },

    {
        time: 101,
        ns: 0.348,
        ew: 0.452,
        priority: "EW",
        green: 67.0
    },

    {
        time: 121,
        ns: 0.244,
        ew: 0.562,
        priority: "NS",
        green: 58.3
    },

    {
        time: 141,
        ns: 0.600,
        ew: 0.290,
        priority: "EW",
        green: 60.2
    },

    {
        time: 161,
        ns: 0.155,
        ew: 0.040,
        priority: "NS",
        green: 54.5
    },

    {
        time: 181,
        ns: 0.216,
        ew: 0.247,
        priority: "EW",
        green: 58.4
    },

    {
        time: 201,
        ns: 0.047,
        ew: 0.187,
        priority: "NS",
        green: 50.0
    }

];


/* ============================================================
   STATE
============================================================ */

let simulationTime = 0;

let simulationRunning = false;

let simulationInterval = null;

let vehicleAnimationFrame = null;

let lastVehicleFrameTime = null;


/* ============================================================
   VEHICLE CONFIGURATION
============================================================ */

const VEHICLE_STOP_POINT = 0.40;

const VEHICLE_CROSS_POINT = 0.52;

const VEHICLE_EXIT_POINT = 1.10;

const VEHICLE_SPEED = 0.09;

const VEHICLE_SPACING = 0.075;


/* ============================================================
   VEHICLE STATE
============================================================ */

const vehicleStates = {

    ns: [],

    ew: []

};


/* ============================================================
   DOM ELEMENTS
============================================================ */

const simulationTimeElement =
    document.getElementById(
        "simulationTime"
    );


const simulationProgress =
    document.getElementById(
        "simulationProgress"
    );


const startBtn =
    document.getElementById(
        "startBtn"
    );


const pauseBtn =
    document.getElementById(
        "pauseBtn"
    );


const resetBtn =
    document.getElementById(
        "resetBtn"
    );


const simulationStatus =
    document.getElementById(
        "simulationStatus"
    );


const clock =
    document.getElementById(
        "clock"
    );


const nsValue =
    document.getElementById(
        "nsValue"
    );


const ewValue =
    document.getElementById(
        "ewValue"
    );


const nsBar =
    document.getElementById(
        "nsBar"
    );


const ewBar =
    document.getElementById(
        "ewBar"
    );


const currentPhase =
    document.getElementById(
        "currentPhase"
    );


const greenDuration =
    document.getElementById(
        "greenDuration"
    );


const priority =
    document.getElementById(
        "priority"
    );


const decision =
    document.getElementById(
        "decision"
    );


const redLight =
    document.getElementById(
        "redLight"
    );


const yellowLight =
    document.getElementById(
        "yellowLight"
    );


const greenLight =
    document.getElementById(
        "greenLight"
    );


const nsSignal =
    document.getElementById(
        "nsSignal"
    );


const ewSignal =
    document.getElementById(
        "ewSignal"
    );


const nsVehicles =
    document.getElementById(
        "nsVehicles"
    );


const ewVehicles =
    document.getElementById(
        "ewVehicles"
    );


const nsDensityLabel =
    document.getElementById(
        "nsDensityLabel"
    );


const ewDensityLabel =
    document.getElementById(
        "ewDensityLabel"
    );


/* ============================================================
   CLOCK
============================================================ */

function updateClock() {

    const now =
        new Date();


    const hours =
        String(
            now.getHours()
        ).padStart(
            2,
            "0"
        );


    const minutes =
        String(
            now.getMinutes()
        ).padStart(
            2,
            "0"
        );


    const seconds =
        String(
            now.getSeconds()
        ).padStart(
            2,
            "0"
        );


    clock.textContent =
        `${hours}:${minutes}:${seconds}`;

}


setInterval(
    updateClock,
    1000
);


updateClock();


/* ============================================================
   FIND SNAPSHOT
============================================================ */

function getSnapshotForTime(time) {

    let selected =
        snapshots[0];


    for (
        const snapshot of snapshots
    ) {

        if (
            snapshot.time <= time
        ) {

            selected =
                snapshot;

        }

    }


    return selected;

}


/* ============================================================
   SIMULATION TIME
============================================================ */

function updateSimulationTime() {

    simulationTimeElement.textContent =
        `${simulationTime.toFixed(1)}s`;


    const percentage =
        (
            simulationTime /
            SIMULATION_END
        ) * 100;


    simulationProgress.style.width =
        `${Math.min(
            percentage,
            100
        )}%`;

}


/* ============================================================
   PREDICTION
============================================================ */

function updatePrediction(snapshot) {

    const ns =
        Math.max(
            0,
            Math.min(
                snapshot.ns,
                1
            )
        );


    const ew =
        Math.max(
            0,
            Math.min(
                snapshot.ew,
                1
            )
        );


    nsValue.textContent =
        ns.toFixed(3);


    ewValue.textContent =
        ew.toFixed(3);


    nsBar.style.width =
        `${ns * 100}%`;


    ewBar.style.width =
        `${ew * 100}%`;

}


/* ============================================================
   VEHICLE INITIALIZATION
============================================================ */

function initializeVehicleStates() {

    vehicleStates.ns = [];

    vehicleStates.ew = [];


    const nsCars =
        nsVehicles
            ? nsVehicles.querySelectorAll(
                ".car"
            )
            : [];


    const ewCars =
        ewVehicles
            ? ewVehicles.querySelectorAll(
                ".car"
            )
            : [];


    nsCars.forEach(
        (vehicle, index) => {

            vehicleStates.ns.push({

                element:
                    vehicle,

                position:
                    -0.20 -
                    (
                        index *
                        VEHICLE_SPACING
                    ),

                visible:
                    false,

                crossed:
                    false

            });

        }
    );


    ewCars.forEach(
        (vehicle, index) => {

            vehicleStates.ew.push({

                element:
                    vehicle,

                position:
                    -0.20 -
                    (
                        index *
                        VEHICLE_SPACING
                    ),

                visible:
                    false,

                crossed:
                    false

            });

        }
    );


    renderVehicles();

}


/* ============================================================
   RESET SINGLE VEHICLE
============================================================ */

function resetVehicle(
    state,
    index
) {

    state.position =
        -0.20 -
        (
            index *
            VEHICLE_SPACING
        );


    state.crossed =
        false;

}


/* ============================================================
   RENDER NS VEHICLE
============================================================ */

function renderNSVehicle(state) {

    /*
        North → South
    */

    const y =
        state.position *
        380;


    state.element.style.transform =
        `translateY(${y}px)`;

}


/* ============================================================
   RENDER EW VEHICLE
============================================================ */

function renderEWVehicle(state) {

    /*
        East → West
    */

    const x =
        -state.position *
        520;


    state.element.style.transform =
        `translateX(${x}px)`;

}


/* ============================================================
   RENDER ALL VEHICLES
============================================================ */

function renderVehicles() {

    vehicleStates.ns.forEach(
        renderNSVehicle
    );


    vehicleStates.ew.forEach(
        renderEWVehicle
    );

}


/* ============================================================
   UPDATE VEHICLE
============================================================ */

function updateVehicle(
    state,
    index,
    directionGreen,
    deltaTime,
    states
) {

    if (
        !state.visible
    ) {

        return;

    }


    /*
        --------------------------------------------------------
        VEHICLE HAS ALREADY CROSSED
        --------------------------------------------------------

        Once the vehicle has entered the intersection,
        it must NOT stop because of a signal change.
    */

    if (
        state.crossed
    ) {

        state.position +=
            VEHICLE_SPEED *
            deltaTime;

    }


    /*
        --------------------------------------------------------
        VEHICLE HAS NOT CROSSED
        --------------------------------------------------------
    */

    else {

        /*
            Green signal:
            vehicle can approach and cross.
        */

        if (
            directionGreen
        ) {

            state.position +=
                VEHICLE_SPEED *
                deltaTime;

        }


        /*
            Red signal:
            stop before the intersection.
        */

        else {

            if (
                state.position <
                VEHICLE_STOP_POINT
            ) {

                state.position +=
                    VEHICLE_SPEED *
                    deltaTime;

            }


            /*
                Stop exactly at the stop line.
            */

            if (
                state.position >=
                VEHICLE_STOP_POINT
            ) {

                state.position =
                    VEHICLE_STOP_POINT;

            }

        }

    }


    /*
        Vehicle enters intersection.
    */

    if (
        state.position >=
        VEHICLE_CROSS_POINT
    ) {

        state.crossed =
            true;

    }


    /*
        Vehicle has completely left the screen.

        Recycle it to the beginning of the road.
    */

    if (
        state.position >
        VEHICLE_EXIT_POINT
    ) {

        resetVehicle(
            state,
            index
        );

    }

}


/* ============================================================
   PREVENT VEHICLE OVERLAP
============================================================ */

function enforceVehicleSpacing(
    states
) {

    const visibleVehicles =
        states
            .filter(
                state =>
                    state.visible
            )
            .sort(
                (a, b) =>
                    b.position -
                    a.position
            );


    for (
        let i = 1;
        i < visibleVehicles.length;
        i++
    ) {

        const front =
            visibleVehicles[
                i - 1
            ];


        const behind =
            visibleVehicles[
                i
            ];


        const distance =
            front.position -
            behind.position;


        if (
            distance <
            VEHICLE_SPACING
        ) {

            behind.position =
                front.position -
                VEHICLE_SPACING;

        }

    }

}


/* ============================================================
   VEHICLE ANIMATION LOOP
============================================================ */

function animateVehicles(
    timestamp
) {

    if (
        !simulationRunning
    ) {

        lastVehicleFrameTime =
            null;

        vehicleAnimationFrame =
            null;

        return;

    }


    if (
        lastVehicleFrameTime ===
        null
    ) {

        lastVehicleFrameTime =
            timestamp;

    }


    const deltaTime =
        Math.min(
            (
                timestamp -
                lastVehicleFrameTime
            ) / 1000,
            0.05
        );


    lastVehicleFrameTime =
        timestamp;


    const snapshot =
        getSnapshotForTime(
            simulationTime
        );


    /* --------------------------------------------------------
       NS VEHICLES
    -------------------------------------------------------- */

    vehicleStates.ns.forEach(
        (
            state,
            index
        ) => {

            updateVehicle(
                state,
                index,
                snapshot.priority === "NS",
                deltaTime,
                vehicleStates.ns
            );

        }
    );


    /* --------------------------------------------------------
       EW VEHICLES
    -------------------------------------------------------- */

    vehicleStates.ew.forEach(
        (
            state,
            index
        ) => {

            updateVehicle(
                state,
                index,
                snapshot.priority === "EW",
                deltaTime,
                vehicleStates.ew
            );

        }
    );


    /* --------------------------------------------------------
       SPACING
    -------------------------------------------------------- */

    enforceVehicleSpacing(
        vehicleStates.ns
    );


    enforceVehicleSpacing(
        vehicleStates.ew
    );


    renderVehicles();


    vehicleAnimationFrame =
        requestAnimationFrame(
            animateVehicles
        );

}


/* ============================================================
   START VEHICLE ANIMATION
============================================================ */

function startVehicleAnimation() {

    if (
        vehicleAnimationFrame !==
        null
    ) {

        return;

    }


    lastVehicleFrameTime =
        null;


    vehicleAnimationFrame =
        requestAnimationFrame(
            animateVehicles
        );

}


/* ============================================================
   STOP VEHICLE ANIMATION
============================================================ */

function stopVehicleAnimation() {

    if (
        vehicleAnimationFrame !==
        null
    ) {

        cancelAnimationFrame(
            vehicleAnimationFrame
        );

    }


    vehicleAnimationFrame =
        null;


    lastVehicleFrameTime =
        null;

}


/* ============================================================
   SIGNAL
============================================================ */

function updateSignal(
    snapshot
) {

    const isNS =
        snapshot.priority ===
        "NS";


    const isEW =
        snapshot.priority ===
        "EW";


    /* --------------------------------------------------------
       TEXT
    -------------------------------------------------------- */

    currentPhase.textContent =
        isNS
            ? "NS Green"
            : "EW Green";


    greenDuration.textContent =
        `${snapshot.green.toFixed(1)} sec`;


    priority.textContent =
        isNS
            ? "North–South"
            : "East–West";


    decision.textContent =
        isNS
            ? "NORTH–SOUTH"
            : "EAST–WEST";


    /* --------------------------------------------------------
       SIGNAL INDICATORS
    -------------------------------------------------------- */

    nsSignal.classList.toggle(
        "active",
        isNS
    );


    ewSignal.classList.toggle(
        "active",
        isEW
    );


    /* --------------------------------------------------------
       TRAFFIC LIGHT
    -------------------------------------------------------- */

    redLight.classList.remove(
        "active-light"
    );


    yellowLight.classList.remove(
        "active-light"
    );


    greenLight.classList.remove(
        "active-light"
    );


    greenLight.classList.add(
        "active-light"
    );


    /* --------------------------------------------------------
       INTERSECTION CLASS
    -------------------------------------------------------- */

    const intersection =
        document.getElementById(
            "intersection"
        ) ||
        document.querySelector(
            ".intersection"
        );


    if (
        intersection
    ) {

        intersection.classList.toggle(
            "priority-ns",
            isNS
        );


        intersection.classList.toggle(
            "priority-ew",
            isEW
        );

    }

}


/* ============================================================
   TRAFFIC DENSITY
============================================================ */

/*
    ML intensity is used to determine how many
    incoming vehicles are visible.

    This is NOT an actual SUMO vehicle count.

    0.00 → 0 vehicles
    0.25 → 1 vehicle
    0.50 → 2 vehicles
    0.75 → 3 vehicles
    1.00 → 4 vehicles
*/

function updateTrafficDensity(
    snapshot
) {

    const ns =
        Math.max(
            0,
            Math.min(
                snapshot.ns,
                1
            )
        );


    const ew =
        Math.max(
            0,
            Math.min(
                snapshot.ew,
                1
            )
        );


    const nsCars =
        Math.ceil(
            ns * 4
        );


    const ewCars =
        Math.ceil(
            ew * 4
        );


    /* --------------------------------------------------------
       NS VEHICLES
    -------------------------------------------------------- */

    vehicleStates.ns.forEach(
        (
            state,
            index
        ) => {

            const shouldShow =
                index <
                nsCars;


            /*
                If a previously hidden vehicle becomes
                active again, place it back at the entrance.
            */

            if (
                shouldShow &&
                !state.visible
            ) {

                resetVehicle(
                    state,
                    index
                );

            }


            state.visible =
                shouldShow;


            state.element.style.display =
                shouldShow
                    ? "block"
                    : "none";

        }
    );


    /* --------------------------------------------------------
       EW VEHICLES
    -------------------------------------------------------- */

    vehicleStates.ew.forEach(
        (
            state,
            index
        ) => {

            const shouldShow =
                index <
                ewCars;


            if (
                shouldShow &&
                !state.visible
            ) {

                resetVehicle(
                    state,
                    index
                );

            }


            state.visible =
                shouldShow;


            state.element.style.display =
                shouldShow
                    ? "block"
                    : "none";

        }
    );


    /* --------------------------------------------------------
       DENSITY LABELS
    -------------------------------------------------------- */

    nsDensityLabel.textContent =
        `NS Density ${
            (ns * 100).toFixed(0)
        }%`;


    ewDensityLabel.textContent =
        `EW Density ${
            (ew * 100).toFixed(0)
        }%`;


    nsDensityLabel.classList.toggle(
        "high",
        ns >= 0.6
    );


    ewDensityLabel.classList.toggle(
        "high",
        ew >= 0.6
    );

}


/* ============================================================
   UPDATE DASHBOARD
============================================================ */

function updateDashboard() {

    const snapshot =
        getSnapshotForTime(
            simulationTime
        );


    updatePrediction(
        snapshot
    );


    updateSignal(
        snapshot
    );


    updateTrafficDensity(
        snapshot
    );


    renderVehicles();

}


/* ============================================================
   START SIMULATION
============================================================ */

function startSimulation() {

    if (
        simulationRunning
    ) {

        return;

    }


    if (
        simulationTime >=
        SIMULATION_END
    ) {

        simulationTime =
            0;

        initializeVehicleStates();

        updateDashboard();

    }


    simulationRunning =
        true;


    simulationStatus.textContent =
        "Simulation Running";


    startBtn.disabled =
        true;


    pauseBtn.disabled =
        false;


    /* Start smooth vehicle movement */

    startVehicleAnimation();


    /*
        Advance simulation every 100 ms.

        0.1 simulation seconds per 100 ms
        = 1 simulation second per real second.
    */

    simulationInterval =
        setInterval(
            () => {

                simulationTime +=
                    0.1;


                if (
                    simulationTime >=
                    SIMULATION_END
                ) {

                    simulationTime =
                        SIMULATION_END;


                    updateSimulationTime();

                    updateDashboard();


                    stopSimulation();


                    simulationStatus.textContent =
                        "Simulation Complete";


                    return;

                }


                updateSimulationTime();

                updateDashboard();

            },
            100
        );

}


/* ============================================================
   PAUSE
============================================================ */

function pauseSimulation() {

    if (
        !simulationRunning
    ) {

        return;

    }


    clearInterval(
        simulationInterval
    );


    simulationInterval =
        null;


    simulationRunning =
        false;


    stopVehicleAnimation();


    simulationStatus.textContent =
        "Simulation Paused";


    startBtn.disabled =
        false;


    pauseBtn.disabled =
        true;

}


/* ============================================================
   STOP
============================================================ */

function stopSimulation() {

    clearInterval(
        simulationInterval
    );


    simulationInterval =
        null;


    simulationRunning =
        false;


    stopVehicleAnimation();


    startBtn.disabled =
        false;


    pauseBtn.disabled =
        true;

}


/* ============================================================
   RESET
============================================================ */

function resetSimulation() {

    stopSimulation();


    simulationTime =
        0;


    initializeVehicleStates();


    simulationStatus.textContent =
        "Simulation Ready";


    updateSimulationTime();

    updateDashboard();


    startBtn.disabled =
        false;


    pauseBtn.disabled =
        true;

}


/* ============================================================
   BUTTON EVENTS
============================================================ */

startBtn.addEventListener(
    "click",
    startSimulation
);


pauseBtn.addEventListener(
    "click",
    pauseSimulation
);


resetBtn.addEventListener(
    "click",
    resetSimulation
);


/* ============================================================
   NAVIGATION ACTIVE STATE
============================================================ */

const navItems =
    document.querySelectorAll(
        ".nav-item"
    );


navItems.forEach(
    item => {

        item.addEventListener(
            "click",
            () => {

                navItems.forEach(
                    nav =>
                        nav.classList.remove(
                            "active"
                        )
                );


                item.classList.add(
                    "active"
                );

            }
        );

    }
);


/* ============================================================
   INITIALIZATION
============================================================ */

pauseBtn.disabled =
    true;


initializeVehicleStates();


updateSimulationTime();


updateDashboard();