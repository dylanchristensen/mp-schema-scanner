MP MODELS -- NSA INSuRE+C, UNC Charlotte

All files are Monterey Phoenix schemas. Every model uses state-alternation
grammars with no iteration, so the trace space is the same at any scope
(scope 1 and scope 2 give identical counts). Counts below were reproduced
with the closed-form enumerator (pipeline/mp_enumerate.py) and, for maritime
and healthcare, confirmed against Gryphon.

File                                                Domain                        ROOTs  REJECT  Orderings  Unconstrained -> Constrained
--------------------------------------------------  ----------------------------  -----  ------  ---------  ---------------------------
healthcareDelivery_corrected.mp                     Healthcare delivery               6       8         10        729 ->     36
Smart_Home_Energy_Composed.mp                       Smart-home energy                 7      14          3     57,600 -> 18,080
Maritime_Port_Logistics_Composed_12REJECT.mp        Maritime port logistics           8      12          4    172,800 -> 45,836
Maritime_Port_Logistics_Composed_15REJECT_paper.mp  Same model + 3 weather rules      8      15          4    172,800 -> 38,348
Power_Grid_SCADA_Composed.mp                        Substation SCADA                  8       9          4     49,152 -> 14,733
Connected_Street_V2X_Composed.mp                    Connected street / V2X            8      12          6     61,440 -> 24,536
ATC_System_Composed_8ROOT.mp                        Air traffic control               8      28          9  1,312,500 -> 350,778
adasOtaEcosystem.mp                                 AI-assisted driving + OTA        10      23          0  1,105,920 -> 28,572 (see note)
Agentic_AI_Composed.mp                              LLM agent tool orchestration      8      10          3     27,648 ->  6,608

Notes
- The 15-REJECT maritime file is the revision used in the paper's maritime
  section; adding the three weather-coupling rules to the 12-REJECT file removes
  7,488 traces and raises the co-occurrence trend count from 136 to 154.
- The ATC file is the current 8-ROOT model (Flow_Management and Weather_System
  added); results on the earlier 6-ROOT data are superseded.
- adasOtaEcosystem.mp was contributed by Victor Sanchez and uses no ENSURE
  FOREACH ordering rules. The constrained count shown is the enumerator's result
  for this file; an earlier run of a different revision gave 17,988.
- The agentic-AI file writes approve-before-act as COORDINATE blocks rather than
  bare cross-ROOT ENSURE rules, which MP would turn into an exclusion.
- Standards each model was built from: SunSpec Modbus / SAE J1772 / OCPP 1.6 /
  IEEE 2030.5 (smart home); ITU-R M.1371, COLREGs 16/17/19, IALA VTS, NMEA
  (maritime); IEC 61850 (SCADA); NTCIP 1202 (connected street); ICAO Doc 4444 /
  FAA 7110.65 (ATC); ISO 21448, ISO/PAS 8800, UNECE R156, SAE J3016 (ADAS/OTA);
  MCP, OWASP LLM Top 10 (agentic AI).
- Trace files (.gry) and the SQLite trace databases are not included; they run
  to about a gigabyte. The enumerator regenerates them from these schemas.
