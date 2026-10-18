# Hospital Appointment & Billing Management System

# --- LEGB: Global config (read by functions without modifying global state) ---
CONFIG = {"currency": "$", "senior_age": 60, "senior_disc": 0.10,
          "ins_consult": 0.20, "ins_test": 0.50}

# --- Starter Data ---
patients = {
    "P001": {"name": "Ali Khan",   "age": 32, "city": "Lahore",    "insurance": True},
    "P002": {"name": "Ahmed Raza", "age": 45, "city": "Multan",    "insurance": False},
    "P003": {"name": "Sara Ahmed", "age": 28, "city": "Lahore",    "insurance": True},
    "P004": {"name": "Usman Ali",  "age": 67, "city": "Islamabad", "insurance": False},
}
doctors = {
    "D001": {"name": "Dr. Hassan", "specialization": "Cardiology",  "fee": 5000, "available": True},
    "D002": {"name": "Dr. Sara",   "specialization": "Dermatology", "fee": 3000, "available": True},
    "D003": {"name": "Dr. Ahmed",  "specialization": "General",     "fee": 2000, "available": True},
}
appointments = [
    {"appointment_id": "A001", "patient_id": "P001", "doctor_id": "D001", "status": "completed", "tests": ["ECG", "Blood Test"]},
    {"appointment_id": "A002", "patient_id": "P002", "doctor_id": "D003", "status": "completed", "tests": []},
    {"appointment_id": "A003", "patient_id": "P003", "doctor_id": "D002", "status": "cancelled", "tests": []},
    {"appointment_id": "A004", "patient_id": "P004", "doctor_id": "D001", "status": "completed", "tests": ["ECG"]},
]
test_prices = {"ECG": 1500, "Blood Test": 1000, "X-Ray": 2500, "MRI": 8000}

# --- LEGB: Enclosing scope demo (closure captures rate) ---
def make_discount_applier(rate):
    def apply(amount): return amount * rate
    return apply

senior_discount_fn = make_discount_applier(CONFIG["senior_disc"])

# --- *args challenge ---
def calculate_total(*charges):
    """Sum any number of charges.  e.g. calculate_total(5000, 1500, 1000) -> 7500"""
    return sum(charges)

# --- Helper functions ---
def calculate_test_charges(test_list):
    seen = set()
    return sum(test_prices[t] for t in test_list if t not in seen and not seen.add(t))

def calculate_insurance_coverage(consult, tests, insured):
    if not insured: return 0, 0
    return consult * CONFIG["ins_consult"], tests * CONFIG["ins_test"]

# --- **kwargs challenge ---
def calculate_bill(consult_fee, **kw):
    """Configurable billing: insurance, senior_discount, include_tests, tests_fee."""
    tests_fee = kw.get("tests_fee", 0) if kw.get("include_tests", True) else 0
    subtotal = calculate_total(consult_fee, tests_fee)
    c_cov, t_cov = calculate_insurance_coverage(consult_fee, tests_fee, kw.get("insurance", False))
    ins_covered = c_cov + t_cov
    after_ins = subtotal - ins_covered
    disc = senior_discount_fn(after_ins) if kw.get("senior_discount", False) else 0
    return {"subtotal": subtotal, "insurance_covered": ins_covered,
            "senior_discount": disc, "patient_pays": after_ins - disc}

# --- Validation ---
processed_ids = set()

def validate_appointment(pid, did, tests, status):
    if pid not in patients: return False, f"Patient {pid} does not exist"
    if not isinstance(patients[pid].get("age"), (int, float)) or patients[pid]["age"] < 0:
        return False, f"Invalid age for patient {pid}"
    if did not in doctors: return False, f"Doctor {did} does not exist"
    if not doctors[did].get("available", True):
        return False, f"Doctor {doctors[did]['name']} is currently unavailable"
    if status not in ("completed", "pending", "cancelled"):
        return False, f"Invalid appointment status: '{status}'"
    for t in tests:
        if t not in test_prices: return False, f"Invalid test requested: '{t}'"
    return True, None

def process_appointment(aid, pid, did, tests, status="pending"):
    if aid in processed_ids: return False, f"Appointment {aid} has already been processed"
    ok, reason = validate_appointment(pid, did, tests, status)
    if not ok: return False, reason
    p, d = patients[pid], doctors[did]
    seen = set()
    unique = [t for t in tests if t not in seen and not seen.add(t)]  # comprehension
    tfee = calculate_test_charges(unique)
    bill = calculate_bill(d["fee"], insurance=p.get("insurance", False),
                          senior_discount=p["age"] >= CONFIG["senior_age"],
                          include_tests=True, tests_fee=tfee)
    processed_ids.add(aid)
    return True, {"appointment_id": aid, "patient_id": pid, "doctor_id": did,
                  "status": status, "tests": unique, "consult_fee": d["fee"],
                  "tests_fee": tfee, "billing": bill}

