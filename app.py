
import os
from datetime import date

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
    create_recruitment_table,
    add_candidate,
    get_candidates,
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
# GOOGLE LOGIN
# ============================================================

if not st.user.is_logged_in:
    st.title("🔐 AI HR System")
    st.subheader("Σύνδεση στο HR System")

    st.button(
        "Σύνδεση με Google",
        on_click=st.login,
    )

    st.stop()


# ============================================================
# USER / ROLE
# ============================================================

user_email = st.user.email

admin_emails = st.secrets["roles"]["admin_emails"]
hr_emails = st.secrets["roles"]["hr_emails"]

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
# SIDEBAR USER INFO
# ============================================================

st.sidebar.success(
    f"👤 {st.user.name or user_email}"
)

st.sidebar.info(
    f"Ρόλος: {user_role}"
)

if st.sidebar.button("🚪 Αποσύνδεση"):
    st.logout()


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

if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None


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
# SIDEBAR MENU
# ============================================================

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

page = st.sidebar.radio(
    "Μενού",
    menu_options,
)

st.sidebar.markdown("---")
st.sidebar.caption("AI HR Management System")


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("📊 HR Dashboard")
    st.caption(
        "Κεντρική εικόνα του τμήματος Ανθρώπινου Δυναμικού."
    )

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    employees = get_employees()
    candidates = get_candidates()
    leaves = get_leaves()
    stats = get_hr_statistics()

    # --------------------------------------------------------
    # DEPARTMENT FILTER
    # --------------------------------------------------------

    department_values = sorted(
        {
            employee.get("department")
            for employee in employees
            if employee.get("department")
        }
    )

    department_filter = st.selectbox(
        "🏢 Φίλτρο τμήματος",
        ["Όλα"] + department_values,
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

    filtered_inactive = filtered_total - filtered_active

    active_rate = (
        (filtered_active / filtered_total) * 100
        if filtered_total > 0
        else 0
    )

    # --------------------------------------------------------
    # MAIN KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 Σύνολο εργαζομένων",
            filtered_total,
        )

    with col2:
        st.metric(
            "✅ Ενεργοί εργαζόμενοι",
            filtered_active,
        )

    with col3:
        st.metric(
            "📋 Υποψήφιοι",
            stats["total_candidates"],
        )

    with col4:
        st.metric(
            "🏖️ Εκκρεμή αιτήματα",
            stats["pending_leaves"],
        )

    st.divider()

    # --------------------------------------------------------
    # SECOND KPI ROW
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "❌ Ανενεργοί",
            filtered_inactive,
        )

    with col2:
        st.metric(
            "🎯 Προσλήψεις",
            stats["hired_candidates"],
        )

    with col3:
        st.metric(
            "🏖️ Σύνολο αιτήσεων άδειας",
            stats["total_leaves"],
        )

    with col4:
        st.metric(
            "📈 Active Rate",
            f"{active_rate:.1f}%",
        )

    st.divider()

    # --------------------------------------------------------
    # EMPLOYEES BY DEPARTMENT
    # --------------------------------------------------------

    st.subheader("👥 Εργαζόμενοι ανά τμήμα")

    if employees:

        department_df = pd.DataFrame(employees)

        if "department" in department_df.columns:

            department_counts = (
                department_df["department"]
                .fillna("Χωρίς τμήμα")
                .value_counts()
            )

            st.bar_chart(department_counts)

    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")

    st.divider()

    # --------------------------------------------------------
    # EMPLOYEE STATUS
    # --------------------------------------------------------

    st.subheader("📊 Κατάσταση εργαζομένων")

    if filtered_employees:

        status_df = pd.DataFrame(filtered_employees)

        if "status" in status_df.columns:

            status_counts = (
                status_df["status"]
                .fillna("Άγνωστη κατάσταση")
                .value_counts()
            )

            st.bar_chart(status_counts)

    else:
        st.info(
            "Δεν υπάρχουν εργαζόμενοι για το συγκεκριμένο τμήμα."
        )

    st.divider()

    # --------------------------------------------------------
    # RECRUITMENT
    # --------------------------------------------------------

    st.subheader("📋 Recruitment")

    if candidates:

        candidate_df = pd.DataFrame(candidates)

        if "status" in candidate_df.columns:

            recruitment_counts = (
                candidate_df["status"]
                .fillna("Άγνωστη κατάσταση")
                .value_counts()
            )

            st.bar_chart(recruitment_counts)

    else:
        st.info("Δεν υπάρχουν υποψήφιοι.")

    # --------------------------------------------------------
    # RECRUITMENT FUNNEL
    # --------------------------------------------------------

    st.subheader("🎯 Recruitment Funnel")

    if candidates:

        candidate_df = pd.DataFrame(candidates)

        if "status" in candidate_df.columns:

            funnel = (
                candidate_df["status"]
                .fillna("Άγνωστη κατάσταση")
                .value_counts()
            )

            st.bar_chart(funnel)

            hired = int(
                (
                    candidate_df["status"]
                    == "Προσλήφθηκε"
                ).sum()
            )

            total_candidates = len(candidate_df)

            hiring_rate = (
                (hired / total_candidates) * 100
                if total_candidates > 0
                else 0
            )

            st.metric(
                "📈 Ποσοστό πρόσληψης",
                f"{hiring_rate:.1f}%",
            )

    else:
        st.info("Δεν υπάρχουν δεδομένα recruitment.")

    st.divider()

    # --------------------------------------------------------
    # LEAVE ANALYTICS
    # --------------------------------------------------------

    st.subheader("🏖️ Leave Analytics")

    if leaves:

        leave_df = pd.DataFrame(leaves)

        if "status" in leave_df.columns:

            approved = int(
                (
                    leave_df["status"]
                    == "Εγκρίθηκε"
                ).sum()
            )

            rejected = int(
                (
                    leave_df["status"]
                    == "Απορρίφθηκε"
                ).sum()
            )

            pending = int(
                (
                    leave_df["status"]
                    == "Εκκρεμεί"
                ).sum()
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "✅ Εγκεκριμένες",
                    approved,
                )

            with col2:
                st.metric(
                    "❌ Απορριφθείσες",
                    rejected,
                )

            with col3:
                st.metric(
                    "⏳ Εκκρεμείς",
                    pending,
                )

    else:
        st.info(
            "Δεν υπάρχουν αιτήματα άδειας."
        )

    st.divider()

    # --------------------------------------------------------
    # RECENT EMPLOYEES
    # --------------------------------------------------------

    st.subheader("👤 Πρόσφατοι εργαζόμενοι")

    if filtered_employees:

        recent_df = pd.DataFrame(
            filtered_employees
        )

        columns_to_show = [
            column
            for column in [
                "first_name",
                "last_name",
                "email",
                "position",
                "department",
                "status",
            ]
            if column in recent_df.columns
        ]

        st.dataframe(
            recent_df[columns_to_show].head(10),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "Δεν υπάρχουν εργαζόμενοι."
        )


