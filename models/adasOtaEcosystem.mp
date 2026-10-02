/* ===============================================================
   AI-ASSISTED DRIVING AND SOFTWARE UPDATE ECOSYSTEM
   A System-of-Systems model

   WHAT THIS MODELS, IN PLAIN TERMS
   --------------------------------
   A car whose driving automation depends on a machine-learned
   perception model, together with the off-board systems that build,
   deliver, approve and validate that model.

   A carmaker builds a new perception model and delivers it to the car
   over the air. The car verifies it, installs it while parked, and
   activates it. Meanwhile the car may be driving itself, a camera
   watches whether the person behind the wheel is supervising, and the
   conditions outside may or may not be those the model was built for.
   Ten systems must cooperate, and no single party controls all of
   them, which is what makes this a system of systems.

   NOTE ON TERMINOLOGY
   -------------------
   The perception element is a machine-learned model: a neural network
   trained on labelled driving data. The standards call this an "AI
   element"; ISO/PAS 8800 uses that term throughout. Both usages appear
   below, and mean the same thing.

   GLOSSARY (terms taken from the standards)
   -----------------------------------------
     ODD      Operational Design Domain. The conditions a system was
              designed and validated for: roads, weather, speeds.
              Operating outside the ODD is the central hazard in
              ISO 21448.
     SOTIF    Safety Of The Intended Functionality. Hazards arising
              when nothing has broken, for example when a trained
              model is simply wrong. ISO 21448.
     MRM      Minimal Risk Manoeuvre. What the vehicle does when it can
              no longer perform the driving task: slow and stop safely.
     RxSWIN   Regulatory Software Identification Number. The identifier
              a regulator holds for an approved software version.
              Required by UN ECE R156.
     OTA      Over The Air. An update delivered by radio link rather
              than at a workshop.

   STANDARDS THIS IS GROUNDED IN
   -----------------------------
     ISO/PAS 8800:2024   Road vehicles: safety and artificial
                         intelligence. Output insufficiencies of AI
                         elements; validation scope of a trained model.
     ISO 21448 (SOTIF)   Operational design domain and its boundaries.
     ISO 26262           Functional safety, fault handling, safe states.
     UN ECE R156         Software Update Management System. Updates
                         executed only under safe conditions; recovery
                         on failure; compatibility verified against the
                         target configuration before delivery; RxSWIN
                         bookkeeping.
     UN ECE R155 /
     ISO-SAE 21434       Cybersecurity; authenticity and integrity of
                         delivered software.
     SAE J3016           Driving automation levels, driver engagement,
                         takeover request, minimal risk manoeuvre.

   THE TEN COMPONENTS
   ------------------
     Perception_Stack        the machine-learned model that classifies
                             the scene
     Model_Validation        the record of conditions that model was
                             validated against
     OTA_Backend             the manufacturer's update campaign server
     Update_Manager          the update agent inside the vehicle
     Configuration_Record    the manufacturer's record of what software
                             this vehicle is running
     Vehicle_Motion          parked, driven, self-driving, or stopping
     Driver_Monitoring       whether the driver is supervising
     Telematics_Link         the vehicle's link to the backend
     Type_Approval           the regulator's record of approved software
     Operating_Environment   conditions outside the vehicle

   METHODOLOGICAL NOTE
   -------------------
   The rules below were written from the cited standards, asking in
   each case what the standard requires. They were not selected to
   produce or to avoid any particular finding, and no dependency has
   been deliberately omitted. Whatever the detection pass surfaces on
   this trace space is therefore a property of the schema as written
   rather than of an expectation held while writing it.

   MODELLING NOTES
   ---------------
   1. Every REJECT rule relates events belonging to two DIFFERENT
      components. A rule relating two states of the same component is
      trivially satisfied, because a trace gives each component
      exactly one state.

   2. This model uses no ENSURE FOREACH ordering rules. In Monterey
      Phoenix, BEFORE holds only between events the trace's partial
      order actually relates. An ordering rule between two components
      that nothing coordinates can be satisfied by no trace containing
      both events, so it silently acts as an exclusion rather than as
      sequencing. Prerequisites are therefore written as REJECT rules.

   3. Perception continues to publish output when conditions are
      outside the validated domain and when the deployed model carries
      no validation evidence. This follows ISO 21448 and ISO/PAS 8800:
      an AI element outside its validated envelope does not fall
      silent, it produces confident output that may be wrong.
      Suppressing output in those cases would model a system that
      knows its own limits, which is the opposite of the SOTIF
      phenomenon.

   4. Scope 1 gives a snapshot of one encounter rather than a process
      over time, matching the other models in this study. Workshop
      (non-OTA) updates and security monitoring are out of scope.
=============================================================== */

SCHEMA adasOtaEcosystem

/* The machine-learned perception model. It may be operating, less
   confident than usual, mid-swap, running a reduced fallback, or
   faulted. */
ROOT Perception_Stack :
    ( perception_nominal | perception_degraded | perception_model_switching
    | perception_fallback_active | perception_faulted );

