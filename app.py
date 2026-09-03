import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from database import (
    create_tables,
    add_employee,
    get_employees,
    delete_employee,
    get_employee_by_email,
    update_employee,
    create_recruitment_table,
    add_candidate,
    get_candidates,
    update_candidate,
    get_candidate_history,
    create_onboarding_table,
    create_onboarding,
    get_onboarding,
    update_onboarding,
    create_leave_table,
    add_leave,
    get_leaves,
    update_leave_status,
    get_hr_statistics,
    get_time_to_hire_stats,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI HR System",
    page_icon="👥",
    layout="wide",
)


# ============================================================
# GOOGLE LOGIN
# ============================================================

if not st.user.is_logged_in:
    st.title("🔐 AI HR System")
    st.subheader("Σύνδεση στο HR System")
    st.write("Συνδέσου με Google για να συνεχίσεις.")
    st.button("🔑 Σύνδεση με Google", on_click=st.login)
    st.stop()


# ============================================================
# USER / ROLE
# ============================================================

user_email = (st.user.email or "").strip().lower()

def _get_secret_list(key):
    value = st.secrets.get("roles", {}).get(key, [])
    if isinstance(value, str):
        return [value.strip().lower()]
    return [str(item).strip().lower() for item in value]

admin_emails = _get_secret_list("admin_emails")
hr_emails = _get_secret_list("hr_emails")

if user_email in admin_emails:
    user_role = "Admin"
elif user_email in hr_emails:
    user_role = "HR"
else:
    user_role = "Employee"

IS_ADMIN = user_role == "Admin"
IS_HR = user_role in ["Admin", "HR"]
IS_EMPLOYEE = user_role == "Employee"


# ============================================================
# SIDEBAR
# ============================================================

display_name = getattr(st.user, "name", None) or user_email

st.sidebar.success(f"👤 {display_name}")
st.sidebar.info(f"Ρόλος: {user_role}")

if st.sidebar.button("🚪 Αποσύνδεση"):
    st.logout()

st.sidebar.title("🤖 AI HR System")
st.sidebar.markdown("---")

if IS_HR:
    menu_options = [
        "📊 Dashboard",
        "👥 Εργαζόμενοι",
        "📋 Recruitment",
        "🚀 Onboarding",
        "🏖️ Άδειες",
        "🤖 AI Assistant",
    ]
else:
    menu_options = [
        "👤 Το προφίλ μου",
        "🏖️ Οι άδειές μου",
        "🤖 AI Assistant",
    ]

page = st.sidebar.radio("Μενού", menu_options)
st.sidebar.markdown("---")
st.sidebar.caption("AI HR Management System")


# ============================================================
# OPENAI
# ============================================================

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None

client = OpenAI(api_key=api_key) if api_key else None



# ============================================================
# HELPERS
# ============================================================

def parse_date(value, default=None):
    if default is None:
        default = date.today()

    if not value:
        return default

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            pass

    return default


def format_date(value):
    if not value:
        return "-"
    return parse_date(value).strftime("%d/%m/%Y")


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@st.cache_resource
def initialize_database():
    create_tables()
    create_recruitment_table()
    create_onboarding_table()
    create_leave_table()
    return True