# ============================================================
# EMPLOYEE PROFILE
# ============================================================

elif page == "👤 Το προφίλ μου":

    st.title("👤 Το προφίλ μου")

    employee = get_employee_by_email(
        user_email
    )

    if employee is None:

        st.warning(
            "Δεν βρέθηκε εργαζόμενος με αυτό το "
            "Google email. Παρακαλώ επικοινώνησε με το HR."
        )

    else:

        st.subheader(
            f"{employee['first_name']} "
            f"{employee['last_name']}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                "**Όνομα:**",
                employee["first_name"],
            )

            st.write(
                "**Επώνυμο:**",
                employee["last_name"],
            )

            st.write(
                "**Email:**",
                employee["email"],
            )

            st.write(
                "**Τηλέφωνο:**",
                employee["phone"] or "-",
            )

        with col2:

            st.write(
                "**Θέση:**",
                employee["position"] or "-",
            )

            st.write(
                "**Τμήμα:**",
                employee["department"] or "-",
            )

            st.write(
                "**Ημερομηνία πρόσληψης:**",
                employee["hire_date"] or "-",
            )

            st.write(
                "**Κατάσταση:**",
                employee["status"] or "-",
            )


# ============================================================
# EMPLOYEE LEAVES
# ============================================================

elif page == "🏖️ Οι άδειές μου":

    st.title("🏖️ Οι άδειές μου")

    employee = get_employee_by_email(
        user_email
    )

    if employee is None:

        st.warning(
            "Δεν βρέθηκε εργαζόμενος με αυτό "
            "το Google email. Επικοινώνησε με το HR."
        )

    else:

        leaves = get_leaves()

        my_leaves = [
            leave
            for leave in leaves
            if leave["employee_id"] == employee["id"]
        ]

        st.subheader("📋 Ιστορικό αδειών")

        if not my_leaves:

            st.info(
                "Δεν υπάρχουν καταχωρημένες άδειες."
            )

        else:

            for leave in my_leaves:

                st.divider()

                st.write(
                    f"**Τύπος άδειας:** "
                    f"{leave['leave_type']}"
                )

                st.write(
                    f"**Από:** {leave['start_date']} "
                    f"**Έως:** {leave['end_date']}"
                )

                st.write(
                    f"**Αιτιολογία:** "
                    f"{leave['reason'] or '-'}"
                )

                st.write(
                    f"**Κατάσταση:** "
                    f"{leave['status']}"
                )

        st.divider()

        # ----------------------------------------------------
        # NEW LEAVE REQUEST
        # ----------------------------------------------------

        st.subheader(
            "➕ Νέο αίτημα άδειας"
        )

        with st.form(
            "leave_request_form"
        ):

            leave_type = st.selectbox(
                "Τύπος άδειας",
                [
                    "Κανονική",
                    "Αναρρωτική",
                    "Άδεια άνευ αποδοχών",
                    "Ειδική",
                ],
            )

            col1, col2 = st.columns(2)

            with col1:

                start_date = st.date_input(
                    "Ημερομηνία έναρξης",
                    value=date.today(),
                    format="DD/MM/YYYY",
                )

            with col2:

                end_date = st.date_input(
                    "Ημερομηνία λήξης",
                    value=date.today(),
                    format="DD/MM/YYYY",
                )

            reason = st.text_area(
                "Αιτιολογία"
            )

            submitted = st.form_submit_button(
                "📤 Υποβολή αιτήματος"
            )

            if submitted:

                if end_date < start_date:

                    st.error(
                        "Η ημερομηνία λήξης δεν μπορεί "
                        "να είναι πριν από την ημερομηνία έναρξης."
                    )

                else:

                    add_leave(
                        employee["id"],
                        leave_type,
                        start_date.strftime(
                            "%Y-%m-%d"
                        ),
                        end_date.strftime(
                            "%Y-%m-%d"
                        ),
                        reason,
                        "Εκκρεμεί",
                    )

                    st.success(
                        "✅ Το αίτημα άδειας "
                        "υποβλήθηκε επιτυχώς."
                    )

                    st.rerun()