/* The record of conditions the deployed model was validated against. */
ROOT Model_Validation :
    ( odd_fully_validated | odd_partially_validated
    | validation_expired  | model_unvalidated );

/* The manufacturer's server: builds, signs and dispatches campaigns. */
ROOT OTA_Backend :
    ( campaign_idle | campaign_staged | campaign_dispatched | campaign_halted );

/* The in-vehicle agent: verifies, installs and activates updates. */
ROOT Update_Manager :
    ( update_idle | update_verified | update_applied
    | update_failed | update_deferred );

/* The manufacturer's record of the software configuration of this
   vehicle. R156 requires an update to be verified as compatible with
   the target configuration before delivery, which presupposes such a
   record. The record can be accurate, out of date, absent, or a known
   conflict. */
ROOT Configuration_Record :
    ( config_matches_target | config_drifted
    | config_unreported | config_incompatible );

/* What the vehicle is doing. */
ROOT Vehicle_Motion :
    ( vehicle_parked | vehicle_manual_driving
    | vehicle_automated_driving | minimal_risk_manoeuvre );

/* Whether the driver is supervising. */
ROOT Driver_Monitoring :
    ( driver_attentive | driver_hands_off | driver_disengaged | dms_unavailable );

/* The vehicle's connection to the backend. */
ROOT Telematics_Link :
    ( link_online | link_degraded | link_offline );

/* The regulator's record of the approved software version. */
ROOT Type_Approval :
    ( rxswin_current | rxswin_pending | rxswin_lapsed );

/* Conditions outside the vehicle, relative to its design domain. */
ROOT Operating_Environment :
    ( environment_nominal | environment_degraded
    | environment_out_of_odd | sensors_occluded );


/* ===============================================================
   COMPONENT BEHAVIORS
   Each state expands into the events it produces. The rules below
   are written in terms of these events.
=============================================================== */

/* --- Perception: the machine-learned model --------------------- */

/* operating: processes frames, classifies, publishes a scene */
perception_nominal :
    frames_processed
    objects_classified
    perception_output_published;

/* lower confidence, still publishing (modelling note 3) */
perception_degraded :
    frames_processed
    confidence_dropped
    perception_output_published;

/* swapping one model for another */
perception_model_switching :
    model_unloaded
    model_loaded;

/* reduced-capability fallback instead of the full model */
perception_fallback_active :
    running_reduced_capability;

/* faulted: publishing nothing */
perception_faulted :
    perception_output_withheld;

/* --- Validation scope of the deployed model -------------------- */

/* validated across the declared operating domain */
odd_fully_validated :
    validation_evidence_complete
    odd_scope_declared;

/* validated across part of the declared domain */
odd_partially_validated :
    validation_evidence_partial
    odd_scope_declared;

/* validated, but the evidence is out of date */
validation_expired :
    validation_evidence_stale;

/* no validation evidence at all */
model_unvalidated :
    no_validation_evidence;

/* --- The manufacturer's update server -------------------------- */

/* no campaign in progress */
campaign_idle :
    backend_quiescent;

/* built and signed, not yet dispatched */
campaign_staged :
    package_built
    package_signed
    compatibility_checked;

/* dispatched to the vehicle */
campaign_dispatched :
    package_built
    package_signed
    compatibility_checked
    package_transmitted;

/* campaign withdrawn */
campaign_halted :
    campaign_withdrawn;

/* --- The in-vehicle update agent -------------------------------
   Verification is modelled separately from installation: a vehicle
   may verify a package in motion, but R156 permits installation only
   in a safe execution state.                                      */

/* idle */
update_idle :
    agent_waiting;

/* verified, not installed */
update_verified :
    package_verified;

/* verified, installed and activated */
update_applied :
    package_verified
    installing_software
    activation_logged
    [rxswin_updated];

/* installation attempted and rolled back */
update_failed :
    package_verified
    installing_software
    previous_version_restored;

/* verified, then postponed */
update_deferred :
    package_verified
    update_postponed;

/* --- The manufacturer's configuration record ------------------- */

/* the record matches the vehicle the update was built for */
config_matches_target :
    configuration_reported
    configuration_matches_build;

/* the vehicle has changed since the record was taken */
config_drifted :
    configuration_reported
    configuration_changed_since_build;

/* no current record for this vehicle */
config_unreported :
    no_configuration_report;

/* a recorded, known conflict */
config_incompatible :
    configuration_reported
    configuration_conflict;

/* --- Vehicle motion (SAE J3016) -------------------------------- */

vehicle_parked :
    vehicle_stationary;

vehicle_manual_driving :
    driver_in_control;

vehicle_automated_driving :
    automation_engaged
    driving_delegated_to_car;

minimal_risk_manoeuvre :
    mrm_initiated
    vehicle_brought_to_stop;

/* --- Driver monitoring (SAE J3016) ----------------------------- */

driver_attentive :
    gaze_on_road;

