# Modern Power Grid & Wide-Area SCADA — Model Writeup

## Overview

[Power_Grid_SCADA_Composed.mp](file:///d:/Research/NSA%20INSuRE+C/Summer/May/Power_Grid_SCADA_Composed.mp) is a Monterey Phoenix (MP) behavior-trace model representing a transmission and distribution power grid. It models the ultra-fast cyber-physical interactions between high-voltage physics and protective automation.

The model contains **8 ROOT components**, **31 top-level states**, **~50 sub-events**, **4 ordering constraints**, **9 presence constraints**, and **4 coordination blocks**.

---

## Source Documentation

The logic and components are grounded in industrial control system (ICS) and power engineering standards:

| Ref ID | Document | What it provided |
|--------|----------|-----------------|
| **D1** | **IEC 61850** | International standard for Substation Automation. Defines **GOOSE** (Generic Object Oriented Substation Event) for ultra-fast peer-to-peer relay tripping, and **MMS** for SCADA reporting. |
| **D2** | **IEEE 1815 (DNP3)** | Distributed Network Protocol. The primary North American standard for SCADA telemetry (polling/responses) between substations and control centers. |
| **D3** | **Power System Protection Principles** | Defines the physical sequence of fault clearing: Fault $\rightarrow$ Relay Pickup $\rightarrow$ Trip Command $\rightarrow$ Breaker Coil Energized $\rightarrow$ Arc Extinguished. |

---

## Components

### 1. Generation_Plant (4 states)
**Mapping:** A power plant (e.g., natural gas, nuclear, or hydro).
- `baseload_running`: Nominal operation, synchronized to the grid AC frequency.
- `ramping_up` / `peaking_plant_active`: Adjusting output to meet demand.
- `tripped_offline`: Protection systems automatically shut down the generator, causing grid frequency to drop.

### 2. Substation_Relay_IED (4 states)
**Mapping:** Intelligent Electronic Device (IED). The digital "brain" of the substation that monitors current/voltage.
- `ied_monitoring`: Nominal state; sampling transformers and sending MMS reports to SCADA (D1).
- `ied_overcurrent_detected`: Senses a fault (protection pickup).
- `ied_issuing_goose_trip`: Publishes a multicast GOOSE packet to trip a breaker (D1).
- `ied_locked_out`: Breaker failed to clear the fault; relay locks out to prevent reclosing onto a short circuit.

### 3. Substation_Breaker (4 states)
**Mapping:** High-voltage circuit breaker. The "muscle" of the substation.
- `breaker_closed`: Contacts closed, power flowing.
- `breaker_opening`: The trip coil is energized, contacts are parting, and a high-voltage arc is present.
- `breaker_open`: Arc extinguished, circuit broken.
- `breaker_failure_to_trip`: A critical mechanical failure.

### 4. SCADA_Control_Center (4 states)
**Mapping:** The utility's Energy Management System (EMS).
- `ems_nominal`: State estimation algorithm converged based on DNP3 polling (D2).
- `ems_agc_active`: Automatic Generation Control balancing load and generation.
- `ems_load_shedding`: Drastic measure to prevent total blackout by cutting power to specific areas.
- `scada_blind`: Telemetry lost; operators cannot see grid state.

### 5. Transmission_Line (4 states)
**Mapping:** The high-voltage physics of the grid.
- `line_nominal` / `line_overloaded`: Operating within or beyond thermal limits (sagging lines).
- `line_faulted`: A short circuit (e.g., lightning strike, tree contact).
- `line_de_energized`: Successfully isolated by breakers.

### 6. Distribution_Network (4 states)
**Mapping:** The local grid feeding neighborhoods.
- `dist_nominal` / `dist_peak_load` / `dist_feeder_fault`.
- `microgrid_islanded`: A modern neighborhood disconnecting from a dead transmission grid and surviving on local solar/batteries.

### 7. Comm_Network (3 states)
**Mapping:** The Operational Technology (OT) fiber/microwave network.
- `ot_net_nominal` / `ot_net_congested` / `ot_net_partitioned` (link severed).

### 8. Smart_Meter_AMI (4 states)
**Mapping:** Advanced Metering Infrastructure on homes.
- `ami_reporting` / `ami_demand_response` / `ami_disconnect_active` / `ami_blackout_detected` ("last gasp" message).

---

## Constraints & Physics Rules

The constraints model the harsh realities of power engineering:

### Fault Clearing Sequence (ENSURE FOREACH & COORDINATE)
The model enforces the strict causal chain of clearing a fault:
1. `high_fault_current` (Line) PRECEDES `protection_pickup` (Relay).
2. `protection_pickup` (Relay) PRECEDES `publishing_goose_message` (Relay).
3. `publishing_goose_message` (Relay) PRECEDES `trip_coil_energized` (Breaker).
4. `trip_coil_energized` (Breaker) PRECEDES `contacts_open` (Breaker).

### Cascading Failures (REJECT)
- **Breaker Failure Logic:** If a line is faulted (`line_faulted`) but the breaker mechanism gets stuck (`breaker_failure_to_trip`), the model REJECTS any trace where the line becomes `line_de_energized`. The fault remains on the system.
- **Generator Trip:** If a fault is left on the system (due to breaker failure), the massive mechanical stress will force the `Generation_Plant` to trip offline (`tripped_offline`). Traces where the plant survives a breaker failure are REJECTED.

### Cyber-Physical Dependencies (REJECT)
- **OT Network Criticality:** The IED cannot issue a GOOSE trip if the OT network is partitioned. (IEC 61850 relies entirely on the Ethernet LAN).
- **SCADA Blindness:** If the OT network is partitioned, SCADA MUST enter the `scada_blind` state.

---

## Relevance to Differential Analysis

The power grid is the ultimate example of a system where localized failures cascade into massive emergent behavior (blackouts). 

By analyzing the traces of this model:
- **Precedence Violations:** You can detect scenarios where a breaker opens *without* a GOOSE message (indicating a physical malfunction or cyber attack).
- **Co-occurrence Analysis:** The statistical link between `ot_net_congested` (packet loss) and `breaker_failure_to_trip` will emerge, showing how cyber degradation causes physical destruction.
- **Emergent Behavior Identification:** Scenarios where a single `dist_feeder_fault` spirals into `ems_load_shedding` because of a latent misconfiguration in the `Substation_Relay_IED` are classic examples of emergent SoS failures.
