MODELS FOR MIKE COLLINS -- NSA INSuRE+C, UNC Charlotte (Christensen, Sanchez, Sridhar)
Prepared 2026-09-25

All files are Monterey Phoenix schemas saved as plain text. Every model uses
state-alternation grammars with no iteration, so the trace space is the same at
any scope (scope 1 and scope 2 give identical counts). Counts below were
reproduced independently with our closed-form enumerator and, for maritime and
healthcare, confirmed against Gryphon.

File                                                  Domain                        ROOTs  REJECT  Orderings  Unconstrained -> Constrained
----------------------------------------------------  ----------------------------  -----  ------  ---------  ---------------------------
01_Healthcare_Delivery.txt                            Healthcare delivery (spring)      6       8         10        729 ->     36
02_Smart_Home_Energy.txt                              Smart-home energy (in paper)      7      14          3     57,600 -> 18,080
03a_Maritime_Port_12-REJECT_45836-traces.txt          Maritime port logistics           8      12          4    172,800 -> 45,836
03b_Maritime_Port_15-REJECT_38348-traces_paper-version.txt
                                                      Same model + 3 weather rules      8      15          4    172,800 -> 38,348
04_Power_Grid_SCADA.txt                               Substation SCADA                  8       9          4     49,152 -> 14,733
05_Connected_Street_V2X.txt                           Connected street / V2X            8      12          6     61,440 -> 24,536
06_Air_Traffic_Control_8-ROOT.txt                     Air traffic control               8      28          9  1,312,500 -> 350,778
07_ADAS_OTA_Vehicle_Update.txt                        AI-assisted driving + OTA        10      23          ?  1,105,920 -> 28,572 (see note)
08_Agentic_AI.txt                                     LLM agent tool orchestration      8      10          3     27,648 ->  6,608

Notes
- 03a is the version previously sent (12 REJECT). 03b is the revision used in the
  paper's maritime section; adding the three weather-coupling rules removes 7,488
  traces and raises the co-occurrence trend count from 136 to 154.
- 06 is the current 8-ROOT ATC model (Flow_Management and Weather_System added);
  earlier results quoted on 6-ROOT data are superseded.
- 07 is Victor Sanchez's model. Our enumerator gives 28,572 constrained traces for
  this file; the 17,988 quoted in the presentation came from a different run or
  revision and has not been reconciled yet. Treat the count as provisional.
- 08 includes the 8/24 guardrail fix (approve-before-act written as COORDINATE
  blocks rather than bare cross-ROOT ENSURE, which MP would have turned into an
  exclusion).
- Standards each model was built from: SunSpec Modbus / SAE J1772 / OCPP 1.6 /
  IEEE 2030.5 (02); ITU-R M.1371, COLREGs 16/17/19, IALA VTS, NMEA (03);
  IEC 61850 (04); NTCIP 1202 (05); ICAO Doc 4444 / FAA 7110.65 (06);
  ISO 21448, ISO/PAS 8800, UNECE R156, SAE J3016 (07); MCP, OWASP LLM Top 10 (08).
- Trace files (.gry) and the SQLite trace databases are not included; they run
  to about a gigabyte. The enumerator regenerates them from these schemas.

Tools (parser, trace reader, enumerator, schema scanner, co-occurrence engine,
web UI, packaged executable) to follow separately as a repository.