driver_hands_off :
    hands_off_detected
    supervision_expected;

driver_disengaged :
    no_supervision_detected;

dms_unavailable :
    monitoring_offline;

/* --- Telematics link (R155 / ISO-SAE 21434) -------------------- */

link_online :
    link_established
    channel_authenticated;

link_degraded :
    link_established
    link_intermittent;

link_offline :
    no_backend_contact;

/* --- Type approval (R156 RxSWIN) ------------------------------- */

rxswin_current :
    rxswin_matches_approval;

rxswin_pending :
    rxswin_awaiting_amendment;

rxswin_lapsed :
    rxswin_mismatch;

/* --- Operating environment (ISO 21448 ODD) --------------------- */

environment_nominal :
    conditions_within_odd;

environment_degraded :
    conditions_marginal;

environment_out_of_odd :
    conditions_outside_odd;

sensors_occluded :
    sensor_view_obstructed;


/* ===============================================================
   PRESENCE CONSTRAINTS (REJECT)
   Each rule states a combination the cited standard forbids.
=============================================================== */

/* --- Delivery (R155, R156) ------------------------------------- */

/* A package cannot be verified unless it was delivered. */
IF #package_verified > 0 AND #package_transmitted == 0 THEN
    REJECT;
FI;

/* Delivery requires a link. */
IF #package_transmitted > 0 AND #link_established == 0 THEN
    REJECT;
FI;

/* No backend contact means no delivery. */
IF #no_backend_contact > 0 AND #package_transmitted > 0 THEN
    REJECT;
FI;

/* A withdrawn campaign delivers nothing. */
IF #campaign_withdrawn > 0 AND #package_verified > 0 THEN
    REJECT;
FI;

/* R156: compatibility is verified against the target configuration,
   so a configuration record must exist. */
IF #compatibility_checked > 0 AND #no_configuration_report > 0 THEN
    REJECT;
FI;

/* --- Safe installation (R156) ---------------------------------- */

/* Installation occurs only in a safe execution state. */
IF #installing_software > 0 AND #vehicle_stationary == 0 THEN
    REJECT;
FI;

/* Installation onto a recorded conflict is forbidden. */
IF #installing_software > 0 AND #configuration_conflict > 0 THEN
    REJECT;
FI;

/* Rollback presupposes a delivered package. */
IF #previous_version_restored > 0 AND #package_transmitted == 0 THEN
    REJECT;
FI;

/* --- Type approval bookkeeping (R156) -------------------------- */

/* An approval amendment presupposes an activation. */
IF #rxswin_awaiting_amendment > 0 AND #activation_logged == 0 THEN
    REJECT;
FI;

/* An approval mismatch presupposes an activation that changed
   type-approval-relevant software. */
IF #rxswin_mismatch > 0 AND #activation_logged == 0 THEN
    REJECT;
FI;

/* Automated driving is not permitted on software that no longer
   matches the approved configuration. */
IF #driving_delegated_to_car > 0 AND #rxswin_mismatch > 0 THEN
    REJECT;
FI;

/* --- Model deployment ------------------------------------------ */

/* A model can be loaded only if an update was activated. */
IF #model_loaded > 0 AND #activation_logged == 0 THEN
    REJECT;
FI;

/* A model swap does not occur while the vehicle is driving itself. */
IF #model_unloaded > 0 AND #driving_delegated_to_car > 0 THEN
    REJECT;
FI;

/* --- Driving automation (SAE J3016) ---------------------------- */

/* Automation cannot be engaged while perception output is withheld. */
IF #automation_engaged > 0 AND #perception_output_withheld > 0 THEN
    REJECT;
FI;

/* Hands-off operation requires engaged automation. */
IF #hands_off_detected > 0 AND #automation_engaged == 0 THEN
    REJECT;
FI;

/* The driving task is not delegated when driver monitoring is out. */
IF #driving_delegated_to_car > 0 AND #monitoring_offline > 0 THEN
    REJECT;
FI;

/* Leaving the operating design domain requires a takeover or an MRM. */
IF #driving_delegated_to_car > 0 AND #conditions_outside_odd > 0 THEN
    REJECT;
FI;

/* A driver who has stopped supervising is not left with the task. */
IF #driving_delegated_to_car > 0 AND #no_supervision_detected > 0 THEN
    REJECT;
FI;

/* An MRM requires a trigger: a perception fault, or lost supervision. */
IF #mrm_initiated > 0
    AND #perception_output_withheld == 0
    AND #no_supervision_detected == 0 THEN
    REJECT;
FI;

/* --- Perception and environment (ISO 21448) -------------------- */

/* Obstructed sensors cannot yield a classified scene. */
IF #sensor_view_obstructed > 0 AND #objects_classified > 0 THEN
    REJECT;
FI;

/* Reduced-capability fallback presupposes adverse conditions. */
IF #running_reduced_capability > 0
    AND #conditions_marginal == 0
    AND #sensor_view_obstructed == 0 THEN
    REJECT;
FI;