# =============================================================================
#   Hospital Appointment & Billing Management System
#   Python Intern Assignment — Intermediate Level
# =============================================================================

# ── LEGB DEMO ─────────────────────────────────────────────────────────────────
# Global clinic config — read by functions via the Enclosing/Global scope.
# Functions never write to these globals (no 'global' keyword), so the global
# state is never accidentally mutated (that's the LEGB best-practice point).
CLINIC_CONFIG = {
    "currency":         "PKR ",
    "senior_age":        60,
    "senior_disc_rate":  0.10,   # 10 % off after insurance
    "ins_consult_rate":  0.20,   # insurance covers 20 % of consultation
    "ins_test_rate":     0.50,   # insurance covers 50 % of tests
}

# ── STARTER DATA ──────────────────────────────────────────────────────────────
patients = {
    "P001": {"name": "Ali Khan",    "age": 32, "city": "Lahore",    "insurance": True},
    "P002": {"name": "Ahmed Raza",  "age": 45, "city": "Multan",    "insurance": False},
    "P003": {"name": "Sara Ahmed",  "age": 28, "city": "Lahore",    "insurance": True},
    "P004": {"name": "Usman Ali",   "age": 67, "city": "Islamabad", "insurance": False},
}

doctors = {
    "D001": {"name": "Dr. Hassan", "specialization": "Cardiology",  "fee": 5000, "available": True},
    "D002": {"name": "Dr. Sara",   "specialization": "Dermatology", "fee": 3000, "available": True},
    "D003": {"name": "Dr. Ahmed",  "specialization": "General",     "fee": 2000, "available": True},
}

appointments = [
    {"appointment_id": "A001", "patient_id": "P001", "doctor_id": "D001",
     "status": "completed", "tests": ["ECG", "Blood Test"]},
    {"appointment_id": "A002", "patient_id": "P002", "doctor_id": "D003",
     "status": "completed", "tests": []},
    {"appointment_id": "A003", "patient_id": "P003", "doctor_id": "D002",
     "status": "cancelled", "tests": []},
    {"appointment_id": "A004", "patient_id": "P004", "doctor_id": "D001",
     "status": "completed", "tests": ["ECG"]},
]

test_prices = {
    "ECG":        1500,
    "Blood Test": 1000,
    "X-Ray":      2500,
    "MRI":        8000,
}

# ── *args CHALLENGE ───────────────────────────────────────────────────────────
def calculate_total(*charges):
    """Accept any number of charge amounts and return their total.

    Example:
        calculate_total(5000, 1500, 1000) → 7500
    """
    return sum(charges)


# ── BILLING HELPERS ───────────────────────────────────────────────────────────
def calculate_test_charges(tests):
    """Return the combined price of a list of test names."""
    return calculate_total(*[test_prices[t] for t in tests])


def calculate_insurance_coverage(consultation_fee, tests_fee, insured):
    """Return (consultation_coverage, tests_coverage) based on insurance flag."""
    if not insured:
        return 0, 0
    # Read rates from global config — LEGB: Global scope lookup
    consult_coverage = consultation_fee * CLINIC_CONFIG["ins_consult_rate"]
    tests_coverage   = tests_fee        * CLINIC_CONFIG["ins_test_rate"]
    return consult_coverage, tests_coverage


# ── **kwargs CHALLENGE ────────────────────────────────────────────────────────
def calculate_bill(consultation_fee, **options):
    """Configurable billing function.

    Keyword options
    ---------------
    insurance      : bool  — apply insurance coverage (default False)
    senior_discount: bool  — apply 10 % senior discount (default False)
    include_tests  : bool  — include test charges in bill (default True)
    tests_fee      : float — pre-calculated test charges (default 0)

    Returns a dict with subtotal, insurance_covered, senior_discount,
    and patient_pays.
    """
    # Read senior discount rate from enclosing/global config (LEGB demo)
    senior_rate = CLINIC_CONFIG["senior_disc_rate"]

    tests_fee = options.get("tests_fee", 0) if options.get("include_tests", True) else 0

    subtotal = calculate_total(consultation_fee, tests_fee)

    consult_cov, tests_cov = calculate_insurance_coverage(
        consultation_fee, tests_fee, options.get("insurance", False)
    )
    insurance_covered = consult_cov + tests_cov

    amount_after_insurance = subtotal - insurance_covered

    senior_discount = 0
    if options.get("senior_discount", False):
        senior_discount = amount_after_insurance * senior_rate   # 10 %

    patient_pays = amount_after_insurance - senior_discount

    return {
        "subtotal":          round(subtotal, 2),
        "insurance_covered": round(insurance_covered, 2),
        "senior_discount":   round(senior_discount, 2),
        "patient_pays":      round(patient_pays, 2),
    }


