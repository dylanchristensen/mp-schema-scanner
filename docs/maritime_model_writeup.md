# Global Maritime Tracking and Port Logistics — Model Writeup

## Overview

[Maritime_Port_Logistics_Composed.mp](file:///d:/Research/NSA%20INSuRE+C/Summer/May/Maritime_Port_Logistics_Composed.mp) is a Monterey Phoenix (MP) behavior-trace model representing a maritime ecosystem. It covers the cyber-physical interactions between a large cargo vessel, shore-based Vessel Traffic Services (VTS), automated port terminals, and environmental factors.

The model contains **8 ROOT components**, **33 top-level states**, **~55 sub-events**, **4 ordering constraints**, **11 presence constraints**, and **5 coordination blocks**.

---

## Source Documentation

The rules and states in this model are grounded in international maritime law and technical standards:

| Ref ID | Document | What it provided |
|--------|----------|-----------------|
| **D1** | **ITU-R M.1371** | Technical characteristics of the Automatic Identification System (AIS). Defines Message 1 (Dynamic) and Message 5 (Static/Voyage) structures. |
| **D2** | **IMO COLREGs** | International Regulations for Preventing Collisions at Sea. Defines Rule 16 (Give-way vessel) and Rule 17 (Stand-on vessel) behaviors. |
| **D3** | **IALA VTS Manual** | Guidelines for Vessel Traffic Services; how shore-based radar interacts with vessel navigation. |
| **D4** | **NMEA 0183/2000** | Marine electronics interface standards; dictates how GNSS data feeds ECDIS and AIS. |

---

## Components

### 1. Vessel_Kinematics (6 states)
**Mapping:** The physical motion and maneuvering state of a large commercial vessel.
- `vessel_cruising` / `vessel_altering_course` / `vessel_stopping`: Open-water maneuvers.
- `vessel_maneuvering_port`: Slow-speed operations requiring bow thrusters.
- `vessel_moored` / `vessel_anchored`: Static states (docked vs. anchored).

### 2. Vessel_Navigation (5 states)
**Mapping:** The bridge decision-making logic, governed by human crew and the Electronic Chart Display and Information System (ECDIS).
- `ecdis_nominal`: Standard route monitoring with ARPA radar tracking.
- `colregs_stand_on`: Rule 17 requires maintaining course/speed unless a collision is imminent (action in extremis).
- `colregs_give_way`: Rule 16 requires early evasive action.
- `pilot_onboard`: Harbor pilot directing port maneuvers.
- `nav_degraded`: Fallback to manual plotting when electronics fail.

### 3. Vessel_AIS (4 states)
**Mapping:** The VHF AIS transponder (D1).
- `ais_tx_rx_active`: Standard operation transmitting Msg 1 (position) and Msg 5 (static).
- `ais_rx_only`: Stealth or degraded mode.
- `ais_transmitting_error`: Transmitting corrupt data (e.g., due to gyrocompass or GNSS failure).
- `ais_offline`: Unit failed or powered off.

### 4. VTS_Center (4 states)
**Mapping:** Shore-based Vessel Traffic Service (D3).
- `vts_monitoring`: Ingesting AIS and shore radar.
- `vts_issuing_warning`: Broadcasting VHF Ch16 hazard alerts.
- `vts_managing_anchorage`: Assigning parking to delayed vessels.

### 5. Port_Terminal (5 states)
**Mapping:** The destination facility.
- `berth_available` / `berth_allocated` / `berth_occupied`: Physical dock states.
- `cargo_ops_active`: Ship-to-Shore (STS) cranes and Automated Guided Vehicles (AGVs) unloading containers.
- `terminal_congested`: Backlog preventing mooring.

### 6. Tugboat_Fleet (4 states)
**Mapping:** Harbor assist vessels required for large ships.
- `tugs_idle` / `tugs_dispatched` / `tugs_assisting` / `tugs_unavailable`.

### 7. Weather_Tide (5 states)
**Mapping:** Environmental factors dictating maritime limits.
- `weather_nominal` / `restricted_visibility` (triggers COLREGs Rule 19).
- `tide_high` / `tide_low` (affects Under Keel Clearance).

### 8. GNSS_System (3 states)
**Mapping:** GPS/GLONASS satellite constellation feeding the ship's NMEA network.
- `gnss_nominal` / `gnss_degraded` / `gnss_jammed`.

---

## Constraints (ENSURE FOREACH & REJECT)

### Regulatory Constraints (COLREGs)
- **Give-Way Mandate:** A vessel in `colregs_give_way` cannot simply cruise; it MUST transition to `vessel_altering_course` or `vessel_stopping` (Rule 16).
- **Stand-On Mandate:** A vessel in `colregs_stand_on` CANNOT alter course unless the optional `Rule_17_action_in_extremis` is triggered by a failing give-way vessel.

### Physical & Port Constraints
- **Pilotage Laws:** A vessel cannot enter `vessel_maneuvering_port` without a `pilot_onboard`.
- **Tug Requirement:** `vessel_moored` requires `tugs_assisting` for large cargo ships.
- **Congestion:** A vessel cannot moor if the `terminal_congested` state is active.
- **Draft Limits:** High draft vessels cannot maneuver in port during `tide_low`.

### Cyber-Physical Dependencies
- **AIS needs GNSS:** `tx_msg1_dynamic` (which transmits latitude/longitude) is rejected if `gnss_jammed` is active.
- **Navigation Downgrade:** If `gnss_jammed` is active, the bridge must transition to `nav_degraded`.

---

## Coordination Blocks (PRECEDES)

Data flows bridge the systems:
1. **Satellite to Ship:** `precise_position_fix` (GNSS) feeds `tx_msg1_dynamic` (AIS).
2. **Ship to Shore:** `tx_msg1_dynamic` feeds `ais_ingestion` (VTS).
3. **Shore to Ship:** `conflict_identified` (VTS) triggers `Rule_16_take_early_action` (Bridge).
4. **Physical Assistance:** `pushing_pulling` (Tugs) precedes `bow_thrusters_active` (Ship maneuvering).
5. **Logistics:** `lines_fast` (Moored) enables `sts_cranes_working` (Port Ops).

---

## Relevance to Differential Analysis

In the maritime domain, **emergent behavior** often occurs at the intersection of cyber (AIS spoofing/GNSS jamming) and physical (COLREGs/Tides) systems.
- Comparing traces where GNSS is jammed will reveal how the loss of AIS Message 1 cascades into VTS blindness and forced manual navigation.
- Capacity limits (e.g., `terminal_congested` combined with `tugs_unavailable`) will force vessels into emergent holding patterns (`vessel_anchored`), demonstrating supply chain bottlenecks.