initialize_database()


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("📊 HR Dashboard")
    st.caption("Κεντρική εικόνα του τμήματος Ανθρώπινου Δυναμικού.")

    employees = get_employees()
    candidates = get_candidates()
    leaves = get_leaves()
    onboarding_rows = get_onboarding()

    try:
        time_to_hire_data = get_time_to_hire_stats()
    except Exception:
        time_to_hire_data = []

    departments = sorted({
        employee.get("department")
        for employee in employees
        if employee.get("department")
    })

    department_filter = st.selectbox(
        "🏢 Φίλτρο τμήματος",
        ["Όλα"] + departments,
    )

    if department_filter == "Όλα":
        filtered_employees = employees
    else:
        filtered_employees = [
            employee
            for employee in employees
            if employee.get("department") == department_filter
        ]

    filtered_total = len(filtered_employees)
    filtered_active = sum(
        1
        for employee in filtered_employees
        if employee.get("status") == "Ενεργός"
    )
    filtered_inactive = sum(
        1
        for employee in filtered_employees
        if employee.get("status") == "Ανενεργός"
    )

    active_rate = (
        filtered_active / filtered_total * 100
        if filtered_total
        else 0
    )

    total_candidates = len(candidates)
    hired_candidates = sum(
        1
        for candidate in candidates
        if candidate.get("status") == "Προσλήφθηκε"
    )
    pending_leaves = sum(
        1
        for leave in leaves
        if leave.get("status") == "Εκκρεμεί"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👥 Σύνολο εργαζομένων", filtered_total)
    with col2:
        st.metric("✅ Ενεργοί", filtered_active)
    with col3:
        st.metric("📋 Υποψήφιοι", total_candidates)
    with col4:
        st.metric("⏳ Εκκρεμείς άδειες", pending_leaves)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("❌ Ανενεργοί", filtered_inactive)
    with col2:
        st.metric("🎯 Προσλήψεις", hired_candidates)
    with col3:
        st.metric("🏖️ Σύνολο αδειών", len(leaves))
    with col4:
        st.metric("📈 Active Rate", f"{active_rate:.1f}%")

    # ========================================================
    # EMPLOYEE TURNOVER
    # ========================================================

    st.divider()
    st.subheader("📉 Employee Turnover")

    current_year = date.today().year
    year_start = date(current_year, 1, 1)

    departures_this_year = []

    for employee in filtered_employees:
        termination_value = employee.get("termination_date")

        if not termination_value:
            continue

        termination_date_obj = parse_date(termination_value)

        if termination_date_obj.year == current_year:
            departures_this_year.append(employee)

    headcount_start = 0

    for employee in filtered_employees:
        hire_value = employee.get("hire_date")

        if not hire_value:
            continue

        hire_date_obj = parse_date(hire_value)
        termination_value = employee.get("termination_date")

        termination_date_obj = (
            parse_date(termination_value)
            if termination_value
            else None
        )

        if (
            hire_date_obj < year_start
            and (
                termination_date_obj is None
                or termination_date_obj >= year_start
            )
        ):
            headcount_start += 1

    headcount_now = filtered_active
    average_headcount = (headcount_start + headcount_now) / 2

    turnover_rate = (
        len(departures_this_year) / average_headcount * 100
        if average_headcount > 0
        else 0
    )

    t1, t2, t3, t4 = st.columns(4)
    t1.metric(f"Turnover Rate {current_year}", f"{turnover_rate:.1f}%")
    t2.metric("Αποχωρήσεις", len(departures_this_year))
    t3.metric("Headcount αρχής έτους", headcount_start)
    t4.metric("Τωρινό Headcount", headcount_now)

    if departures_this_year:
        reason_counts = {}

        for employee in departures_this_year:
            reason = employee.get("termination_reason") or "Άλλο"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        st.write("#### Αποχωρήσεις ανά λόγο")

        reason_df = pd.DataFrame(
            {
                "Λόγος": list(reason_counts.keys()),
                "Αποχωρήσεις": list(reason_counts.values()),
            }
        ).set_index("Λόγος")

        st.bar_chart(reason_df)

        departure_rows = [
            {
                "Εργαζόμενος": (
                    f"{employee.get('first_name', '')} "
                    f"{employee.get('last_name', '')}"
                ).strip(),
                "Θέση": employee.get("position") or "-",
                "Τμήμα": employee.get("department") or "-",
                "Ημερομηνία αποχώρησης": format_date(
                    employee.get("termination_date")
                ),
                "Λόγος": employee.get("termination_reason") or "-",
            }
            for employee in departures_this_year
        ]

        st.dataframe(
            pd.DataFrame(departure_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(f"Δεν υπάρχουν καταχωρημένες αποχωρήσεις για το {current_year}.")

    # ========================================================
    # TIME TO HIRE
    # ========================================================

    st.divider()
    st.subheader("⏱️ Time to Hire")

    if time_to_hire_data:
        average_time_to_hire = round(
            sum(item["days_to_hire"] for item in time_to_hire_data)
            / len(time_to_hire_data),
            1,
        )
        fastest_hire = min(
            item["days_to_hire"]
            for item in time_to_hire_data
        )
        slowest_hire = max(
            item["days_to_hire"]
            for item in time_to_hire_data
        )

        h1, h2, h3 = st.columns(3)
        h1.metric("Μέσο Time to Hire", f"{average_time_to_hire} ημέρες")
        h2.metric("Ταχύτερη πρόσληψη", f"{fastest_hire} ημέρες")
        h3.metric("Μεγαλύτερο Time to Hire", f"{slowest_hire} ημέρες")

        time_to_hire_df = pd.DataFrame(
            [
                {
                    "Υποψήφιος": (
                        f"{item.get('first_name', '')} "
                        f"{item.get('last_name', '')}"
                    ).strip(),
                    "Θέση": item.get("position") or "-",
                    "Ημερομηνία αίτησης": (
                        item["application_date"].strftime("%d/%m/%Y")
                        if item.get("application_date")
                        else "-"
                    ),
                    "Ημερομηνία πρόσληψης": (
                        item["hired_date"].strftime("%d/%m/%Y")
                        if item.get("hired_date")
                        else "-"
                    ),
                    "Time to Hire": f"{item['days_to_hire']} ημέρες",
                }
                for item in time_to_hire_data
            ]
        )

        st.dataframe(
            time_to_hire_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Δεν υπάρχουν ακόμη αρκετά δεδομένα για υπολογισμό Time to Hire.")

    # ========================================================
    # WORKFORCE ANALYTICS
    # ========================================================

    st.divider()
    st.subheader("👥 Εργαζόμενοι ανά τμήμα")

    if employees:
        df = pd.DataFrame(employees)
        counts = (
            df["department"]
            .fillna("Χωρίς τμήμα")
            .replace("", "Χωρίς τμήμα")
            .value_counts()
        )
        st.bar_chart(counts)
    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")

    st.divider()
    st.subheader("📊 Κατάσταση εργαζομένων")

    if filtered_employees:
        df = pd.DataFrame(filtered_employees)
        st.bar_chart(
            df["status"]
            .fillna("Άγνωστη κατάσταση")
            .value_counts()
        )
    else:
        st.info("Δεν υπάρχουν δεδομένα για το συγκεκριμένο φίλτρο.")

    # ========================================================
    # RECRUITMENT
    # ========================================================

    st.divider()
    st.subheader("📋 Recruitment")

    if candidates:
        df = pd.DataFrame(candidates)
        st.bar_chart(
            df["status"]
            .fillna("Άγνωστη κατάσταση")
            .value_counts()
        )
    else:
        st.info("Δεν υπάρχουν υποψήφιοι.")

    st.subheader("🎯 Recruitment Funnel")

    if candidates:
        df = pd.DataFrame(candidates)

        funnel_order = [
            "Νέα αίτηση",
            "Σε αξιολόγηση",
            "Συνέντευξη",
            "Προσφορά",
            "Προσλήφθηκε",
            "Απορρίφθηκε",
        ]

        funnel = (
            df["status"]
            .value_counts()
            .reindex(funnel_order, fill_value=0)
        )

        st.bar_chart(funnel)

        total = len(df)
        hired = int(
            (df["status"] == "Προσλήφθηκε").sum()
        )

        st.metric(
            "📈 Ποσοστό πρόσληψης",
            f"{(hired / total * 100) if total else 0:.1f}%",
        )
    else:
        st.info("Δεν υπάρχουν δεδομένα recruitment.")

    # ========================================================
    # LEAVES
    # ========================================================

    st.divider()
    st.subheader("🏖️ Leave Analytics")

    if leaves:
        df = pd.DataFrame(leaves)
        approved = int(
            (df["status"] == "Εγκρίθηκε").sum()
        )
        rejected = int(
            (df["status"] == "Απορρίφθηκε").sum()
        )
        pending = int(
            (df["status"] == "Εκκρεμεί").sum()
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("✅ Εγκεκριμένες", approved)
        with c2:
            st.metric("❌ Απορριφθείσες", rejected)
        with c3:
            st.metric("⏳ Εκκρεμείς", pending)
    else:
        st.info("Δεν υπάρχουν αιτήματα άδειας.")

    # ========================================================
    # ONBOARDING
    # ========================================================

    st.divider()
    st.subheader("🚀 Onboarding")

    if onboarding_rows:
        onboarding_completed = 0
        onboarding_in_progress = 0
        onboarding_not_started = 0

        for row in onboarding_rows:
            completed = sum(
                int(bool(row.get(key)))
                for key in [
                    "contract",
                    "documents",
                    "email",
                    "equipment",
                    "system_access",
                    "training",
                    "manager_meeting",
                ]
            )

            if completed == 7:
                onboarding_completed += 1
            elif completed > 0:
                onboarding_in_progress += 1
            else:
                onboarding_not_started += 1

        o1, o2, o3 = st.columns(3)
        o1.metric("Δεν ξεκίνησε", onboarding_not_started)
        o2.metric("Σε εξέλιξη", onboarding_in_progress)
        o3.metric("Ολοκληρώθηκε", onboarding_completed)
    else:
        st.info("Δεν υπάρχουν onboarding διαδικασίες.")

    # ========================================================
    # RECENT EMPLOYEES
    # ========================================================

    st.divider()
    st.subheader("👤 Πρόσφατοι εργαζόμενοι")

    if filtered_employees:
        recent_rows = [
            {
                "Όνομα": employee.get("first_name"),
                "Επώνυμο": employee.get("last_name"),
                "Email": employee.get("email"),
                "Θέση": employee.get("position"),
                "Τμήμα": employee.get("department"),
                "Κατάσταση": employee.get("status"),
                "Πρόσληψη": format_date(employee.get("hire_date")),
                "Αποχώρηση": format_date(employee.get("termination_date")),
            }
            for employee in filtered_employees[:10]
        ]

        st.dataframe(
            pd.DataFrame(recent_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")


# ============================================================
# EMPLOYEE PROFILE
# ============================================================

elif page == "👤 Το προφίλ μου":

    st.title("👤 Το προφίλ μου")
    employee = get_employee_by_email(user_email)

    if employee is None:
        st.warning("Δεν βρέθηκε εργαζόμενος με αυτό το Google email. Επικοινώνησε με το HR.")
    else:
        st.subheader(f"{employee['first_name']} {employee['last_name']}")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Όνομα:**", employee["first_name"] or "-")
            st.write("**Επώνυμο:**", employee["last_name"] or "-")
            st.write("**Email:**", employee["email"] or "-")
            st.write("**Τηλέφωνο:**", employee["phone"] or "-")
        with c2:
            st.write("**Θέση:**", employee["position"] or "-")
            st.write("**Τμήμα:**", employee["department"] or "-")
            st.write("**Ημερομηνία πρόσληψης:**", employee["hire_date"] or "-")
            st.write("**Κατάσταση:**", employee["status"] or "-")


# ============================================================
# EMPLOYEE LEAVES
# ============================================================

elif page == "🏖️ Οι άδειές μου":

    st.title("🏖️ Οι άδειές μου")
    employee = get_employee_by_email(user_email)

    if employee is None:
        st.warning("Δεν βρέθηκε εργαζόμενος με αυτό το Google email. Επικοινώνησε με το HR.")
    else:
        leaves = [
            leave for leave in get_leaves()
            if leave["employee_id"] == employee["id"]
        ]

        st.subheader("📋 Ιστορικό αδειών")
        if leaves:
            rows = [{
                "Τύπος": l["leave_type"],
                "Από": l["start_date"],
                "Έως": l["end_date"],
                "Αιτιολογία": l["reason"] or "-",
                "Κατάσταση": l["status"],
            } for l in leaves]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν καταχωρημένες άδειες.")

        st.divider()
        st.subheader("➕ Νέο αίτημα άδειας")
        with st.form("employee_leave_request"):
            leave_type = st.selectbox("Τύπος άδειας", [
                "Κανονική", "Αναρρωτική", "Άδεια άνευ αποδοχών", "Ειδική"
            ])
            c1, c2 = st.columns(2)
            with c1:
                start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            with c2:
                end_date = st.date_input("Ημερομηνία λήξης", value=date.today(), format="DD/MM/YYYY")
            reason = st.text_area("Αιτιολογία")
            submitted = st.form_submit_button("📤 Υποβολή αιτήματος")

            if submitted:
                if end_date < start_date:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την ημερομηνία έναρξης.")
                else:
                    add_leave(
                        employee["id"], leave_type,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        reason, "Εκκρεμεί"
                    )
                    st.success("✅ Το αίτημα άδειας υποβλήθηκε.")
                    st.rerun()


# ============================================================
# EMPLOYEES
# ============================================================

elif page == "👥 Εργαζόμενοι":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("👥 Διαχείριση Εργαζομένων")

    st.subheader("➕ Προσθήκη εργαζομένου")
    with st.form("employee_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Όνομα")
            last_name = st.text_input("Επώνυμο")
            email = st.text_input("Email")
            phone = st.text_input("Τηλέφωνο")
        with c2:
            position = st.text_input("Θέση")
            department = st.text_input("Τμήμα")
            hire_date = st.date_input("Ημερομηνία πρόσληψης", value=date.today(), format="DD/MM/YYYY")
            status = st.selectbox("Κατάσταση", ["Ενεργός", "Ανενεργός", "Σε άδεια"])

        submitted = st.form_submit_button("💾 Αποθήκευση εργαζομένου")
        if submitted:
            if not first_name.strip() or not last_name.strip():
                st.error("Το Όνομα και το Επώνυμο είναι υποχρεωτικά.")
            else:
                try:
                    add_employee(
                        first_name.strip(), last_name.strip(),
                        email.strip().lower() or None,
                        phone.strip(), position.strip(), department.strip(),
                        hire_date.strftime("%Y-%m-%d"), status
                    )
                    st.success("✅ Ο εργαζόμενος προστέθηκε.")
                    st.rerun()
                except Exception as e:
                    if "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                        st.error("❌ Υπάρχει ήδη εργαζόμενος με αυτό το email.")
                    else:
                        st.error(f"❌ Σφάλμα αποθήκευσης: {e}")

    st.divider()
    st.subheader("📋 Λίστα εργαζομένων")
    employees = get_employees()

    if employees:
        search_text = st.text_input("🔎 Αναζήτηση", placeholder="Όνομα, επώνυμο ή email...")
        dept_options = sorted({e.get("department") for e in employees if e.get("department")})
        selected_department = st.selectbox("🏢 Τμήμα", ["Όλα"] + dept_options)
        selected_status = st.selectbox("📌 Κατάσταση", ["Όλες", "Ενεργός", "Ανενεργός", "Σε άδεια"])

        filtered_employees = employees
        if search_text.strip():
            q = search_text.strip().lower()
            filtered_employees = [
                e for e in filtered_employees
                if q in (e.get("first_name") or "").lower()
                or q in (e.get("last_name") or "").lower()
                or q in (e.get("email") or "").lower()
            ]
        if selected_department != "Όλα":
            filtered_employees = [e for e in filtered_employees if e.get("department") == selected_department]
        if selected_status != "Όλες":
            filtered_employees = [e for e in filtered_employees if e.get("status") == selected_status]

        st.caption(f"Βρέθηκαν {len(filtered_employees)} εργαζόμενοι.")

        table = [{
            "ID": e["id"],
            "Όνομα": e["first_name"],
            "Επώνυμο": e["last_name"],
            "Email": e["email"],
            "Τηλέφωνο": e["phone"],
            "Θέση": e["position"],
            "Τμήμα": e["department"],
            "Ημερομηνία πρόσληψης": format_date(e.get("hire_date")),
            "Κατάσταση": e["status"],
            "Ημερομηνία αποχώρησης": format_date(e.get("termination_date")),
            "Λόγος αποχώρησης": e.get("termination_reason") or "-",
        } for e in filtered_employees]
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("👤 Employee Profile")

        if filtered_employees:
            profile_options = {
                f'{e["first_name"]} {e["last_name"]} — {e["position"] or "Χωρίς θέση"} (ID: {e["id"]})': e
                for e in filtered_employees
            }
            profile_label = st.selectbox("Επίλεξε εργαζόμενο", list(profile_options.keys()), key="employee_profile_selector")
            selected_employee = profile_options[profile_label]

            all_leaves = get_leaves()
            all_onboarding = get_onboarding()
            employee_leaves = [l for l in all_leaves if l["employee_id"] == selected_employee["id"]]
            employee_onboarding = [o for o in all_onboarding if o["employee_id"] == selected_employee["id"]]
            approved = sum(1 for l in employee_leaves if l["status"] == "Εγκρίθηκε")
            pending = sum(1 for l in employee_leaves if l["status"] == "Εκκρεμεί")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📌 Κατάσταση", selected_employee["status"] or "-")
            with c2:
                st.metric("🏖️ Σύνολο αδειών", len(employee_leaves))
            with c3:
                st.metric("✅ Εγκεκριμένες", approved)
            with c4:
                st.metric("⏳ Εκκρεμείς", pending)

            tab1, tab2, tab3, tab4 = st.tabs(["👤 Στοιχεία", "🏖️ Άδειες", "🚀 Onboarding", "📋 Ιστορικό"])

            with tab1:
                with st.form(f"edit_employee_{selected_employee['id']}"):
                    c1, c2 = st.columns(2)

                    with c1:
                        edit_first = st.text_input(
                            "Όνομα",
                            value=selected_employee["first_name"] or "",
                        )
                        edit_last = st.text_input(
                            "Επώνυμο",
                            value=selected_employee["last_name"] or "",
                        )
                        edit_email = st.text_input(
                            "Email",
                            value=selected_employee["email"] or "",
                        )
                        edit_phone = st.text_input(
                            "Τηλέφωνο",
                            value=selected_employee["phone"] or "",
                        )

                    with c2:
                        edit_position = st.text_input(
                            "Θέση",
                            value=selected_employee["position"] or "",
                        )
                        edit_department = st.text_input(
                            "Τμήμα",
                            value=selected_employee["department"] or "",
                        )
                        edit_hire = st.date_input(
                            "Ημερομηνία πρόσληψης",
                            value=parse_date(selected_employee.get("hire_date")),
                            format="DD/MM/YYYY",
                        )

                        status_options = [
                            "Ενεργός",
                            "Ανενεργός",
                            "Σε άδεια",
                        ]

                        current_status = (
                            selected_employee.get("status")
                            or "Ενεργός"
                        )

                        edit_status = st.selectbox(
                            "Κατάσταση",
                            status_options,
                            index=(
                                status_options.index(current_status)
                                if current_status in status_options
                                else 0
                            ),
                        )

                    st.markdown("#### 📉 Στοιχεία αποχώρησης")
                    st.caption(
                        "Τα παρακάτω αποθηκεύονται μόνο όταν η κατάσταση είναι «Ανενεργός»."
                    )

                    term1, term2 = st.columns(2)

                    termination_date_value = term1.date_input(
                        "Ημερομηνία αποχώρησης",
                        value=parse_date(
                            selected_employee.get("termination_date"),
                            date.today(),
                        ),
                        format="DD/MM/YYYY",
                    )

                    termination_reasons = [
                        "Παραίτηση",
                        "Απόλυση",
                        "Λήξη σύμβασης",
                        "Συνταξιοδότηση",
                        "Άλλο",
                    ]

                    current_reason = selected_employee.get(
                        "termination_reason"
                    )

                    reason_index = (
                        termination_reasons.index(current_reason)
                        if current_reason in termination_reasons
                        else 0
                    )

                    termination_reason_value = term2.selectbox(
                        "Λόγος αποχώρησης",
                        termination_reasons,
                        index=reason_index,
                    )

                    save = st.form_submit_button(
                        "💾 Αποθήκευση αλλαγών"
                    )

                    if save:
                        if (
                            edit_status == "Ανενεργός"
                            and termination_date_value < edit_hire
                        ):
                            st.error(
                                "Η ημερομηνία αποχώρησης δεν μπορεί να είναι πριν από την ημερομηνία πρόσληψης."
                            )
                        else:
                            try:
                                update_employee(
                                    selected_employee["id"],
                                    edit_first.strip(),
                                    edit_last.strip(),
                                    edit_email.strip().lower() or None,
                                    edit_phone.strip(),
                                    edit_position.strip(),
                                    edit_department.strip(),
                                    edit_hire.strftime("%Y-%m-%d"),
                                    edit_status,
                                    (
                                        termination_date_value.strftime("%Y-%m-%d")
                                        if edit_status == "Ανενεργός"
                                        else None
                                    ),
                                    (
                                        termination_reason_value
                                        if edit_status == "Ανενεργός"
                                        else None
                                    ),
                                )

                                st.success(
                                    "✅ Τα στοιχεία ενημερώθηκαν."
                                )
                                st.rerun()

                            except Exception as e:
                                if (
                                    "UniqueViolation" in str(e)
                                    or "duplicate key" in str(e).lower()
                                ):
                                    st.error(
                                        "❌ Υπάρχει ήδη εργαζόμενος με αυτό το email."
                                    )
                                else:
                                    st.error(
                                        f"❌ Σφάλμα ενημέρωσης: {e}"
                                    )

            with tab2:
                if employee_leaves:
                    rows = [{
                        "Τύπος": l["leave_type"], "Από": l["start_date"], "Έως": l["end_date"],
                        "Αιτιολογία": l["reason"] or "-", "Κατάσταση": l["status"]
                    } for l in employee_leaves]
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Δεν υπάρχουν άδειες.")

            with tab3:
                if employee_onboarding:
                    for item in employee_onboarding:
                        completed = sum(bool(item[k]) for k in ["contract", "documents", "email", "equipment", "system_access", "training", "manager_meeting"])
                        st.write(f"**Ημερομηνία έναρξης:** {item['start_date'] or '-'}")
                        st.progress(completed / 7)
                        st.write(f"**Ολοκλήρωση:** {completed}/7 ({completed / 7 * 100:.0f}%)")
                        st.write(f"📄 Σύμβαση: {'✅' if item['contract'] else '❌'}")
                        st.write(f"📁 Έγγραφα: {'✅' if item['documents'] else '❌'}")
                        st.write(f"📧 Email: {'✅' if item['email'] else '❌'}")
                        st.write(f"💻 Εξοπλισμός: {'✅' if item['equipment'] else '❌'}")
                        st.write(f"🔐 Πρόσβαση: {'✅' if item['system_access'] else '❌'}")
                        st.write(f"🎓 Εκπαίδευση: {'✅' if item['training'] else '❌'}")
                        st.write(f"🤝 Manager Meeting: {'✅' if item['manager_meeting'] else '❌'}")
                        st.divider()
                else:
                    st.info("Δεν υπάρχει onboarding.")

            with tab4:
                st.write(f"📅 Ημερομηνία πρόσληψης: {selected_employee['hire_date'] or '-'}")
                st.write(f"🏢 Τμήμα: {selected_employee['department'] or '-'}")
                st.write(f"💼 Θέση: {selected_employee['position'] or '-'}")
                st.write(f"📌 Κατάσταση: {selected_employee['status'] or '-'}")
                st.write(
                    f"📉 Ημερομηνία αποχώρησης: "
                    f"{format_date(selected_employee.get('termination_date'))}"
                )
                st.write(
                    f"📝 Λόγος αποχώρησης: "
                    f"{selected_employee.get('termination_reason') or '-'}"
                )
                st.write(f"🏖️ Αιτήματα άδειας: {len(employee_leaves)}")
                st.write(f"✅ Εγκεκριμένες άδειες: {approved}")
                st.write(f"⏳ Εκκρεμή αιτήματα: {pending}")
                st.write(f"🚀 Onboarding: {'Υπάρχει' if employee_onboarding else 'Δεν υπάρχει'}")

        st.divider()
        st.subheader("🗑️ Διαγραφή εργαζομένου")
        delete_options = {
            f'{e["first_name"]} {e["last_name"]} (ID: {e["id"]})': e["id"]
            for e in employees
        }
        selected_delete = st.selectbox("Επίλεξε εργαζόμενο", list(delete_options.keys()), key="delete_employee_selector")
        if st.button("🗑️ Διαγραφή εργαζομένου"):
            delete_employee(delete_options[selected_delete])
            st.success("✅ Ο εργαζόμενος διαγράφηκε.")
            st.rerun()
    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")


# ============================================================
# RECRUITMENT
# ============================================================

elif page == "📋 Recruitment":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("📋 Recruitment")
    st.caption("Διαχείριση υποψηφίων και pipeline προσλήψεων.")

    candidates = get_candidates()
    pipeline_statuses = [
        "Νέα αίτηση", "Σε αξιολόγηση", "Συνέντευξη",
        "Προσφορά", "Προσλήφθηκε", "Απορρίφθηκε"
    ]

    st.subheader("➕ Νέος υποψήφιος")
    with st.form("candidate_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Όνομα")
            last_name = st.text_input("Επώνυμο")
            email = st.text_input("Email")
            phone = st.text_input("Τηλέφωνο")
        with c2:
            position = st.text_input("Θέση εργασίας")
            application_date = st.date_input("Ημερομηνία αίτησης", value=date.today(), format="DD/MM/YYYY")
            recruiter = st.text_input("👤 Recruiter")
            initial_status = st.selectbox("Κατάσταση", pipeline_statuses)
        submitted = st.form_submit_button("💾 Προσθήκη υποψηφίου")

        if submitted:
            if not first_name.strip() or not last_name.strip():
                st.error("Το Όνομα και το Επώνυμο είναι υποχρεωτικά.")
            else:
                add_candidate(
                    first_name.strip(), last_name.strip(), email.strip() or None,
                    phone.strip(), position.strip(), application_date.strftime("%Y-%m-%d"),
                    initial_status, None, None, None, recruiter.strip() or None
                )
                st.success("✅ Ο υποψήφιος προστέθηκε.")
                st.rerun()

    st.divider()
    st.subheader("🎯 Recruitment Pipeline")
    pipeline_counts = {status: 0 for status in pipeline_statuses}
    for candidate in candidates:
        if candidate.get("status") in pipeline_counts:
            pipeline_counts[candidate["status"]] += 1
    cols = st.columns(6)
    for i, status in enumerate(pipeline_statuses):
        with cols[i]:
            st.metric(status, pipeline_counts[status])

    st.divider()
    st.subheader("🔎 Αναζήτηση υποψηφίων")
    c1, c2 = st.columns(2)
    with c1:
        search_text = st.text_input("Όνομα, επώνυμο ή email", placeholder="Αναζήτηση...")
    with c2:
        status_filter = st.selectbox("📌 Κατάσταση", ["Όλες"] + pipeline_statuses)

    filtered_candidates = candidates
    if search_text.strip():
        q = search_text.strip().lower()
        filtered_candidates = [
            c for c in filtered_candidates
            if q in (c.get("first_name") or "").lower()
            or q in (c.get("last_name") or "").lower()
            or q in (c.get("email") or "").lower()
        ]
    if status_filter != "Όλες":
        filtered_candidates = [c for c in filtered_candidates if c.get("status") == status_filter]

    st.caption(f"Βρέθηκαν {len(filtered_candidates)} υποψήφιοι.")

    st.subheader("📊 Pipeline")
    visible_pipeline = ["Νέα αίτηση", "Σε αξιολόγηση", "Συνέντευξη", "Προσφορά", "Προσλήφθηκε"]
    columns = st.columns(len(visible_pipeline))
    for i, stage in enumerate(visible_pipeline):
        with columns[i]:
            st.markdown(f"### {stage}")
            stage_candidates = [c for c in filtered_candidates if c.get("status") == stage]
            if not stage_candidates:
                st.caption("Κανένας υποψήφιος")
            for candidate in stage_candidates:
                with st.container(border=True):
                    st.write(f"**{candidate['first_name']} {candidate['last_name']}**")
                    st.caption(candidate.get("position") or "Χωρίς θέση")
                    if candidate.get("email"):
                        st.write(f"📧 {candidate['email']}")
                    if candidate.get("rating"):
                        st.write(f"⭐ {candidate['rating']}/5")

    st.divider()
    st.subheader("⚙️ Διαχείριση υποψηφίου")

    if filtered_candidates:
        options = {
            f'{c["first_name"]} {c["last_name"]} (ID: {c["id"]})': c
            for c in filtered_candidates
        }
        selected_label = st.selectbox("Επίλεξε υποψήφιο", list(options.keys()), key="candidate_selector")
        candidate = options[selected_label]

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"📧 **Email:** {candidate.get('email') or '-'}")
            st.write(f"📞 **Τηλέφωνο:** {candidate.get('phone') or '-'}")
            st.write(f"💼 **Θέση:** {candidate.get('position') or '-'}")
        with c2:
            st.write(f"📅 **Αίτηση:** {candidate.get('application_date') or '-'}")
            st.write(f"👤 **Recruiter:** {candidate.get('recruiter') or '-'}")

        with st.form(f"candidate_management_{candidate['id']}"):
            new_status = st.selectbox(
                "🔄 Κατάσταση",
                pipeline_statuses,
                index=pipeline_statuses.index(candidate["status"]) if candidate["status"] in pipeline_statuses else 0,
            )
            interview_date = st.text_input(
                "📅 Ημερομηνία συνέντευξης",
                value=candidate.get("interview_date") or "",
                placeholder="π.χ. 10/09/2026 11:00",
            )
            rating = st.select_slider(
                "⭐ Βαθμολογία",
                options=[1, 2, 3, 4, 5],
                value=candidate.get("rating") if candidate.get("rating") in [1, 2, 3, 4, 5] else 3,
            )
            recruiter_edit = st.text_input("👤 Recruiter", value=candidate.get("recruiter") or "")
            notes = st.text_area("📝 Σημειώσεις HR", value=candidate.get("notes") or "", height=140)

            save_candidate = st.form_submit_button("💾 Αποθήκευση")
            if save_candidate:
                try:
                    update_candidate(
                        candidate["id"], new_status, user_email,
                        interview_date.strip() or None, rating,
                        notes.strip() or None, recruiter_edit.strip() or None
                    )
                    st.success("✅ Τα στοιχεία του υποψηφίου ενημερώθηκαν.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Σφάλμα ενημέρωσης: {e}")

        st.divider()
        st.subheader("📋 Ιστορικό υποψηφίου")
        history = get_candidate_history(candidate["id"])
        if history:
            history_rows = [{
                "Παλιά κατάσταση": h["old_status"] or "-",
                "Νέα κατάσταση": h["new_status"],
                "Αλλαγή από": h["changed_by"] or "-",
                "Ημερομηνία": str(h["changed_at"]),
            } for h in history]
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχει ιστορικό.")
    else:
        st.info("Δεν υπάρχουν υποψήφιοι με τα συγκεκριμένα φίλτρα.")

    st.divider()
    st.subheader("📋 Πλήρης λίστα υποψηφίων")
    if filtered_candidates:
        rows = [{
            "ID": c["id"],
            "Όνομα": c["first_name"],
            "Επώνυμο": c["last_name"],
            "Email": c["email"],
            "Θέση": c["position"],
            "Recruiter": c.get("recruiter"),
            "Συνέντευξη": c.get("interview_date"),
            "Βαθμολογία": c.get("rating"),
            "Κατάσταση": c["status"],
        } for c in filtered_candidates]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν υποψήφιοι.")


# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("🚀 Employee Onboarding")
    st.caption("Checklist για την ένταξη νέων εργαζομένων.")

    employees = get_employees()
    if not employees:
        st.warning("Πρέπει πρώτα να προσθέσεις εργαζόμενο.")
    else:
        st.subheader("➕ Νέο Onboarding")
        employee_options = {
            f'{e["first_name"]} {e["last_name"]}': e["id"]
            for e in employees
        }
        with st.form("onboarding_form"):
            selected_employee = st.selectbox("Εργαζόμενος", list(employee_options.keys()))
            start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            submitted = st.form_submit_button("🚀 Δημιουργία Onboarding")
            if submitted:
                create_onboarding(employee_options[selected_employee], start_date.strftime("%Y-%m-%d"))
                st.success("✅ Το onboarding δημιουργήθηκε.")
                st.rerun()

        st.divider()
        st.subheader("📋 Onboarding Checklist")
        onboarding = get_onboarding()
        if onboarding:
            for item in onboarding:
                employee_name = f'{item["first_name"]} {item["last_name"]}'
                with st.expander(f"👤 {employee_name}"):
                    st.write(f"**Ημερομηνία έναρξης:** {item['start_date'] or '-'}")
                    contract = st.checkbox("📄 Σύμβαση", value=bool(item["contract"]), key=f"contract_{item['id']}")
                    documents = st.checkbox("📁 Έγγραφα", value=bool(item["documents"]), key=f"documents_{item['id']}")
                    email_setup = st.checkbox("📧 Email", value=bool(item["email"]), key=f"email_{item['id']}")
                    equipment = st.checkbox("💻 Εξοπλισμός", value=bool(item["equipment"]), key=f"equipment_{item['id']}")
                    system_access = st.checkbox("🔐 Πρόσβαση σε συστήματα", value=bool(item["system_access"]), key=f"system_{item['id']}")
                    training = st.checkbox("🎓 Εκπαίδευση", value=bool(item["training"]), key=f"training_{item['id']}")
                    manager_meeting = st.checkbox("🤝 Συνάντηση με Manager", value=bool(item["manager_meeting"]), key=f"manager_{item['id']}")
                    if st.button("💾 Αποθήκευση Checklist", key=f"save_onboarding_{item['id']}"):
                        update_onboarding(item["id"], int(contract), int(documents), int(email_setup), int(equipment), int(system_access), int(training), int(manager_meeting))
                        st.success("✅ Το checklist ενημερώθηκε.")
                        st.rerun()
        else:
            st.info("Δεν υπάρχουν onboarding διαδικασίες.")


# ============================================================
# LEAVES - HR
# ============================================================

elif page == "🏖️ Άδειες":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("🏖️ Διαχείριση Αδειών")
    employees = get_employees()

    if not employees:
        st.warning("Πρέπει πρώτα να προσθέσεις εργαζόμενο.")
    else:
        st.subheader("➕ Νέα αίτηση άδειας")
        employee_options = {
            f'{e["first_name"]} {e["last_name"]}': e["id"]
            for e in employees
        }
        with st.form("leave_form"):
            selected_employee = st.selectbox("Εργαζόμενος", list(employee_options.keys()))
            leave_type = st.selectbox("Τύπος άδειας", ["Κανονική", "Αναρρωτική", "Άδεια άνευ αποδοχών", "Ειδική", "Άλλο"])
            start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            end_date = st.date_input("Ημερομηνία λήξης", value=date.today(), format="DD/MM/YYYY")
            reason = st.text_area("Αιτιολογία")
            submitted = st.form_submit_button("📨 Υποβολή αίτησης")
            if submitted:
                if end_date < start_date:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την ημερομηνία έναρξης.")
                else:
                    add_leave(employee_options[selected_employee], leave_type, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), reason, "Εκκρεμεί")
                    st.success("✅ Η αίτηση άδειας καταχωρήθηκε.")
                    st.rerun()

        st.divider()
        st.subheader("📋 Αιτήσεις αδειών")
        leaves = get_leaves()
        if leaves:
            rows = [{
                "ID": l["id"],
                "Εργαζόμενος": f'{l["first_name"]} {l["last_name"]}',
                "Τύπος": l["leave_type"],
                "Από": l["start_date"],
                "Έως": l["end_date"],
                "Αιτιολογία": l["reason"] or "-",
                "Κατάσταση": l["status"],
            } for l in leaves]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("✅ HR Approval Center")
            pending_leaves = [l for l in leaves if l["status"] == "Εκκρεμεί"]
            if pending_leaves:
                for leave in pending_leaves:
                    with st.container(border=True):
                        st.write(f'**#{leave["id"]} — {leave["first_name"]} {leave["last_name"]}**')
                        st.write(f'Τύπος: {leave["leave_type"]}')
                        st.write(f'Από: {leave["start_date"]} Έως: {leave["end_date"]}')
                        st.write(f'Αιτιολογία: {leave["reason"] or "-"}')
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Έγκριση", key=f"approve_{leave['id']}"):
                                update_leave_status(leave["id"], "Εγκρίθηκε")
                                st.rerun()
                        with c2:
                            if st.button("❌ Απόρριψη", key=f"reject_{leave['id']}"):
                                update_leave_status(leave["id"], "Απορρίφθηκε")
                                st.rerun()
            else:
                st.success("✅ Δεν υπάρχουν εκκρεμή αιτήματα.")
        else:
            st.info("Δεν υπάρχουν αιτήσεις άδειας.")


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title("🤖 AI HR Assistant")
    st.caption("Ο έξυπνος βοηθός του HR.")

    if client is None:
        st.error("Δεν βρέθηκε το OPENAI_API_KEY.")
        st.info("Στο Streamlit Cloud πρόσθεσε το OPENAI_API_KEY στα Secrets.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Γράψε την ερώτησή σου...")

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Το AI σκέφτεται..."):
                    try:
                        response = client.responses.create(
                            model="gpt-5-mini",
                            instructions="""
Είσαι ένας επαγγελματικός AI HR Assistant.

Βοηθάς σε Recruitment, Employee Management, Onboarding,
HR Administration, HR KPIs, HR emails, Job descriptions,
Job advertisements και HR διαδικασίες.

Απαντάς στα ελληνικά εκτός αν ζητηθεί άλλη γλώσσα.
Οι απαντήσεις είναι επαγγελματικές, πρακτικές και σαφείς.
Δεν παρουσιάζεις νομική συμβουλή ως βεβαιότητα.
""",
                            input=question,
                        )
                        answer = response.output_text
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"Παρουσιάστηκε σφάλμα: {e}")

        if st.session_state.messages:
            st.divider()
            if st.button("🗑️ Καθαρισμός συνομιλίας"):
                st.session_state.messages = []
                st.rerun()
