/* ═══════════════════════════════════════════════════════════════
   Healthcare Delivery Ecosystem — SoS Model
   Corrected version: ENSURE FOREACH for ordering constraints,
   REJECT for presence constraints.

   Components:
     - Patient
     - Clinical_Device
     - EHR_System
     - Physician
     - Pharmacy
     - Insurance
═══════════════════════════════════════════════════════════════ */

SCHEMA healthcareDelivery

ROOT Patient :
    ( patient_walking_in | patient_admitted | patient_discharged );

ROOT Clinical_Device :
    ( device_active | device_recalibrating | device_powered_off );

ROOT EHR_System :
    ( ehr_up_to_date | ehr_outdated | ehr_system_down );

ROOT Physician :
    ( physician_reviewing | physician_prescribing | physician_off_duty );

ROOT Pharmacy :
    ( pharmacy_filling | pharmacy_checking_prescription | pharmacy_closed );

ROOT Insurance :
    ( claim_approved | claim_pending | claim_denied );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
═══════════════════════════════════════════ */

/* --- Patient --- */
patient_walking_in :
    has_symptoms
    seeking_care;

patient_admitted :
    receiving_treatment;

patient_discharged :
    treatment_complete;

/* --- Clinical Device --- */
device_active :
    measuring_vitals
    vitals_recorded;

device_recalibrating :
    awaiting_calibration;

device_powered_off :
    device_offline;

/* --- EHR System --- */
ehr_up_to_date :
    records_current
    current_data_available;

ehr_outdated :
    records_outdated
    outdated_data_available;

ehr_system_down :
    no_records_available;

/* --- Physician --- */
physician_reviewing :
    reviewing_patient_data
    evaluating_condition;

physician_prescribing :
    reading_patient_data
    assessing_condition
    prescription_issued;

physician_off_duty :
    no_physician_present;

/* --- Pharmacy --- */
pharmacy_filling :
    dispensing_medication;

pharmacy_checking_prescription :
    verifying_prescription
    awaiting_confirmation;

pharmacy_closed :
    pharmacy_window_closed;

/* --- Insurance --- */
claim_approved :
    claim_authorized
    payment_sent_to_provider;

claim_pending :
    awaiting_review;

claim_denied :
    authorization_rejected;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
   Transitive temporal ordering between events.
   These filter traces where ordering is violated.
═══════════════════════════════════════════ */

/* Device → EHR: vitals recorded before records are current */
ENSURE FOREACH $d: vitals_recorded, $e: records_current
    ($d BEFORE $e);

/* EHR → Physician: data available before physician reads */
ENSURE FOREACH $e: current_data_available, $p: reviewing_patient_data
    ($e BEFORE $p);

ENSURE FOREACH $e: current_data_available, $p: reading_patient_data
    ($e BEFORE $p);

ENSURE FOREACH $e: outdated_data_available, $p: reviewing_patient_data
    ($e BEFORE $p);

ENSURE FOREACH $e: outdated_data_available, $p: reading_patient_data
    ($e BEFORE $p);

/* Physician → Pharmacy: prescription before dispensing/verification */
ENSURE FOREACH $p: prescription_issued, $f: dispensing_medication
    ($p BEFORE $f);

ENSURE FOREACH $p: prescription_issued, $f: verifying_prescription
    ($p BEFORE $f);

/* Pharmacy → Insurance: dispensing before payment */
ENSURE FOREACH $f: dispensing_medication, $i: payment_sent_to_provider
    ($f BEFORE $i);

/* Patient → Physician: seeking care before assessment */
ENSURE FOREACH $p: seeking_care, $d: assessing_condition
    ($p BEFORE $d);

ENSURE FOREACH $p: seeking_care, $d: evaluating_condition
    ($p BEFORE $d);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
   Hard physical/logical constraints.
   These eliminate impossible traces entirely.
═══════════════════════════════════════════ */

/* Vitals require a patient to be present */
IF #vitals_recorded > 0 AND #has_symptoms == 0 AND #receiving_treatment == 0 THEN
    REJECT;
FI;

/* Physician can't prescribe without any data available */
IF #prescription_issued > 0
    AND #current_data_available == 0
    AND #outdated_data_available == 0 THEN
    REJECT;
FI;

/* Pharmacy can't dispense without a prescription */
IF #dispensing_medication > 0 AND #prescription_issued == 0 THEN
    REJECT;
FI;

/* Pharmacy can't verify without a prescription */
IF #verifying_prescription > 0 AND #prescription_issued == 0 THEN
    REJECT;
FI;

/* Payment requires some treatment to have been delivered */
IF #payment_sent_to_provider > 0
    AND #dispensing_medication == 0
    AND #receiving_treatment == 0 THEN
    REJECT;
FI;

/* Claim denied requires something to have been submitted */
IF #authorization_rejected > 0
    AND #prescription_issued == 0
    AND #dispensing_medication == 0 THEN
    REJECT;
FI;

/* Physician can't assess without a patient present */
IF #assessing_condition > 0
    AND #has_symptoms == 0
    AND #receiving_treatment == 0 THEN
    REJECT;
FI;

IF #evaluating_condition > 0
    AND #has_symptoms == 0
    AND #receiving_treatment == 0 THEN
    REJECT;
FI;
