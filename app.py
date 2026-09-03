import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

from database import (
    create_tables,
    add_employee,
    get_employees,
    get_employee_by_email,
    update_employee,
    delete_employee,
    create_recruitment_table,
    add_candidate,
    get_candidates,
    update_candidate,
    get_candidate_history,
    create_employee_from_candidate,
    create_onboarding_table,
    create_onboarding,
    get_onboarding,
    update_onboarding,
    create_leave_table,
    add_leave,
    get_leaves,
    update_leave_status,
    get_hr_statistics,
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
# DATABASE INIT
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
# HELPERS
# ============================================================

def safe_text(value):
    return "" if value is None else str(value)


def format_date(value):
    if not value:
        return ""

    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")

    text = str(value)

    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%d/%m/%Y")
        except Exception:
            pass

    return text


def get_role(user_email):
    email = safe_text(user_email).strip().lower()

    try:
        roles = st.secrets.get("roles", {})
        admin_emails = [str(x).lower() for x in roles.get("admin_emails", [])]
        hr_emails = [str(x).lower() for x in roles.get("hr_emails", [])]
    except Exception:
        admin_emails = []
        hr_emails = []

    if email in admin_emails:
        return "Admin"

    if email in hr_emails:
        return "HR"

    return "Employee"


# ============================================================
# LOGIN
# ============================================================

if not st.user.is_logged_in:
    st.title("👥 AI HR System")
    st.write("Συνδέσου με τον λογαριασμό σου.")

    st.button(
        "🔑 Σύνδεση με Google",
        on_click=st.login,
    )

    st.stop()

user_email = st.user.get("email", "")
user_name = st.user.get("name", user_email)
user_role = get_role(user_email)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🤖 AI HR System")
st.sidebar.write(user_name)
st.sidebar.caption(f"Ρόλος: {user_role}")
st.sidebar.markdown("---")

if user_role in ("Admin", "HR"):
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

page = st.sidebar.radio(
    "Μενού",
    menu_options,
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Αποσύνδεση"):
    st.logout()

# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.title("📊 Dashboard")
    st.markdown("Κεντρική εικόνα του τμήματος Ανθρώπινου Δυναμικού.")

    stats = get_hr_statistics()
    employees = get_employees()
    candidates = get_candidates()
    leaves = get_leaves()

    departments = sorted({
        safe_text(employee.get("department")).strip()
        for employee in employees
        if safe_text(employee.get("department")).strip()
    })

    department_filter = st.selectbox(
        "Τμήμα",
        ["Όλα"] + departments,
    )

    filtered_employees = employees

    if department_filter != "Όλα":
        filtered_employees = [
            employee
            for employee in employees
            if safe_text(employee.get("department")) == department_filter
        ]

    total_employees = len(filtered_employees)

    active_employees = sum(
        1
        for employee in filtered_employees
        if employee.get("status") == "Ενεργός"
    )

    inactive_employees = sum(
        1
        for employee in filtered_employees
        if employee.get("status") == "Ανενεργός"
    )

    active_rate = (
        round((active_employees / total_employees) * 100, 1)
        if total_employees
        else 0
    )

    total_candidates = len(candidates)

    hired_candidates = sum(
        1
        for candidate_row in candidates
        if candidate_row.get("status") == "Προσλήφθηκε"
    )

    pending_leaves = sum(
        1
        for leave in leaves
        if leave.get("status") == "Εκκρεμεί"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("👥 Εργαζόμενοι", total_employees)
    col2.metric("✅ Ενεργοί", active_employees)
    col3.metric("📋 Υποψήφιοι", total_candidates)
    col4.metric("🏖️ Εκκρεμείς άδειες", pending_leaves)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("❌ Ανενεργοί", inactive_employees)
    col2.metric("🎯 Προσλήψεις", hired_candidates)
    col3.metric("🏖️ Σύνολο αδειών", len(leaves))
    col4.metric("📈 Ποσοστό ενεργών", f"{active_rate}%")

    st.markdown("---")

    if filtered_employees:

        employee_df = pd.DataFrame([
            {
                "Όνομα": employee.get("first_name"),
                "Επώνυμο": employee.get("last_name"),
                "Email": employee.get("email"),
                "Θέση": employee.get("position"),
                "Τμήμα": employee.get("department"),
                "Κατάσταση": employee.get("status"),
            }
            for employee in filtered_employees
        ])

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Εργαζόμενοι ανά τμήμα")

            st.bar_chart(
                employee_df["Τμήμα"]
                .fillna("Χωρίς τμήμα")
                .replace("", "Χωρίς τμήμα")
                .value_counts()
            )

        with col2:
            st.subheader("Εργαζόμενοι ανά κατάσταση")

            st.bar_chart(
                employee_df["Κατάσταση"]
                .fillna("Χωρίς κατάσταση")
                .value_counts()
            )

    if candidates:

        st.subheader("📋 Recruitment Funnel")

        recruitment_statuses = [
            "Νέα αίτηση",
            "Σε αξιολόγηση",
            "Συνέντευξη",
            "Προσφορά",
            "Προσλήφθηκε",
            "Απορρίφθηκε",
        ]

        recruitment_data = pd.Series({
            status_name: sum(
                1
                for candidate_row in candidates
                if candidate_row.get("status") == status_name
            )
            for status_name in recruitment_statuses
        })

        st.bar_chart(recruitment_data)

# ============================================================
# EMPLOYEES
# ============================================================

elif page == "👥 Εργαζόμενοι":

    st.title("👥 Εργαζόμενοι")

    add_tab, manage_tab = st.tabs([
        "➕ Προσθήκη",
        "📋 Διαχείριση",
    ])

    with add_tab:

        st.subheader("➕ Προσθήκη εργαζομένου")

        with st.form("employee_form"):

            first_name = st.text_input("Όνομα")
            last_name = st.text_input("Επώνυμο")
            email = st.text_input("Email")
            phone = st.text_input("Τηλέφωνο")
            position = st.text_input("Θέση")
            department = st.text_input("Τμήμα")

            hire_date = st.date_input(
                "Ημερομηνία πρόσληψης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            employee_status = st.selectbox(
                "Κατάσταση",
                [
                    "Ενεργός",
                    "Ανενεργός",
                    "Σε άδεια",
                ],
            )

            submitted = st.form_submit_button(
                "💾 Αποθήκευση εργαζομένου"
            )

            if submitted:

                if not first_name.strip() or not last_name.strip():

                    st.error(
                        "Το Όνομα και το Επώνυμο είναι υποχρεωτικά."
                    )

                else:

                    try:

                        add_employee(
                            first_name.strip(),
                            last_name.strip(),
                            email.strip() or None,
                            phone.strip() or None,
                            position.strip() or None,
                            department.strip() or None,
                            hire_date.strftime("%Y-%m-%d"),
                            employee_status,
                        )

                        st.success(
                            "✅ Ο εργαζόμενος προστέθηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        if (
                            "unique" in str(e).lower()
                            or "duplicate" in str(e).lower()
                        ):
                            st.error(
                                "Υπάρχει ήδη εργαζόμενος με αυτό το email."
                            )
                        else:
                            st.error(
                                f"Σφάλμα: {e}"
                            )

    with manage_tab:

        employees = get_employees()

        if not employees:

            st.info(
                "Δεν υπάρχουν εργαζόμενοι."
            )

        else:

            search = st.text_input(
                "🔎 Αναζήτηση",
                placeholder="Όνομα, επώνυμο ή email",
            )

            departments = sorted({
                safe_text(employee.get("department")).strip()
                for employee in employees
                if safe_text(employee.get("department")).strip()
            })

            col1, col2 = st.columns(2)

            with col1:

                department_filter = st.selectbox(
                    "Τμήμα",
                    ["Όλα"] + departments,
                    key="employee_department_filter",
                )

            with col2:

                employee_status_filter = st.selectbox(
                    "Κατάσταση",
                    [
                        "Όλες",
                        "Ενεργός",
                        "Ανενεργός",
                        "Σε άδεια",
                    ],
                    key="employee_status_filter",
                )

            filtered = employees

            if search.strip():

                query = search.lower().strip()

                filtered = [
                    employee
                    for employee in filtered
                    if (
                        query
                        in safe_text(employee.get("first_name")).lower()
                        or query
                        in safe_text(employee.get("last_name")).lower()
                        or query
                        in safe_text(employee.get("email")).lower()
                    )
                ]

            if department_filter != "Όλα":

                filtered = [
                    employee
                    for employee in filtered
                    if safe_text(employee.get("department"))
                    == department_filter
                ]

            if employee_status_filter != "Όλες":

                filtered = [
                    employee
                    for employee in filtered
                    if employee.get("status")
                    == employee_status_filter
                ]

            st.dataframe(
                pd.DataFrame([
                    {
                        "ID": employee.get("id"),
                        "Όνομα": employee.get("first_name"),
                        "Επώνυμο": employee.get("last_name"),
                        "Email": employee.get("email"),
                        "Τηλέφωνο": employee.get("phone"),
                        "Θέση": employee.get("position"),
                        "Τμήμα": employee.get("department"),
                        "Ημερομηνία πρόσληψης":
                            format_date(employee.get("hire_date")),
                        "Κατάσταση": employee.get("status"),
                    }
                    for employee in filtered
                ]),
                use_container_width=True,
                hide_index=True,
            )

            employee_options = {
                (
                    f'{employee["first_name"]} '
                    f'{employee["last_name"]} '
                    f'(ID: {employee["id"]})'
                ): employee
                for employee in employees
            }

            selected_employee_label = st.selectbox(
                "Επίλεξε εργαζόμενο",
                list(employee_options.keys()),
            )

            selected_employee = employee_options[
                selected_employee_label
            ]

            employee_tabs = st.tabs([
                "👤 Στοιχεία",
                "🏖️ Άδειες",
                "🚀 Onboarding",
                "📋 Ιστορικό",
            ])

            with employee_tabs[0]:

                with st.form(
                    f"edit_employee_{selected_employee['id']}"
                ):

                    edit_first_name = st.text_input(
                        "Όνομα",
                        value=safe_text(
                            selected_employee.get("first_name")
                        ),
                    )

                    edit_last_name = st.text_input(
                        "Επώνυμο",
                        value=safe_text(
                            selected_employee.get("last_name")
                        ),
                    )

                    edit_email = st.text_input(
                        "Email",
                        value=safe_text(
                            selected_employee.get("email")
                        ),
                    )

                    edit_phone = st.text_input(
                        "Τηλέφωνο",
                        value=safe_text(
                            selected_employee.get("phone")
                        ),
                    )

                    edit_position = st.text_input(
                        "Θέση",
                        value=safe_text(
                            selected_employee.get("position")
                        ),
                    )

                    edit_department = st.text_input(
                        "Τμήμα",
                        value=safe_text(
                            selected_employee.get("department")
                        ),
                    )

                    raw_hire_date = selected_employee.get("hire_date")

                    try:
                        hire_date_value = datetime.strptime(
                            str(raw_hire_date)[:10],
                            "%Y-%m-%d",
                        ).date()
                    except Exception:
                        hire_date_value = date.today()

                    edit_hire_date = st.date_input(
                        "Ημερομηνία πρόσληψης",
                        value=hire_date_value,
                        format="DD/MM/YYYY",
                    )

                    employee_statuses = [
                        "Ενεργός",
                        "Ανενεργός",
                        "Σε άδεια",
                    ]

                    current_employee_status = (
                        selected_employee.get("status")
                        or "Ενεργός"
                    )

                    if current_employee_status in employee_statuses:
                        employee_status_index = employee_statuses.index(
                            current_employee_status
                        )
                    else:
                        employee_status_index = 0

                    edit_status = st.selectbox(
                        "Κατάσταση",
                        employee_statuses,
                        index=employee_status_index,
                    )

                    save_employee = st.form_submit_button(
                        "💾 Αποθήκευση αλλαγών"
                    )

                    if save_employee:

                        try:

                            update_employee(
                                selected_employee["id"],
                                edit_first_name.strip(),
                                edit_last_name.strip(),
                                edit_email.strip() or None,
                                edit_phone.strip() or None,
                                edit_position.strip() or None,
                                edit_department.strip() or None,
                                edit_hire_date.strftime("%Y-%m-%d"),
                                edit_status,
                            )

                            st.success(
                                "✅ Τα στοιχεία ενημερώθηκαν."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Σφάλμα ενημέρωσης: {e}"
                            )

                st.markdown("---")

                if st.button(
                    "🗑️ Διαγραφή εργαζομένου",
                    key=(
                        f"delete_employee_"
                        f"{selected_employee['id']}"
                    ),
                ):

                    try:

                        delete_employee(
                            selected_employee["id"]
                        )

                        st.success(
                            "Ο εργαζόμενος διαγράφηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Σφάλμα διαγραφής: {e}"
                        )

            with employee_tabs[1]:

                employee_leaves = [
                    leave
                    for leave in get_leaves()
                    if leave.get("employee_id")
                    == selected_employee["id"]
                ]

                if employee_leaves:

                    st.dataframe(
                        pd.DataFrame([
                            {
                                "Τύπος":
                                    leave.get("leave_type"),
                                "Από":
                                    format_date(
                                        leave.get("start_date")
                                    ),
                                "Έως":
                                    format_date(
                                        leave.get("end_date")
                                    ),
                                "Αιτιολογία":
                                    leave.get("reason"),
                                "Κατάσταση":
                                    leave.get("status"),
                            }
                            for leave in employee_leaves
                        ]),
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "Δεν υπάρχουν αιτήσεις άδειας."
                    )

            with employee_tabs[2]:

                employee_onboarding = [
                    onboarding_row
                    for onboarding_row in get_onboarding()
                    if onboarding_row.get("employee_id")
                    == selected_employee["id"]
                ]

                if employee_onboarding:

                    for onboarding_row in employee_onboarding:

                        completed = sum([
                            int(bool(
                                onboarding_row.get("contract")
                            )),
                            int(bool(
                                onboarding_row.get("documents")
                            )),
                            int(bool(
                                onboarding_row.get("email")
                            )),
                            int(bool(
                                onboarding_row.get("equipment")
                            )),
                            int(bool(
                                onboarding_row.get("system_access")
                            )),
                            int(bool(
                                onboarding_row.get("training")
                            )),
                            int(bool(
                                onboarding_row.get("manager_meeting")
                            )),
                        ])

                        st.progress(
                            completed / 7
                        )

                        st.write(
                            f"Ολοκλήρωση: {completed}/7"
                        )

                else:

                    st.info(
                        "Δεν υπάρχει onboarding "
                        "για αυτόν τον εργαζόμενο."
                    )

            with employee_tabs[3]:

                st.info(
                    "Το audit log εργαζομένων "
                    "μπορεί να προστεθεί σε επόμενο στάδιο."
                )

# ============================================================
# RECRUITMENT
# ============================================================

elif page == "📋 Recruitment":

    st.title("📋 Recruitment")
    st.markdown(
        "Διαχείριση υποψηφίων και διαδικασίας προσλήψεων."
    )

    add_candidate_tab, manage_candidate_tab = st.tabs([
        "➕ Νέος υποψήφιος",
        "📋 Διαχείριση υποψηφίων",
    ])

    recruitment_statuses = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
        "Απορρίφθηκε",
    ]

    with add_candidate_tab:

        with st.form("candidate_form"):

            candidate_first_name = st.text_input(
                "Όνομα"
            )

            candidate_last_name = st.text_input(
                "Επώνυμο"
            )

            candidate_email = st.text_input(
                "Email"
            )

            candidate_phone = st.text_input(
                "Τηλέφωνο"
            )

            candidate_position = st.text_input(
                "Θέση εργασίας"
            )

            candidate_application_date = st.date_input(
                "Ημερομηνία αίτησης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            candidate_status = st.selectbox(
                "Κατάσταση",
                recruitment_statuses,
            )

            candidate_interview_date = st.text_input(
                "📅 Ημερομηνία / ώρα συνέντευξης",
                placeholder="π.χ. 10/09/2026 11:00",
            )

            candidate_rating = st.selectbox(
                "⭐ Αξιολόγηση",
                [None, 1, 2, 3, 4, 5],
                format_func=lambda x: (
                    "Χωρίς αξιολόγηση"
                    if x is None
                    else str(x)
                ),
            )

            candidate_recruiter = st.text_input(
                "👤 Recruiter"
            )

            candidate_notes = st.text_area(
                "📝 Σημειώσεις HR"
            )

            candidate_submit = st.form_submit_button(
                "💾 Αποθήκευση υποψηφίου"
            )

            if candidate_submit:

                if (
                    not candidate_first_name.strip()
                    or not candidate_last_name.strip()
                ):

                    st.error(
                        "Το Όνομα και το Επώνυμο "
                        "είναι υποχρεωτικά."
                    )

                else:

                    try:

                        add_candidate(
                            candidate_first_name.strip(),
                            candidate_last_name.strip(),
                            candidate_email.strip() or None,
                            candidate_phone.strip() or None,
                            candidate_position.strip() or None,
                            candidate_application_date.strftime(
                                "%Y-%m-%d"
                            ),
                            candidate_status,
                            candidate_interview_date.strip()
                            or None,
                            candidate_rating,
                            candidate_notes.strip() or None,
                            candidate_recruiter.strip() or None,
                        )

                        st.success(
                            "✅ Ο υποψήφιος προστέθηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Σφάλμα προσθήκης: {e}"
                        )

    with manage_candidate_tab:

        candidates = get_candidates()

        if not candidates:

            st.info(
                "Δεν υπάρχουν υποψήφιοι ακόμη."
            )

        else:

            st.subheader(
                "📊 Recruitment Pipeline"
            )

            recruitment_df = pd.DataFrame([
                {
                    "ID":
                        candidate_row.get("id"),
                    "Υποψήφιος":
                        (
                            f'{candidate_row.get("first_name", "")} '
                            f'{candidate_row.get("last_name", "")}'
                        ).strip(),
                    "Email":
                        candidate_row.get("email"),
                    "Θέση":
                        candidate_row.get("position"),
                    "Κατάσταση":
                        candidate_row.get("status"),
                    "Συνέντευξη":
                        candidate_row.get("interview_date"),
                    "Αξιολόγηση":
                        candidate_row.get("rating"),
                    "Recruiter":
                        candidate_row.get("recruiter"),
                }
                for candidate_row in candidates
            ])

            st.dataframe(
                recruitment_df,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("---")

            st.subheader(
                "👤 Διαχείριση υποψηφίου"
            )

            candidate_options = {
                (
                    f'{candidate_row["first_name"]} '
                    f'{candidate_row["last_name"]} '
                    f'– '
                    f'{candidate_row.get("position") or "Χωρίς θέση"} '
                    f'(ID: {candidate_row["id"]})'
                ): candidate_row
                for candidate_row in candidates
            }

            selected_candidate_label = st.selectbox(
                "Επίλεξε υποψήφιο",
                list(candidate_options.keys()),
                key="recruitment_candidate_selector",
            )

            # THIS IS THE ONLY SELECTED CANDIDATE VARIABLE USED BELOW
            selected_candidate = candidate_options[
                selected_candidate_label
            ]

            current_candidate_status = (
                selected_candidate.get("status")
                or "Νέα αίτηση"
            )

            if current_candidate_status in recruitment_statuses:
                candidate_status_index = recruitment_statuses.index(
                    current_candidate_status
                )
            else:
                candidate_status_index = 0

            with st.form(
                f"candidate_manage_{selected_candidate['id']}"
            ):

                new_candidate_status = st.selectbox(
                    "Κατάσταση",
                    recruitment_statuses,
                    index=candidate_status_index,
                )

                interview_date_edit = st.text_input(
                    "📅 Ημερομηνία / ώρα συνέντευξης",
                    value=safe_text(
                        selected_candidate.get(
                            "interview_date"
                        )
                    ),
                    placeholder="π.χ. 10/09/2026 11:00",
                )

                rating_values = [
                    None,
                    1,
                    2,
                    3,
                    4,
                    5,
                ]

                current_rating = selected_candidate.get(
                    "rating"
                )

                if current_rating in rating_values:
                    rating_index = rating_values.index(
                        current_rating
                    )
                else:
                    rating_index = 0

                rating_edit = st.selectbox(
                    "⭐ Αξιολόγηση",
                    rating_values,
                    index=rating_index,
                    format_func=lambda x: (
                        "Χωρίς αξιολόγηση"
                        if x is None
                        else str(x)
                    ),
                )

                recruiter_edit = st.text_input(
                    "👤 Recruiter",
                    value=safe_text(
                        selected_candidate.get(
                            "recruiter"
                        )
                    ),
                )

                notes_edit = st.text_area(
                    "📝 Σημειώσεις HR",
                    value=safe_text(
                        selected_candidate.get(
                            "notes"
                        )
                    ),
                )

                save_candidate = st.form_submit_button(
                    "💾 Αποθήκευση αλλαγών"
                )

                if save_candidate:

                    try:

                        update_candidate(
                            selected_candidate["id"],
                            new_candidate_status,
                            user_email,
                            interview_date_edit.strip()
                            or None,
                            rating_edit,
                            notes_edit.strip()
                            or None,
                            recruiter_edit.strip()
                            or None,
                        )

                        st.success(
                            "✅ Ο υποψήφιος ενημερώθηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Σφάλμα ενημέρωσης: {e}"
                        )

            # ====================================================
            # HIRE -> EMPLOYEE -> ONBOARDING
            # ====================================================

            if (
                selected_candidate.get("status")
                == "Προσλήφθηκε"
            ):

                st.markdown("---")

                st.subheader(
                    "👥 Μεταφορά στους εργαζομένους"
                )

                st.info(
                    "Ο υποψήφιος έχει προσληφθεί. "
                    "Με το κουμπί θα δημιουργηθεί "
                    "Employee Profile και Onboarding."
                )

                if st.button(
                    "👥 Δημιουργία εργαζομένου + Onboarding",
                    key=(
                        f"create_employee_onboarding_"
                        f"{selected_candidate['id']}"
                    ),
                    type="primary",
                ):

                    try:

                        employee_id = (
                            create_employee_from_candidate(
                                selected_candidate["id"]
                            )
                        )

                        existing_onboarding = [
                            onboarding_row
                            for onboarding_row in get_onboarding()
                            if onboarding_row.get("employee_id")
                            == employee_id
                        ]

                        if existing_onboarding:

                            st.warning(
                                "Ο εργαζόμενος υπάρχει ήδη "
                                "και έχει ήδη Onboarding."
                            )

                        else:

                            create_onboarding(
                                employee_id,
                                date.today().strftime(
                                    "%Y-%m-%d"
                                ),
                            )

                            st.success(
                                "✅ Ο εργαζόμενος δημιουργήθηκε "
                                "και ξεκίνησε αυτόματα το Onboarding."
                            )

                    except Exception as e:

                        st.error(
                            f"❌ Σφάλμα: {e}"
                        )

            st.markdown("---")

            st.subheader(
                "📋 Ιστορικό υποψηφίου"
            )

            try:

                candidate_history = get_candidate_history(
                    selected_candidate["id"]
                )

            except Exception as e:

                candidate_history = []

                st.error(
                    f"Σφάλμα φόρτωσης ιστορικού: {e}"
                )

            if candidate_history:

                st.dataframe(
                    pd.DataFrame([
                        {
                            "Από":
                                history_row.get(
                                    "old_status"
                                )
                                or "-",
                            "Σε":
                                history_row.get(
                                    "new_status"
                                ),
                            "Άλλαξε από":
                                history_row.get(
                                    "changed_by"
                                )
                                or "-",
                            "Ημερομηνία":
                                safe_text(
                                    history_row.get(
                                        "changed_at"
                                    )
                                ),
                        }
                        for history_row in candidate_history
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "Δεν υπάρχει ιστορικό αλλαγών."
                )

# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    st.title("🚀 Onboarding")
    st.markdown(
        "Checklist για την ένταξη νέων εργαζομένων."
    )

    employees = get_employees()

    if not employees:

        st.warning(
            "Πρέπει πρώτα να υπάρχει εργαζόμενος."
        )

    else:

        st.subheader(
            "➕ Νέο Onboarding"
        )

        employee_options = {
            (
                f'{employee["first_name"]} '
                f'{employee["last_name"]} '
                f'(ID: {employee["id"]})'
            ): employee["id"]
            for employee in employees
        }

        with st.form("onboarding_form"):

            selected_employee_label = st.selectbox(
                "Εργαζόμενος",
                list(employee_options.keys()),
            )

            onboarding_start_date = st.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            onboarding_submit = st.form_submit_button(
                "🚀 Δημιουργία Onboarding"
            )

            if onboarding_submit:

                employee_id = employee_options[
                    selected_employee_label
                ]

                existing_onboarding = [
                    onboarding_row
                    for onboarding_row in get_onboarding()
                    if onboarding_row.get("employee_id")
                    == employee_id
                ]

                if existing_onboarding:

                    st.warning(
                        "Υπάρχει ήδη onboarding "
                        "για αυτόν τον εργαζόμενο."
                    )

                else:

                    try:

                        create_onboarding(
                            employee_id,
                            onboarding_start_date.strftime(
                                "%Y-%m-%d"
                            ),
                        )

                        st.success(
                            "✅ Το onboarding δημιουργήθηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Σφάλμα: {e}"
                        )

        st.markdown("---")

        st.subheader(
            "📋 Onboarding Checklist"
        )

        onboarding_items = get_onboarding()

        if not onboarding_items:

            st.info(
                "Δεν υπάρχουν onboarding διαδικασίες."
            )

        else:

            for onboarding_row in onboarding_items:

                employee_name = (
                    f'{onboarding_row.get("first_name", "")} '
                    f'{onboarding_row.get("last_name", "")}'
                ).strip()

                with st.expander(
                    (
                        f"👤 {employee_name} — "
                        f"{format_date(onboarding_row.get('start_date'))}"
                    )
                ):

                    contract = st.checkbox(
                        "📄 Σύμβαση",
                        value=bool(
                            onboarding_row.get("contract")
                        ),
                        key=(
                            f"contract_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    documents = st.checkbox(
                        "📁 Έγγραφα",
                        value=bool(
                            onboarding_row.get("documents")
                        ),
                        key=(
                            f"documents_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    company_email = st.checkbox(
                        "📧 Email",
                        value=bool(
                            onboarding_row.get("email")
                        ),
                        key=(
                            f"email_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    equipment = st.checkbox(
                        "💻 Εξοπλισμός",
                        value=bool(
                            onboarding_row.get("equipment")
                        ),
                        key=(
                            f"equipment_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    system_access = st.checkbox(
                        "🔐 Πρόσβαση σε συστήματα",
                        value=bool(
                            onboarding_row.get(
                                "system_access"
                            )
                        ),
                        key=(
                            f"system_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    training = st.checkbox(
                        "🎓 Εκπαίδευση",
                        value=bool(
                            onboarding_row.get("training")
                        ),
                        key=(
                            f"training_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    manager_meeting = st.checkbox(
                        "🤝 Συνάντηση με Manager",
                        value=bool(
                            onboarding_row.get(
                                "manager_meeting"
                            )
                        ),
                        key=(
                            f"manager_"
                            f"{onboarding_row['id']}"
                        ),
                    )

                    if st.button(
                        "💾 Αποθήκευση Checklist",
                        key=(
                            f"save_onboarding_"
                            f"{onboarding_row['id']}"
                        ),
                    ):

                        try:

                            update_onboarding(
                                onboarding_row["id"],
                                int(contract),
                                int(documents),
                                int(company_email),
                                int(equipment),
                                int(system_access),
                                int(training),
                                int(manager_meeting),
                            )

                            st.success(
                                "✅ Το checklist ενημερώθηκε."
                            )

                            st.rerun()

                        except Exception as e:

                            st.error(
                                f"Σφάλμα: {e}"
                            )

# ============================================================
# LEAVES HR / ADMIN
# ============================================================

elif page == "🏖️ Άδειες":

    st.title("🏖️ Άδειες")

    leaves = get_leaves()

    if not leaves:

        st.info(
            "Δεν υπάρχουν αιτήσεις άδειας."
        )

    else:

        pending_leaves = [
            leave
            for leave in leaves
            if leave.get("status") == "Εκκρεμεί"
        ]

        col1, col2 = st.columns(2)

        col1.metric(
            "Σύνολο αιτήσεων",
            len(leaves),
        )

        col2.metric(
            "Εκκρεμείς",
            len(pending_leaves),
        )

        st.dataframe(
            pd.DataFrame([
                {
                    "ID":
                        leave.get("id"),
                    "Εργαζόμενος":
                        (
                            f'{leave.get("first_name", "")} '
                            f'{leave.get("last_name", "")}'
                        ).strip(),
                    "Τύπος":
                        leave.get("leave_type"),
                    "Από":
                        format_date(
                            leave.get("start_date")
                        ),
                    "Έως":
                        format_date(
                            leave.get("end_date")
                        ),
                    "Αιτιολογία":
                        leave.get("reason"),
                    "Κατάσταση":
                        leave.get("status"),
                }
                for leave in leaves
            ]),
            use_container_width=True,
            hide_index=True,
        )

        if pending_leaves:

            st.markdown("---")

            st.subheader(
                "✅ Έγκριση / Απόρριψη"
            )

            leave_options = {
                (
                    f'#{leave["id"]} - '
                    f'{leave.get("first_name", "")} '
                    f'{leave.get("last_name", "")} '
                    f'({format_date(leave.get("start_date"))})'
                ): leave["id"]
                for leave in pending_leaves
            }

            selected_leave_label = st.selectbox(
                "Αίτηση",
                list(leave_options.keys()),
            )

            leave_decision = st.radio(
                "Απόφαση",
                [
                    "Εγκρίθηκε",
                    "Απορρίφθηκε",
                ],
                horizontal=True,
            )

            if st.button(
                "💾 Αποθήκευση απόφασης"
            ):

                try:

                    update_leave_status(
                        leave_options[
                            selected_leave_label
                        ],
                        leave_decision,
                    )

                    st.success(
                        "✅ Η κατάσταση ενημερώθηκε."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Σφάλμα: {e}"
                    )

# ============================================================
# EMPLOYEE PROFILE
# ============================================================

elif page == "👤 Το προφίλ μου":

    st.title(
        "👤 Το προφίλ μου"
    )

    employee = get_employee_by_email(
        user_email
    )

    if not employee:

        st.warning(
            "Δεν βρέθηκε Employee Profile "
            f"συνδεδεμένο με το email {user_email}."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Όνομα:** "
                f"{employee.get('first_name', '')}"
            )

            st.write(
                f"**Επώνυμο:** "
                f"{employee.get('last_name', '')}"
            )

            st.write(
                f"**Email:** "
                f"{employee.get('email', '')}"
            )

            st.write(
                f"**Τηλέφωνο:** "
                f"{employee.get('phone', '')}"
            )

        with col2:

            st.write(
                f"**Θέση:** "
                f"{employee.get('position', '')}"
            )

            st.write(
                f"**Τμήμα:** "
                f"{employee.get('department', '')}"
            )

            st.write(
                "**Ημερομηνία πρόσληψης:** "
                f"{format_date(employee.get('hire_date'))}"
            )

            st.write(
                f"**Κατάσταση:** "
                f"{employee.get('status', '')}"
            )

# ============================================================
# EMPLOYEE LEAVES
# ============================================================

elif page == "🏖️ Οι άδειές μου":

    st.title(
        "🏖️ Οι άδειές μου"
    )

    employee = get_employee_by_email(
        user_email
    )

    if not employee:

        st.warning(
            "Δεν βρέθηκε Employee Profile "
            "συνδεδεμένο με το email σου."
        )

    else:

        with st.form(
            "employee_leave_form"
        ):

            leave_type = st.selectbox(
                "Τύπος άδειας",
                [
                    "Κανονική",
                    "Αναρρωτική",
                    "Άδεια άνευ αποδοχών",
                    "Ειδική",
                    "Άλλο",
                ],
            )

            leave_start_date = st.date_input(
                "Από",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            leave_end_date = st.date_input(
                "Έως",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            leave_reason = st.text_area(
                "Αιτιολογία"
            )

            leave_submit = st.form_submit_button(
                "📨 Υποβολή αίτησης"
            )

            if leave_submit:

                if leave_end_date < leave_start_date:

                    st.error(
                        "Η ημερομηνία λήξης δεν μπορεί "
                        "να είναι πριν από "
                        "την ημερομηνία έναρξης."
                    )

                else:

                    try:

                        add_leave(
                            employee["id"],
                            leave_type,
                            leave_start_date.strftime(
                                "%Y-%m-%d"
                            ),
                            leave_end_date.strftime(
                                "%Y-%m-%d"
                            ),
                            leave_reason.strip()
                            or None,
                        )

                        st.success(
                            "✅ Η αίτηση υποβλήθηκε."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Σφάλμα: {e}"
                        )

        my_leaves = [
            leave
            for leave in get_leaves()
            if leave.get("employee_id")
            == employee["id"]
        ]

        if my_leaves:

            st.dataframe(
                pd.DataFrame([
                    {
                        "Τύπος":
                            leave.get("leave_type"),
                        "Από":
                            format_date(
                                leave.get("start_date")
                            ),
                        "Έως":
                            format_date(
                                leave.get("end_date")
                            ),
                        "Αιτιολογία":
                            leave.get("reason"),
                        "Κατάσταση":
                            leave.get("status"),
                    }
                    for leave in my_leaves
                ]),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "Δεν έχεις αιτήσεις άδειας."
            )

# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title(
        "🤖 AI Assistant"
    )

    st.markdown(
        "Βοηθός για καθημερινές εργασίες HR."
    )

    question = st.text_area(
        "Γράψε την ερώτησή σου:",
        placeholder=(
            "π.χ. Δημιούργησε μια αγγελία "
            "για HR Assistant"
        ),
    )

    if st.button(
        "🤖 Ρώτησε τον AI Assistant"
    ):

        if not question.strip():

            st.warning(
                "Γράψε πρώτα μια ερώτηση."
            )

        else:

            api_key = None

            try:
                api_key = st.secrets.get(
                    "OPENAI_API_KEY"
                )
            except Exception:
                pass

            if not api_key:
                api_key = os.getenv(
                    "OPENAI_API_KEY"
                )

            if not api_key:

                st.info(
                    "Ο AI Assistant δεν έχει ενεργό API key. "
                    "Τα υπόλοιπα modules λειτουργούν κανονικά."
                )

            else:

                try:

                    from openai import OpenAI

                    client = OpenAI(
                        api_key=api_key
                    )

                    response = client.responses.create(
                        model="gpt-5-mini",
                        input=[
                            {
                                "role": "system",
                                "content": (
                                    "Είσαι επαγγελματικός "
                                    "HR Assistant. "
                                    "Απάντησε στα ελληνικά, "
                                    "σύντομα και καθαρά."
                                ),
                            },
                            {
                                "role": "user",
                                "content": question,
                            },
                        ],
                    )

                    st.success(
                        response.output_text
                    )

                except Exception as e:

                    st.error(
                        "Ο AI Assistant "
                        "δεν μπόρεσε να απαντήσει. "
                        f"Λεπτομέρειες: {e}"
                    )