# --- Cancellation ---
def cancel_appointment(aid, appt_list):
    for a in appt_list:
        if a["appointment_id"] == aid:
            if a["status"] == "completed": return False, f"Cannot cancel completed appointment {aid}"
            if a["status"] == "cancelled": return False, f"Appointment {aid} is already cancelled"
            a["status"] = "cancelled"
            return True, f"Appointment {aid} successfully cancelled"
    return False, f"Appointment {aid} not found"

# --- Doctor Report ---
def generate_doctor_report(pa):
    stats, spec_cnt = {}, {}
    for did, d in doctors.items():
        da = [a for a in pa if a["doctor_id"] == did]
        comp = [a for a in da if a["status"] == "completed"]
        canc = [a for a in da if a["status"] == "cancelled"]
        rev = sum(a["billing"]["patient_pays"] + a["billing"]["insurance_covered"] for a in comp)
        stats[did] = {"name": d["name"], "spec": d["specialization"], "total": len(da),
                      "completed": len(comp), "cancelled": len(canc), "revenue": rev,
                      "avg": rev / len(comp) if comp else 0}
        spec_cnt[d["specialization"]] = spec_cnt.get(d["specialization"], 0) + len(da)
    best_doc = max(stats.values(), key=lambda x: x["total"]) if stats else None  # lambda
    best_spec = max(spec_cnt, key=lambda s: spec_cnt[s]) if spec_cnt else "N/A"  # lambda
    return stats, best_doc, best_spec

# --- Patient Report ---
def generate_patient_report(pa):
    insured = [pid for pid, p in patients.items() if p.get("insurance")]    # comprehension
    seniors = [pid for pid, p in patients.items() if p["age"] >= CONFIG["senior_age"]]  # comprehension
    stats = {}
    for pid, p in patients.items():
        pp = [a for a in pa if a["patient_id"] == pid]
        comp = [a for a in pp if a["status"] == "completed"]
        stats[pid] = {"name": p["name"], "total": len(pp), "completed": len(comp),
                      "cancelled": len(pp) - len(comp),
                      "charges": sum(a["consult_fee"] + a["tests_fee"] for a in comp),
                      "ins_cov": sum(a["billing"]["insurance_covered"] for a in comp),
                      "paid": sum(a["billing"]["patient_pays"] for a in comp)}
    top = max(stats.values(), key=lambda x: x["paid"]) if stats else None       # lambda
    most = max(stats.values(), key=lambda x: x["total"]) if stats else None      # lambda
    no_comp = [pid for pid, s in stats.items() if s["completed"] == 0]
    return {"stats": stats, "top_spender": top, "most_appts": most,
            "no_completed": no_comp, "insured": insured, "seniors": seniors}

# --- Clinic Dashboard ---
def display_dashboard(pa):
    ds, _, best_spec = generate_doctor_report(pa)
    pr = generate_patient_report(pa)
    comp = [a for a in pa if a["status"] == "completed"]
    c = CONFIG["currency"]
    top_name = pr["top_spender"]["name"] if pr["top_spender"] else "N/A"

    # Print doctor report
    print("\n" + "=" * 48 + "\n        DOCTOR STATISTICS REPORT\n" + "=" * 48)
    for did, s in ds.items():
        print(f"  {did}: {s['name']} ({s['spec']})")
        print(f"    Appts: {s['total']} | Completed: {s['completed']} | "
              f"Cancelled: {s['cancelled']}")
        print(f"    Revenue: {c}{s['revenue']:,.2f} | Avg Bill: {c}{s['avg']:,.2f}")
    print(f"  >> Most Requested Doctor: {ds and max(ds.values(), key=lambda x: x['total'])['name']}")
    print(f"  >> Most Requested Spec: {best_spec}\n" + "=" * 48)

    # Print patient report
    print("\n" + "=" * 48 + "\n        PATIENT STATISTICS REPORT\n" + "=" * 48)
    for pid, s in pr["stats"].items():
        print(f"  {pid}: {s['name']}")
        print(f"    Appts: {s['total']} | Completed: {s['completed']} | "
              f"Cancelled: {s['cancelled']}")
        print(f"    Charges: {c}{s['charges']:,.2f} | Insurance: {c}{s['ins_cov']:,.2f} | "
              f"Paid: {c}{s['paid']:,.2f}")
    print(f"  >> Highest Spender: {top_name}")
    print(f"  >> Most Appointments: {pr['most_appts']['name'] if pr['most_appts'] else 'N/A'}")
    print(f"  >> No Completed: {pr['no_completed'] or 'None'}")
    print(f"  >> Insured: {pr['insured']} | Seniors: {pr['seniors']}\n" + "=" * 48)

    # Print clinic dashboard
    print(f"""
========================================
           CLINIC DASHBOARD
========================================
Total Patients: {len(patients)}
Total Doctors: {len(doctors)}
Total Appointments: {len(pa)}
Completed: {len(comp)}
Cancelled: {len([a for a in pa if a['status'] == 'cancelled'])}
Pending: {len([a for a in pa if a['status'] == 'pending'])}
Total Consultation Revenue: {c}{sum(a['consult_fee'] for a in comp):,.2f}
Total Test Revenue: {c}{sum(a['tests_fee'] for a in comp):,.2f}
Total Insurance Coverage: {c}{sum(a['billing']['insurance_covered'] for a in comp):,.2f}
Total Patient Revenue: {c}{sum(a['billing']['patient_pays'] for a in comp):,.2f}
Most Requested Specialization: {best_spec}
Highest Spending Patient: {top_name}
========================================""")

