# Connected Autonomous Vehicle (V2X) System-of-Systems — Model Writeup

## Overview

[Connected_Street_V2X_Composed.mp](file:///d:/Research/NSA%20INSuRE+C/Summer/May/Connected_Street_V2X_Composed.mp) is a Monterey Phoenix (MP) behavior-trace model of a "Smart Street" ecosystem, composed as a **system of systems (SoS)**. It models the intricate, high-speed interactions between autonomous vehicles, smart infrastructure, edge servers, and pedestrians.

The model contains **8 ROOT components**, **35 top-level states**, **~60 sub-events**, **6 ordering constraints**, **12 presence constraints**, and **5 coordination blocks**.

---

## Source Documentation

Every component and rule is grounded in real automotive and intelligent transportation systems (ITS) standards:

| Ref ID | Document | What it provided |
|--------|----------|-----------------|
| **D1** | **SAE J2735** | DSRC Message Set Dictionary. Defines the core V2X messages: **BSM** (Basic Safety Message), **SPaT** (Signal Phase and Timing), **MAP** (Intersection Geometry), **TIM** (Traveler Information), **SRM** (Signal Request), **PSM** (Personal Safety Message). |
| **D2** | **NTCIP 1202** | Actuated Signal Controller (ASC) Interface Protocol. Standard for traffic light states, phases, overlaps, and preemption/priority logic. |
| **D3** | **ETSI TS 102 894** | European ITS standards for Cooperative Awareness. Provides the basis for **DENM** (Decentralized Environmental Notification Message) hazard broadcasts. |
| **D4** | **SAE J3016** | Taxonomy and Definitions for Terms Related to Driving Automation Systems. Defines the perception-planning-control pipeline for Level 4/5 AVs. |
| **D5** | **3GPP C-V2X** | Cellular V2X architecture, dictating how Edge Servers (MEC) interact with local vehicle networks. |

---

## Components

### 1. AV_Kinematics (5 states)
**Mapping:** The physical motion and actuator state of the Autonomous Vehicle (longitudinal/lateral control).
- `av_cruising` / `av_accelerating` / `av_stopped`: Nominal motion states.
- `av_braking_normal`: Controlled deceleration using service brakes.
- `av_braking_emergency`: Activation of AEB (Automatic Emergency Braking) and ABS for maximum deceleration.

### 2. AV_Compute (4 states)
**Mapping:** The Level 4/5 Automated Driving System (ADS) software pipeline (Perception $\rightarrow$ Planning).
- `perception_clear`: Nominal state; sensor fusion (LiDAR + Camera) generates a clear planned trajectory (D4).
- `object_detected`: Routine obstacle classification resulting in a trajectory adjustment (e.g., lane change).
- `collision_predicted`: The critical state where the Time-To-Collision (TTC) algorithm breaches safety thresholds, triggering an evasive trajectory plan.
- `sensor_degraded`: Fallback state when physical sensors are blinded (e.g., heavy rain, glare).

### 3. AV_V2X_OBU (4 states)
**Mapping:** The On-Board Unit (OBU) handling DSRC or C-V2X communications (D1, D5).
- `obu_tx_rx_active`: Standard operational mode. Broadcasting BSMs at 10Hz and receiving SPaT/MAP data from intersections.
- `obu_cooperative_perception`: Advanced mode where raw sensor data is shared directly with other entities.
- `obu_rx_only`: Passive listening mode (e.g., stealth mode or transmission failure).
- `obu_isolated`: Complete loss of V2X network connectivity.

### 4. Traffic_Signal (4 states)
**Mapping:** The physical traffic lights at an intersection.
- `phase_green` / `phase_yellow` / `phase_red`: Standard NTCIP 1202 signal indications.
- `overlap_active`: Specific NTCIP 1202 state allowing a protected turn movement independent of the main phase.

### 5. Traffic_Controller (4 states)
**Mapping:** The digital brain in the metal cabinet at the intersection, running NTCIP 1202 logic (D2).
- `tc_coord_normal`: Running standard coordinated timing patterns.
- `tc_transit_priority`: Transit Signal Priority (TSP) active, slightly extending a green phase for a bus.
- `tc_preempt_active`: Hard override. Active phases are terminated and forced into a dwell state to let a fire truck pass.
- `tc_flash_fault`: Malfunction Management Unit (MMU) detects a hardware fault and drops the intersection to flashing red.

### 6. MEC_Server (4 states)
**Mapping:** Multi-access Edge Computing node located near the intersection to process V2X data with ultra-low latency (D5).
- `mec_monitoring_normal`: Ingesting vehicle BSMs and publishing standard TIMs.
- `mec_hazard_broadcasting`: Fusing V2X data to detect a hazard and broadcasting a DENM to warn approaching cars (D3).
- `mec_platoon_coordinating`: Managing aerodynamic vehicle platoons to improve throughput.

### 7. Vulnerable_User (4 states)
**Mapping:** A pedestrian or cyclist carrying a V2X-enabled smartphone or wearable (D1).
- `vru_safe_distance` / `vru_crossing_active` / `vru_in_roadway`: States dictated by physical location. All active states broadcast a PSM (Personal Safety Message) at 1Hz.
- `vru_device_offline`: Pedestrian without V2X capability (dark target).

### 8. Emergency_Vehicle (3 states)
**Mapping:** Fire engine, ambulance, or police cruiser with V2X priority hardware (D1, D2).
- `ev_responding`: Lights/sirens active. Broadcasts high-priority BSMs and specific Signal Request Messages (SRM) to force the traffic controller into `tc_preempt_active`.

---

## Constraints (ENSURE FOREACH & REJECT)

The rules of this model enforce the physics of driving and the strict state machines of ITS protocols.

### Physical & Compute Invariants (REJECT)
- **AEB Requires Prediction:** `av_braking_emergency` cannot occur unless the compute layer is in `collision_predicted`.
- **No Cruising While Crashing:** The vehicle cannot be in `av_cruising` if `collision_predicted` is active.
- **Sensor Blindness:** The vehicle cannot cruise normally if `sensor_degraded` is active; it must adapt its kinematics.
- **Trajectory Logic:** `trajectory_adjusted` requires either an `object_detected` or a `collision_predicted`.

### NTCIP 1202 Controller Logic (ENSURE & REJECT)
- **Preemption Sequence:** `preempt_call_received` $\rightarrow$ `active_phase_terminated` $\rightarrow$ `dwell_state_active`. This exact temporal sequence is mandated by NTCIP 1202 to safely clear an intersection for a fire truck.
- **Mutual Exclusion:** Normal coordination (`tc_coord_normal`) is impossible while preemption (`tc_preempt_active`) is running.
- **Fault Failsafe:** A traffic signal cannot show `phase_green` if the controller is in `tc_flash_fault`.
- **Preemption Authentication:** A controller cannot enter `tc_preempt_active` without a valid request from an `ev_responding`.

### V2X Network Dependencies (ENSURE & REJECT)
- **OBU Isolation:** A vehicle cannot receive SPaT messages or engage in cooperative perception if its OBU is isolated.
- **Hazard Causality:** An edge server (MEC) cannot broadcast a hazard warning (`mec_hazard_broadcasting`) unless there is a valid trigger in the ecosystem (e.g., EV responding, VRU in roadway, or AV predicting a collision).
- **Hazard Sequence:** The hazard must be detected before the DENM warning is published.

### Intersection Safety Envelopes (REJECT)
- **Red Light Obedience:** Assuming a functional V2X system, an AV cannot cruise through an intersection (`av_cruising`) if the signal is `phase_red` AND the AV successfully received the `rx_spat` message. *(If this rule is violated in reality, it constitutes emergent failure).*
- **Pedestrian Safety:** An AV cannot accelerate if a VRU is jaywalking (`vru_in_roadway`), assuming the VRU's device is online and the AV's OBU is not isolated.

---

## Coordination Blocks (PRECEDES)

These five blocks map the critical wireless data exchanges across the SoS:

1. **V2I (Infrastructure to Vehicle):** Traffic Controller running a pattern $\rightarrow$ OBU receives SPaT.
2. **V2I (Vehicle to Infrastructure):** Emergency Vehicle transmits SRM $\rightarrow$ Traffic Controller receives preemption call.
3. **V2N (Pedestrian to Network):** VRU transmits PSM $\rightarrow$ MEC Server ingests the data.
4. **I2V (Edge to Vehicle):** MEC Server publishes DENM hazard $\rightarrow$ AV OBU receives cooperative sensor data.
5. **Internal AV (Compute to Actuation):** Compute plans evasive trajectory $\rightarrow$ Kinematics activates AEB.

---

## Relevance to Differential Analysis

This model is an ideal candidate for scale testing and differential analysis because it bridges the **cyber** (V2X packets, compute states) and **physical** (vehicle kinematics, traffic lights) domains. 

By comparing unconstrained and constrained traces of this model:
- **Precedence Violations:** You can identify scenarios where a traffic light turns green *before* the intersecting preemption dwell state has cleared.
- **Co-occurrence Lift:** You can analyze the statistical dependency between an isolated OBU (`obu_isolated`) and emergency braking (`av_braking_emergency`) when a pedestrian is in the roadway.
- **Emergent Behavior Identification:** Traces where a vehicle enters the intersection despite a conflicting phase—due to latency, sensor degradation, or contradictory V2X inputs—represent the exact class of emergent behaviors your INSuRE+C project is designed to detect.
