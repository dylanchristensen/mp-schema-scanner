"""
Direction-A (M2) analysis on the 36 constrained healthcare traces.

Validation goal: do Spring's three known implicit assumptions separate
from junk in the lift ranking once REJECT-forced pairs are filtered out?

The procedure is locked in explore_lift.analyze() and is identical to the
smart-home run. This file only supplies model data: components, the list
of REJECT-derived forced pairs (manual parse of
healthcareDelivery_corrected.mp), and the three known implicit assumptions
to look up after ranking.
"""

from explore_lift import (
    ModelConfig, ForcedPair, ValidationEntry, analyze,
)

# REJECTs in healthcareDelivery_corrected.mp:
#   R1: vitals_recorded > 0 AND has_symptoms == 0 AND receiving_treatment == 0
#       => device_active requires patient_walking_in OR patient_admitted
#   R2: prescription_issued > 0 AND no data_available
#       => physician_prescribing requires ehr_up_to_date OR ehr_outdated
#   R3: dispensing_medication > 0 AND prescription_issued == 0
#       => pharmacy_filling requires physician_prescribing
#   R4: verifying_prescription > 0 AND prescription_issued == 0
#       => pharmacy_checking_prescription requires physician_prescribing
#   R5: payment_sent_to_provider > 0 AND no dispensing AND no receiving_treatment
#       => claim_approved requires pharmacy_filling OR patient_admitted
#   R6: authorization_rejected > 0 AND no prescription AND no dispensing
#       => claim_denied requires physician_prescribing OR pharmacy_filling
#   R7: assessing_condition > 0 AND no symptoms AND no receiving_treatment
#       => physician_prescribing requires patient_walking_in OR patient_admitted
#   R8: evaluating_condition > 0 AND no symptoms AND no receiving_treatment
#       => physician_reviewing requires patient_walking_in OR patient_admitted
CONFIG = ModelConfig(
    name="healthcare",
    db_path="data/healthcare_traces.db",
    table="trace_states_constrained",
    components=["patient", "clinical_device", "ehr_system",
                "physician", "pharmacy", "insurance"],
    expected_n=36,
    top_k=20,
    forced=[
        ForcedPair("device_active", "patient_walking_in", "R1"),
        ForcedPair("device_active", "patient_admitted", "R1"),
        ForcedPair("physician_prescribing", "ehr_up_to_date", "R2"),
        ForcedPair("physician_prescribing", "ehr_outdated", "R2"),
        ForcedPair("pharmacy_filling", "physician_prescribing", "R3"),
        ForcedPair("pharmacy_checking_prescription", "physician_prescribing", "R4"),
        ForcedPair("claim_approved", "pharmacy_filling", "R5"),
        ForcedPair("claim_approved", "patient_admitted", "R5"),
        ForcedPair("claim_denied", "physician_prescribing", "R6"),
        ForcedPair("claim_denied", "pharmacy_filling", "R6"),
        ForcedPair("physician_prescribing", "patient_walking_in", "R7"),
        ForcedPair("physician_prescribing", "patient_admitted", "R7"),
        ForcedPair("physician_reviewing", "patient_walking_in", "R8"),
        ForcedPair("physician_reviewing", "patient_admitted", "R8"),
    ],
    validation=[
        ValidationEntry("physician_reviewing", "ehr_up_to_date",
                        "Assumption #2: reviewing assumes data available"),
        ValidationEntry("physician_reviewing", "ehr_outdated",
                        "Assumption #2: reviewing assumes data available"),
        ValidationEntry("claim_approved", "physician_prescribing",
                        "Assumption #3: payment assumes clinical activity"),
    ],
    validation_label="KNOWN SPRING IMPLICIT ASSUMPTIONS",
)


if __name__ == "__main__":
    analyze(CONFIG)