# ── LAMBDA USAGE ──────────────────────────────────────────────────────────────
# Lambdas are used throughout the report/sort logic below.
# Examples defined here for clarity:
sort_by_revenue  = lambda items: sorted(items, key=lambda x: x[1]["revenue"],  reverse=True)
sort_by_paid     = lambda items: sorted(items, key=lambda x: x[1]["paid"],     reverse=True)
sort_by_appts    = lambda items: sorted(items, key=lambda x: x[1]["total"],    reverse=True)


# ── VALIDATION ────────────────────────────────────────────────────────────────
def validate_appointment(patient_id, doctor_id, tests, status):
    """Validate all fields of an appointment request.

    Returns (True, None) on success or (False, reason_string) on failure.
    """
    # 1. Patient exists?
    if patient_id not in patients:
        return False, f"Patient {patient_id} does not exist"

    # 2. Valid age?
    age = patients[patient_id].get("age")
    if not isinstance(age, (int, float)) or isinstance(age, bool) or age < 0:
        return False, f"Invalid age for patient {patient_id}"

    # 3. Doctor exists?
    if doctor_id not in doctors:
        return False, f"Doctor {doctor_id} does not exist"

    # 4. Doctor available?
    if not doctors[doctor_id].get("available", True):
        return False, f"Doctor {doctors[doctor_id]['name']} is currently unavailable"

    # 5. Valid status?
    if status not in ("completed", "pending", "cancelled"):
        return False, f"Invalid appointment status: '{status}'"

    # 6. Tests must be a list or tuple (strings are iterable but not valid here)
    if not isinstance(tests, (list, tuple)) or isinstance(tests, str):
        return False, "Tests must be provided as a list"

    # 7. Each test must be a string and a known test name
    for test in tests:
        if not isinstance(test, str) or test not in test_prices:
            return False, f"Invalid test requested: '{test}'"

    return True, None


# ── APPOINTMENT PROCESSING ────────────────────────────────────────────────────
def process_appointment(appointment_id, patient_id, doctor_id,
                        tests, status, processed_ids):
    """Validate and process one appointment.

    processed_ids : set — tracks already-processed IDs to prevent duplicates.

    Returns (True, appointment_dict) on success or (False, reason) on failure.
    """
    # Duplicate check
    if appointment_id in processed_ids:
        return False, f"Appointment {appointment_id} has already been processed"

    # Validate
    valid, reason = validate_appointment(patient_id, doctor_id, tests, status)
    if not valid:
        return False, reason

    patient = patients[patient_id]
    doctor  = doctors[doctor_id]

    # Remove duplicate tests while preserving order
    unique_tests = list(dict.fromkeys(tests))
    tests_fee    = calculate_test_charges(unique_tests)

    # Only bill completed appointments
    if status == "completed":
        is_senior = patient["age"] >= CLINIC_CONFIG["senior_age"]
        billing   = calculate_bill(
            doctor["fee"],
            insurance=patient.get("insurance", False),
            senior_discount=is_senior,
            include_tests=True,
            tests_fee=tests_fee,
        )
    else:
        billing = {"subtotal": 0, "insurance_covered": 0,
                   "senior_discount": 0, "patient_pays": 0}

    processed_ids.add(appointment_id)

    return True, {
        "appointment_id": appointment_id,
        "patient_id":     patient_id,
        "doctor_id":      doctor_id,
        "status":         status,
        "tests":          unique_tests,
        "consult_fee":    doctor["fee"],
        "tests_fee":      tests_fee,
        "billing":        billing,
    }


# ── CANCELLATION ──────────────────────────────────────────────────────────────
def cancel_appointment(appointment_id, appointment_list):
    """Try to cancel an appointment.

    Returns (True, success_message) or (False, reason).
    """
    for i, appt in enumerate(appointment_list):
        if appt["appointment_id"] == appointment_id:
            if appt["status"] == "completed":
                return False, f"Cannot cancel a completed appointment ({appointment_id})"
            if appt["status"] == "cancelled":
                return False, f"Appointment {appointment_id} is already cancelled"
            # Pending → cancel
            appointment_list[i] = {**appt, "status": "cancelled"}
            return True, f"Appointment {appointment_id} cancelled successfully"

    return False, f"Appointment {appointment_id} not found"