# --- Main ---
def main():
    processed = []
    c = CONFIG["currency"]

    print("=" * 55 + "\n  1. PROCESSING STARTER APPOINTMENTS\n" + "=" * 55)
    for a in appointments:
        ok, r = process_appointment(a["appointment_id"], a["patient_id"],
                                    a["doctor_id"], a["tests"], a["status"])
        if ok:
            processed.append(r)
            print(f"  {r['appointment_id']} -> PROCESSED | Pays: {c}{r['billing']['patient_pays']:,.2f}"
                  f" | Insurance: {c}{r['billing']['insurance_covered']:,.2f}")
        else:
            print(f"  {a['appointment_id']} -> REJECTED | {r}")

    print("\n" + "=" * 55 + "\n  2. EDGE-CASE TESTING\n" + "=" * 55)
    edges = [("A005","P999","D001",[],"completed","Bad patient"),
             ("A006","P001","D999",[],"completed","Bad doctor"),
             ("A007","P001","D001",["InvalidTest"],"completed","Bad test"),
             ("A008","P001","D001",["ECG","ECG"],"completed","Dup tests"),
             ("A009","P001","D001",[],"xyz","Bad status"),
             ("A001","P001","D001",[],"completed","Double process")]
    doctors["D002"]["available"] = False
    edges.append(("A011","P003","D002",[],"pending","Doctor unavailable"))
    for aid, pid, did, tests, st, desc in edges:
        ok, r = process_appointment(aid, pid, did, tests, st)
        print(f"  {aid} -> {'SUCCESS' if ok else 'REJECTED'} | {desc} | "
              f"{'Tests: ' + str(r['tests']) if ok else r}")
        if ok: processed.append(r)
    doctors["D002"]["available"] = True

    print("\n" + "=" * 55 + "\n  3. CANCELLATION RULES\n" + "=" * 55)
    for aid, desc in [("A001","completed"), ("A999","missing")]:
        ok, m = cancel_appointment(aid, processed)
        print(f"  Cancel {aid} ({desc}): {'OK' if ok else 'FAIL'} -> {m}")
    ok, r = process_appointment("A010", "P002", "D002", [], "pending")
    if ok: processed.append(r)
    ok, m = cancel_appointment("A010", processed)
    print(f"  Cancel A010 (pending): {'OK' if ok else 'FAIL'} -> {m}")
    ok, m = cancel_appointment("A010", processed)
    print(f"  Cancel A010 (again):   {'OK' if ok else 'FAIL'} -> {m}")

    print("\n" + "=" * 55 + "\n  4. *args DEMO\n" + "=" * 55)
    print(f"  calculate_total(5000, 1500, 1000) = {calculate_total(5000, 1500, 1000)}")
    print(f"  calculate_total(8000) = {calculate_total(8000)}")
    print(f"  calculate_total() = {calculate_total()}")

    print("\n" + "=" * 55 + "\n  5. **kwargs DEMO\n" + "=" * 55)
    b1 = calculate_bill(5000, insurance=True, senior_discount=True, include_tests=True, tests_fee=2500)
    b2 = calculate_bill(5000, insurance=False, senior_discount=False)
    b3 = calculate_bill(3000, insurance=True, include_tests=False)
    print(f"  Insured senior w/ tests: {c}{b1['patient_pays']:,.2f}")
    print(f"  No insurance/senior:     {c}{b2['patient_pays']:,.2f}")
    print(f"  Insured, no tests:       {c}{b3['patient_pays']:,.2f}")

    print("\n" + "=" * 55 + "\n  6. FULL CLINIC DASHBOARD\n" + "=" * 55)
    display_dashboard(processed)

if __name__ == "__main__":
    main()