# ============================================================
# EMPLOYEES
# ============================================================

elif page == "👥 Εργαζόμενοι":

    if not IS_HR:
        st.error(
            "⛔ Δεν έχεις δικαίωμα πρόσβασης."
        )
        st.stop()

    st.title(
        "👥 Διαχείριση Εργαζομένων"
    )

    # --------------------------------------------------------
    # ADD EMPLOYEE
    # --------------------------------------------------------

    st.subheader(
        "➕ Προσθήκη εργαζομένου"
    )

    with st.form(
        "employee_form"
    ):

        first_name = st.text_input(
            "Όνομα"
        )

        last_name = st.text_input(
            "Επώνυμο"
        )

        email = st.text_input(
            "Email"
        )

        phone = st.text_input(
            "Τηλέφωνο"
        )

        position = st.text_input(
            "Θέση"
        )

        department = st.text_input(
            "Τμήμα"
        )

        hire_date = st.date_input(
            "Ημερομηνία πρόσληψης",
            value=date.today(),
            format="DD/MM/YYYY",
        )

        status = st.selectbox(
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

            if not first_name or not last_name:

                st.error(
                    "Το Όνομα και το Επώνυμο "
                    "είναι υποχρεωτικά."
                )

            else:

                try:

                    add_employee(
                        first_name,
                        last_name,
                        email,
                        phone,
                        position,
                        department,
                        hire_date.strftime(
                            "%Y-%m-%d"
                        ),
                        status,
                    )

                    st.success(
                        "✅ Ο εργαζόμενος "
                        "προστέθηκε επιτυχώς."
                    )

                    st.rerun()

                except Exception as e:

                    if (
                        "UniqueViolation" in str(e)
                        or "duplicate key" in str(e).lower()
                    ):

                        st.error(
                            "❌ Υπάρχει ήδη εργαζόμενος "
                            "με αυτό το email."
                        )

                    else:

                        st.error(
                            "❌ Σφάλμα κατά την "
                            f"αποθήκευση: {e}"
                        )

    st.divider()

    # --------------------------------------------------------
    # EMPLOYEE LIST
    # --------------------------------------------------------

    st.subheader("📋 Λίστα εργαζομένων")

employees = get_employees()

if page == "👥 Employees" and employees:

    search_text = st.text_input(
        "🔎 Αναζήτηση εργαζομένου",
        placeholder="Όνομα, επώνυμο ή email..."
    )

    department_filter = st.selectbox(
        "🏢 Φίλτρο τμήματος",
        ["Όλα"] + sorted(
            {
                employee["department"]
                for employee in employees
                if employee.get("department")
            }
        )
    )

    status_filter = st.selectbox(
        "📌 Φίλτρο κατάστασης",
        [
            "Όλες",
            "Ενεργός",
            "Ανενεργός",
            "Σε άδεια"
        ]
    )

    filtered_employees = employees

    if search_text:
        search_lower = search_text.lower()

        filtered_employees = [
            employee
            for employee in filtered_employees
            if search_lower in (
                employee.get("first_name") or ""
            ).lower()
            or search_lower in (
                employee.get("last_name") or ""
            ).lower()
            or search_lower in (
                employee.get("email") or ""
            ).lower()
        ]

    if department_filter != "Όλα":
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.get("department") == department_filter
        ]

    if status_filter != "Όλες":
        filtered_employees = [
            employee
            for employee in filtered_employees
            if employee.get("status") == status_filter
        ]

    st.caption(
        f"Βρέθηκαν {len(filtered_employees)} εργαζόμενοι."
    )

    employee_data = []

    for employee in filtered_employees:

        employee_data.append(
            {
                "ID": employee["id"],
                "Όνομα": employee["first_name"],
                "Επώνυμο": employee["last_name"],
                "Email": employee["email"],
                "Τηλέφωνο": employee["phone"],
                "Θέση": employee["position"],
                "Τμήμα": employee["department"],
                "Ημερομηνία πρόσληψης":
                    employee["hire_date"],
                "Κατάσταση": employee["status"],
            }
        )

    df = pd.DataFrame(employee_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

elif page == "👥 Employees":

    st.info("Δεν υπάρχουν εργαζόμενοι.")

    if employees:

        employee_data = []

        for employee in employees:

            employee_data.append(
                {
                    "ID": employee["id"],
                    "Όνομα": employee["first_name"],
                    "Επώνυμο": employee["last_name"],
                    "Email": employee["email"],
                    "Τηλέφωνο": employee["phone"],
                    "Θέση": employee["position"],
                    "Τμήμα": employee["department"],
                    "Ημερομηνία πρόσληψης":
                        employee["hire_date"],
                    "Κατάσταση": employee["status"],
                }
            )

        df = pd.DataFrame(
            employee_data
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ----------------------------------------------------
        # DELETE EMPLOYEE
        # ----------------------------------------------------

        st.subheader(
            "🗑️ Διαγραφή εργαζομένου"
        )

        employee_options = {
            f'{employee["first_name"]} '
            f'{employee["last_name"]} '
            f'(ID: {employee["id"]})':
            employee["id"]
            for employee in employees
        }

        selected_employee = st.selectbox(
            "Επίλεξε εργαζόμενο",
            list(employee_options.keys()),
        )

        if st.button(
            "🗑️ Διαγραφή",
            type="secondary",
        ):

            employee_id = employee_options[
                selected_employee
            ]

            delete_employee(
                employee_id
            )

            st.success(
                "✅ Ο εργαζόμενος διαγράφηκε."
            )

            st.rerun()

    else:

        st.info(
            "Δεν υπάρχουν εργαζόμενοι."
        )


# ============================================================
# RECRUITMENT
# ============================================================

elif page == "📋 Recruitment":

    if not IS_HR:
        st.error(
            "⛔ Δεν έχεις δικαίωμα πρόσβασης."
        )
        st.stop()

    st.title(
        "📋 Recruitment"
    )

    st.markdown(
        "Διαχείριση υποψηφίων και διαδικασίας προσλήψεων."
    )

    # --------------------------------------------------------
    # ADD CANDIDATE
    # --------------------------------------------------------

    st.subheader(
        "➕ Προσθήκη υποψηφίου"
    )

    with st.form(
        "candidate_form"
    ):

        first_name = st.text_input(
            "Όνομα"
        )

        last_name = st.text_input(
            "Επώνυμο"
        )

        email = st.text_input(
            "Email"
        )

        phone = st.text_input(
            "Τηλέφωνο"
        )

        position = st.text_input(
            "Θέση εργασίας"
        )

        application_date = st.date_input(
            "Ημερομηνία αίτησης",
            value=date.today(),
            format="DD/MM/YYYY",
        )

        status = st.selectbox(
            "Κατάσταση",
            [
                "Νέα αίτηση",
                "Σε αξιολόγηση",
                "Συνέντευξη",
                "Προσλήφθηκε",
                "Απορρίφθηκε",
            ],
        )

        submitted = st.form_submit_button(
            "💾 Αποθήκευση υποψηφίου"
        )

        if submitted:

            if not first_name or not last_name:

                st.error(
                    "Το Όνομα και το Επώνυμο "
                    "είναι υποχρεωτικά."
                )

            else:

                add_candidate(
                    first_name,
                    last_name,
                    email,
                    phone,
                    position,
                    application_date.strftime(
                        "%Y-%m-%d"
                    ),
                    status,
                )

                st.success(
                    "✅ Ο υποψήφιος προστέθηκε."
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CANDIDATES
    # --------------------------------------------------------

    st.subheader(
        "👤 Υποψήφιοι"
    )

    candidates = get_candidates()

    if candidates:

        candidate_data = []

        for candidate in candidates:

            candidate_data.append(
                {
                    "ID": candidate["id"],
                    "Όνομα": candidate["first_name"],
                    "Επώνυμο": candidate["last_name"],
                    "Email": candidate["email"],
                    "Τηλέφωνο": candidate["phone"],
                    "Θέση": candidate["position"],
                    "Ημερομηνία αίτησης":
                        candidate["application_date"],
                    "Κατάσταση":
                        candidate["status"],
                }
            )

        df_candidates = pd.DataFrame(
            candidate_data
        )

        st.dataframe(
            df_candidates,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι ακόμη."
        )


# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    if not IS_HR:
        st.error(
            "⛔ Δεν έχεις δικαίωμα πρόσβασης."
        )
        st.stop()

    st.title(
        "🚀 Employee Onboarding"
    )

    st.markdown(
        "Checklist για την ένταξη νέων εργαζομένων."
    )

    employees = get_employees()

    if not employees:

        st.warning(
            "Πρέπει πρώτα να προσθέσεις εργαζόμενο."
        )

    else:

        # ----------------------------------------------------
        # CREATE ONBOARDING
        # ----------------------------------------------------

        st.subheader(
            "➕ Νέο Onboarding"
        )

        employee_options = {
            f'{employee["first_name"]} '
            f'{employee["last_name"]}':
            employee["id"]
            for employee in employees
        }

        with st.form(
            "onboarding_form"
        ):

            selected_employee = st.selectbox(
                "Εργαζόμενος",
                list(employee_options.keys()),
            )

            start_date = st.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            submitted = st.form_submit_button(
                "🚀 Δημιουργία Onboarding"
            )

            if submitted:

                employee_id = employee_options[
                    selected_employee
                ]

                create_onboarding(
                    employee_id,
                    start_date.strftime(
                        "%Y-%m-%d"
                    ),
                )

                st.success(
                    "✅ Το onboarding δημιουργήθηκε!"
                )

                st.rerun()

        st.divider()

        # ----------------------------------------------------
        # ONBOARDING LIST
        # ----------------------------------------------------

        st.subheader(
            "📋 Onboarding Checklist"
        )

        onboarding = get_onboarding()

        if onboarding:

            for item in onboarding:

                employee_name = (
                    f'{item["first_name"]} '
                    f'{item["last_name"]}'
                )

                with st.expander(
                    f"👤 {employee_name}"
                ):

                    st.write(
                        f"**Ημερομηνία έναρξης:** "
                        f"{item['start_date']}"
                    )

                    contract = st.checkbox(
                        "📄 Σύμβαση",
                        value=bool(
                            item["contract"]
                        ),
                        key=f"contract_{item['id']}",
                    )

                    documents = st.checkbox(
                        "📁 Έγγραφα",
                        value=bool(
                            item["documents"]
                        ),
                        key=f"documents_{item['id']}",
                    )

                    email_setup = st.checkbox(
                        "📧 Email",
                        value=bool(
                            item["email"]
                        ),
                        key=f"email_{item['id']}",
                    )

                    equipment = st.checkbox(
                        "💻 Εξοπλισμός",
                        value=bool(
                            item["equipment"]
                        ),
                        key=f"equipment_{item['id']}",
                    )

                    system_access = st.checkbox(
                        "🔐 Πρόσβαση σε συστήματα",
                        value=bool(
                            item["system_access"]
                        ),
                        key=f"system_{item['id']}",
                    )

                    training = st.checkbox(
                        "🎓 Εκπαίδευση",
                        value=bool(
                            item["training"]
                        ),
                        key=f"training_{item['id']}",
                    )

                    manager_meeting = st.checkbox(
                        "🤝 Συνάντηση με Manager",
                        value=bool(
                            item["manager_meeting"]
                        ),
                        key=f"manager_{item['id']}",
                    )

                    if st.button(
                        "💾 Αποθήκευση Checklist",
                        key=f"save_onboarding_{item['id']}",
                    ):

                        update_onboarding(
                            item["id"],
                            int(contract),
                            int(documents),
                            int(email_setup),
                            int(equipment),
                            int(system_access),
                            int(training),
                            int(manager_meeting),
                        )

                        st.success(
                            "✅ Το checklist ενημερώθηκε!"
                        )

                        st.rerun()

        else:

            st.info(
                "Δεν υπάρχουν onboarding διαδικασίες."
            )


# ============================================================
# HR LEAVES
# ============================================================

elif page == "🏖️ Άδειες":

    if not IS_HR:
        st.error(
            "⛔ Δεν έχεις δικαίωμα πρόσβασης."
        )
        st.stop()

    st.title(
        "🏖️ Διαχείριση Αδειών"
    )

    employees = get_employees()

    if not employees:

        st.warning(
            "Πρέπει πρώτα να προσθέσεις εργαζόμενο."
        )

    else:

        # ----------------------------------------------------
        # ADD LEAVE
        # ----------------------------------------------------

        st.subheader(
            "➕ Νέα αίτηση άδειας"
        )

        employee_options = {
            f'{employee["first_name"]} '
            f'{employee["last_name"]}':
            employee["id"]
            for employee in employees
        }

        with st.form(
            "leave_form"
        ):

            selected_employee = st.selectbox(
                "Εργαζόμενος",
                list(employee_options.keys()),
            )

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

            start_date = st.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            end_date = st.date_input(
                "Ημερομηνία λήξης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            reason = st.text_area(
                "Αιτιολογία"
            )

            submitted = st.form_submit_button(
                "📨 Υποβολή αίτησης"
            )

            if submitted:

                if end_date < start_date:

                    st.error(
                        "Η ημερομηνία λήξης δεν μπορεί "
                        "να είναι πριν από την ημερομηνία έναρξης."
                    )

                else:

                    employee_id = employee_options[
                        selected_employee
                    ]

                    add_leave(
                        employee_id,
                        leave_type,
                        start_date.strftime(
                            "%Y-%m-%d"
                        ),
                        end_date.strftime(
                            "%Y-%m-%d"
                        ),
                        reason,
                    )

                    st.success(
                        "✅ Η αίτηση άδειας καταχωρήθηκε!"
                    )

                    st.rerun()

        st.divider()

        # ----------------------------------------------------
        # LEAVE REQUESTS
        # ----------------------------------------------------

        st.subheader(
            "📋 Αιτήσεις αδειών"
        )

        leaves = get_leaves()

        if leaves:

            leave_data = []

            for leave in leaves:

                leave_data.append(
                    {
                        "ID": leave["id"],
                        "Εργαζόμενος":
                            f'{leave["first_name"]} '
                            f'{leave["last_name"]}',
                        "Τύπος":
                            leave["leave_type"],
                        "Από":
                            leave["start_date"],
                        "Έως":
                            leave["end_date"],
                        "Αιτιολογία":
                            leave["reason"],
                        "Κατάσταση":
                            leave["status"],
                    }
                )

            df_leaves = pd.DataFrame(
                leave_data
            )

            st.dataframe(
                df_leaves,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            # ------------------------------------------------
            # APPROVAL CENTER
            # ------------------------------------------------

            st.subheader(
                "✅ HR Approval Center"
            )

            pending_leaves = [
                leave
                for leave in leaves
                if leave["status"] == "Εκκρεμεί"
            ]

            if pending_leaves:

                for leave in pending_leaves:

                    with st.container(
                        border=True
                    ):

                        st.write(
                            f"**#{leave['id']} — "
                            f"{leave['first_name']} "
                            f"{leave['last_name']}**"
                        )

                        st.write(
                            f"Τύπος: {leave['leave_type']}"
                        )

                        st.write(
                            f"Από: {leave['start_date']} "
                            f"Έως: {leave['end_date']}"
                        )

                        st.write(
                            f"Αιτιολογία: "
                            f"{leave['reason'] or '-'}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            if st.button(
                                "✅ Έγκριση",
                                key=f"approve_{leave['id']}",
                            ):

                                update_leave_status(
                                    leave["id"],
                                    "Εγκρίθηκε",
                                )

                                st.success(
                                    "Η αίτηση εγκρίθηκε."
                                )

                                st.rerun()

                        with col2:

                            if st.button(
                                "❌ Απόρριψη",
                                key=f"reject_{leave['id']}",
                            ):

                                update_leave_status(
                                    leave["id"],
                                    "Απορρίφθηκε",
                                )

                                st.warning(
                                    "Η αίτηση απορρίφθηκε."
                                )

                                st.rerun()

            else:

                st.success(
                    "✅ Δεν υπάρχουν εκκρεμή αιτήματα."
                )

        else:

            st.info(
                "Δεν υπάρχουν αιτήσεις άδειας."
            )


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title(
        "🤖 AI HR Assistant"
    )

    st.markdown(
        "Ο έξυπνος βοηθός του τμήματος "
        "Ανθρώπινου Δυναμικού."
    )

    if client is None:

        st.error(
            "Δεν βρέθηκε το OPENAI_API_KEY. "
            "Για το Cloud βάλε το OPENAI_API_KEY "
            "στα Streamlit Secrets."
        )

    else:

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # ----------------------------------------------------
        # CHAT HISTORY
        # ----------------------------------------------------

        for message in st.session_state.messages:

            with st.chat_message(
                message["role"]
            ):

                st.markdown(
                    message["content"]
                )

        # ----------------------------------------------------
        # QUESTION
        # ----------------------------------------------------

        question = st.chat_input(
            "Γράψε την ερώτησή σου..."
        )

        if question:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": question,
                }
            )

            with st.chat_message("user"):

                st.markdown(
                    question
                )

            with st.chat_message("assistant"):

                with st.spinner(
                    "Το AI σκέφτεται..."
                ):

                    try:

                        response = client.responses.create(
                            model="gpt-5-mini",
                            instructions="""
Είσαι ένας επαγγελματικός AI HR Assistant.

Βοηθάς σε:
- Recruitment
- Onboarding
- Employee Management
- HR Administration
- HR KPIs
- Επαγγελματικά HR emails
- Περιγραφές θέσεων εργασίας
- Αγγελίες εργασίας
- HR διαδικασίες
- Οργάνωση προσωπικού

Απαντάς στα ελληνικά,
εκτός αν ζητηθεί άλλη γλώσσα.

Οι απαντήσεις σου είναι:
- επαγγελματικές
- πρακτικές
- σαφείς
- οργανωμένες
- εύκολες στην εφαρμογή

Δεν παρουσιάζεις νομική συμβουλή ως βεβαιότητα.
Σε θέματα εργατικής νομοθεσίας προτείνεις
έλεγχο από αρμόδιο επαγγελματία.
""",
                            input=question,
                        )

                        answer = (
                            response.output_text
                        )

                        st.markdown(
                            answer
                        )

                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": answer,
                            }
                        )

                    except Exception as e:

                        st.error(
                            f"Παρουσιάστηκε σφάλμα: {e}"
                        )

        st.divider()

        if st.button(
            "🗑️ Καθαρισμός συνομιλίας"
        ):

            st.session_state.messages = []

            st.rerun()