# ── DOCTOR REPORT ─────────────────────────────────────────────────────────────
def generate_doctor_report(processed_appointments):
    """Return statistics for every doctor plus summary highlights."""

    # Build per-doctor stats using dict comprehension
    doctor_stats = {
        doc_id: {
            "name":      doc["name"],
            "spec":      doc["specialization"],
            "total":     0,
            "completed": 0,
            "cancelled": 0,
            "revenue":   0,
        }
        for doc_id, doc in doctors.items()
    }

    for appt in processed_appointments:
        doc_id = appt["doctor_id"]
        if doc_id not in doctor_stats:
            continue
        doctor_stats[doc_id]["total"] += 1
        if appt["status"] == "completed":
            doctor_stats[doc_id]["completed"] += 1
            # Revenue = what patient paid + what insurance paid
            doctor_stats[doc_id]["revenue"] += (
                appt["billing"]["patient_pays"] +
                appt["billing"]["insurance_covered"]
            )
        elif appt["status"] == "cancelled":
            doctor_stats[doc_id]["cancelled"] += 1

    # Average bill per completed appointment
    for stats in doctor_stats.values():
        stats["avg_bill"] = (
            round(stats["revenue"] / stats["completed"], 2)
            if stats["completed"] > 0 else 0
        )

    # Count appointments per specialization — comprehension + lambda sort
    spec_counts = {}
    for doc_id, stats in doctor_stats.items():
        spec = stats["spec"]
        spec_counts[spec] = spec_counts.get(spec, 0) + stats["total"]

    most_requested_doctor = max(
        doctor_stats.values(), key=lambda s: s["total"]
    ) if doctor_stats else None

    most_requested_spec = (
        max(spec_counts, key=lambda s: spec_counts[s])
        if spec_counts else "N/A"
    )

    return doctor_stats, most_requested_doctor, most_requested_spec

# ── PATIENT REPORT ────────────────────────────────────────────────────────────
def generate_patient_report(processed_appointments):
    """Return statistics for every patient plus summary highlights."""

    # List comprehensions for insured and senior patients
    insured_patients = [pid for pid, p in patients.items() if p.get("insurance")]
    senior_patients  = [pid for pid, p in patients.items()
                        if isinstance(p.get("age"), (int, float))
                        and not isinstance(p.get("age"), bool)
                        and p["age"] >= CLINIC_CONFIG["senior_age"]]

    patient_stats = {
        pid: {
            "name":      p["name"],
            "total":     0,
            "completed": 0,
            "cancelled": 0,
            "charges":   0,   # gross (before insurance / discount)
            "ins_cov":   0,
            "paid":      0,
        }
        for pid, p in patients.items()
    }

    for appt in processed_appointments:
        pid = appt["patient_id"]
        if pid not in patient_stats:
            continue
        patient_stats[pid]["total"] += 1
        if appt["status"] == "completed":
            patient_stats[pid]["completed"] += 1
            patient_stats[pid]["charges"] += appt["consult_fee"] + appt["tests_fee"]
            patient_stats[pid]["ins_cov"] += appt["billing"]["insurance_covered"]
            patient_stats[pid]["paid"]    += appt["billing"]["patient_pays"]
        elif appt["status"] == "cancelled":
            patient_stats[pid]["cancelled"] += 1

    # Lambdas for sorting (requirement 11)
    highest_spender = max(
        patient_stats.values(), key=lambda s: s["paid"]
    ) if patient_stats else None

    most_appointments = max(
        patient_stats.values(), key=lambda s: s["total"]
    ) if patient_stats else None

    no_completed = [
        pid for pid, s in patient_stats.items() if s["completed"] == 0
    ]

    return {
        "stats":        patient_stats,
        "top_spender":  highest_spender,
        "most_appts":   most_appointments,
        "no_completed": no_completed,
        "insured":      insured_patients,
        "seniors":      senior_patients,
    }

# ── CLINIC DASHBOARD ──────────────────────────────────────────────────────────
def generate_clinic_report(processed_appointments):
    """Print the full clinic management dashboard."""

    doctor_stats, most_req_doctor, most_req_spec = generate_doctor_report(processed_appointments)
    patient_report = generate_patient_report(processed_appointments)

    currency = CLINIC_CONFIG["currency"]   # LEGB: global read inside function

    completed_appts = [a for a in processed_appointments if a["status"] == "completed"]
    cancelled_count = sum(1 for a in processed_appointments if a["status"] == "cancelled")
    pending_count   = sum(1 for a in processed_appointments if a["status"] == "pending")

    consult_revenue  = sum(a["consult_fee"]                    for a in completed_appts)
    test_revenue     = sum(a["tests_fee"]                      for a in completed_appts)
    insurance_total  = sum(a["billing"]["insurance_covered"]   for a in completed_appts)
    patient_total    = sum(a["billing"]["patient_pays"]        for a in completed_appts)

    top_spender_name = (
        patient_report["top_spender"]["name"]
        if patient_report["top_spender"] else "N/A"
    )

    # ── Doctor Statistics ──────────────────────────────────────────────────
    print("\n" + "=" * 48)
    print("         DOCTOR STATISTICS REPORT")
    print("=" * 48)
    for doc_id, stats in sort_by_revenue(doctor_stats.items()):
        print(f"  {doc_id}: {stats['name']} ({stats['spec']})")
        print(f"    Appointments : {stats['total']}  |  Completed : {stats['completed']}"
              f"  |  Cancelled : {stats['cancelled']}")
        print(f"    Revenue      : {currency}{stats['revenue']:,.0f}"
              f"  |  Avg Bill : {currency}{stats['avg_bill']:,.0f}")

    most_req_doc_name = most_req_doctor["name"] if most_req_doctor else "N/A"
    print(f"\n  >> Most Requested Doctor       : {most_req_doc_name}")
    print(f"  >> Most Requested Specialization: {most_req_spec}")
    print("=" * 48)

    # ── Patient Statistics ─────────────────────────────────────────────────
    print("\n" + "=" * 48)
    print("         PATIENT STATISTICS REPORT")
    print("=" * 48)
    for pid, stats in sort_by_paid(patient_report["stats"].items()):
        print(f"  {pid}: {stats['name']}")
        print(f"    Appointments : {stats['total']}  |  Completed : {stats['completed']}"
              f"  |  Cancelled : {stats['cancelled']}")
        print(f"    Charges      : {currency}{stats['charges']:,.0f}"
              f"  |  Insurance : {currency}{stats['ins_cov']:,.0f}"
              f"  |  Paid : {currency}{stats['paid']:,.0f}")

    most_appts_name = patient_report["most_appts"]["name"] if patient_report["most_appts"] else "N/A"
    print(f"\n  >> Highest Spending Patient : {top_spender_name}")
    print(f"  >> Most Appointments Patient: {most_appts_name}")
    print(f"  >> No Completed Appointments: {patient_report['no_completed'] or 'None'}")
    print(f"  >> Insured Patients         : {patient_report['insured']}")
    print(f"  >> Senior Patients (60+)    : {patient_report['seniors']}")
    print("=" * 48)

    # ── Clinic Dashboard ───────────────────────────────────────────────────
    print(f"""
========================================
           CLINIC DASHBOARD
========================================
Total Patients          : {len(patients)}
Total Doctors           : {len(doctors)}
Total Appointments      : {len(processed_appointments)}
  Completed             : {len(completed_appts)}
  Cancelled             : {cancelled_count}
  Pending               : {pending_count}
Total Consultation Rev  : {currency}{consult_revenue:,.0f}
Total Test Revenue      : {currency}{test_revenue:,.0f}
Total Insurance Coverage: {currency}{insurance_total:,.0f}
Total Patient Revenue   : {currency}{patient_total:,.0f}
Most Requested Spec     : {most_req_spec}
Highest Spending Patient: {top_spender_name}
========================================""")
def main():
    processed_appointments = []   # list of processed appointment dicts
    processed_ids          = set() # tracks processed IDs to block duplicates
    currency               = CLINIC_CONFIG["currency"]
    global doctors   # needed only in the edge-case block to swap a local copy

    # ── 1. Process Starter Appointments ─────────────────────────────────────
    print("\n" + "=" * 55)
    print("  STEP 1 — PROCESSING STARTER APPOINTMENTS")
    print("=" * 55)

    for appt in appointments:
        success, result = process_appointment(
            appt["appointment_id"],
            appt["patient_id"],
            appt["doctor_id"],
            appt["tests"],
            appt["status"],
            processed_ids,
        )
        if success:
            processed_appointments.append(result)
            b = result["billing"]
            print(f"  {result['appointment_id']} → PROCESSED  "
                  f"| Patient Pays: {currency}{b['patient_pays']:,.0f}"
                  f"  | Insurance: {currency}{b['insurance_covered']:,.0f}"
                  f"  | Senior Disc: {currency}{b['senior_discount']:,.0f}")
        else:
            print(f"  {appt['appointment_id']} → REJECTED   | Reason: {result}")

    # ── 2. Edge Cases ────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  STEP 2 — EDGE CASE TESTING")
    print("=" * 55)

    sandbox_ids  = set(processed_ids)   # copy already-processed IDs so
                                        # the duplicate-ID test still works
    sandbox_list = []                   # throwaway — never passed to reports

    doctors_with_d002_off = {
        doc_id: dict(doc) for doc_id, doc in doctors.items()
    }
    doctors_with_d002_off["D002"]["available"] = False

    _doctors_backup = doctors
    try:
        doctors = doctors_with_d002_off

        edge_cases = [
            # (id,    patient, doctor, tests,             status,      description)
            ("A005", "P999",  "D001", [],                "completed", "Invalid patient ID"),
            ("A006", "P001",  "D999", [],                "completed", "Invalid doctor ID"),
            ("A007", "P001",  "D002", [],                "completed", "Doctor unavailable"),
            ("A008", "P001",  "D001", ["InvalidTest"],   "completed", "Invalid test name"),
            ("A009", "P001",  "D001", ["ECG", "ECG"],    "completed", "Duplicate tests (auto-removed)"),
            ("A010", "P001",  "D001", [],                "xyz",       "Invalid status"),
            ("A001", "P001",  "D001", [],                "completed", "Double-process same ID"),
            ("A012", "P001",  "D001", None,              "completed", "tests=None crash guard"),
            ("A013", "P001",  "D001", "ECG",             "completed", "tests=string crash guard"),
        ]

        for (appt_id, pid, did, tests, status, desc) in edge_cases:
            success, result = process_appointment(
                appt_id, pid, did, tests, status, sandbox_ids
            )
            if success:
                sandbox_list.append(result)   # stays in sandbox only
            label   = "SUCCESS " if success else "REJECTED"
            details = f"Tests kept: {result['tests']}" if success else result
            print(f"  {appt_id} → {label} | {desc}")
            print(f"           └─ {details}")

    finally:
        doctors = _doctors_backup   # always restore, even if something blows up

    # ── 3. Cancellation Tests ────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  STEP 3 — CANCELLATION RULES")
    print("=" * 55)
    cancel_sandbox = list(processed_appointments)   # shallow copy of real appts
    success, pending_appt = process_appointment(
        "A011", "P002", "D003", [], "pending", set(processed_ids)
    )
    if success:
        cancel_sandbox.append(pending_appt)

    cancel_tests = [
        ("A001",  "Cancel completed appointment   "),
        ("A003",  "Cancel already-cancelled appt  "),
        ("A011",  "Cancel pending appointment     "),
        ("A011",  "Cancel same appointment again  "),
        ("A999",  "Cancel non-existent appointment"),
    ]
    for appt_id, desc in cancel_tests:
        ok, msg = cancel_appointment(appt_id, cancel_sandbox)
        outcome = "OK  " if ok else "FAIL"
        print(f"  {desc}: {outcome} → {msg}")
    print("\n" + "=" * 55)
    print("  STEP 4 — *args  →  calculate_total()")
    print("=" * 55)
    print(f"  calculate_total(5000, 1500, 1000) = {calculate_total(5000, 1500, 1000)}")
    print(f"  calculate_total(8000)             = {calculate_total(8000)}")
    print(f"  calculate_total()                 = {calculate_total()}")
    print("\n" + "=" * 55)
    print("  STEP 5 — **kwargs  →  calculate_bill()")
    print("=" * 55)

    demo_cases = [
        (5000, {"insurance": True,  "senior_discount": True,  "include_tests": True,  "tests_fee": 2500},
               "Insured + senior + tests"),
        (5000, {"insurance": False, "senior_discount": False, "include_tests": True,  "tests_fee": 2500},
               "No insurance, no senior, with tests"),
        (3000, {"insurance": True,  "senior_discount": False, "include_tests": False},
               "Insured, no tests"),
        (2000, {"insurance": False, "senior_discount": True,  "include_tests": False},
               "No insurance, senior, no tests"),
    ]
    for fee, opts, desc in demo_cases:
        bill = calculate_bill(fee, **opts)
        print(f"  {desc}")
        print(f"    Subtotal: {currency}{bill['subtotal']:,.0f}"
              f"  | Insurance: {currency}{bill['insurance_covered']:,.0f}"
              f"  | Senior Disc: {currency}{bill['senior_discount']:,.0f}"
              f"  | Pays: {currency}{bill['patient_pays']:,.0f}")

    # ── 6. Full Clinic Dashboard ─────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  STEP 6 — FULL CLINIC DASHBOARD & REPORTS")
    print("=" * 55)
    generate_clinic_report(processed_appointments)

if __name__ == "__main__":
    main()
