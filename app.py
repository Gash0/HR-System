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
    update_employee,
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
# GOOGLE AUTHENTICATION
# ============================================================

if not st.user.is_logged_in:
    st.title("🔐 AI HR System")
    st.subheader("Σύνδεση στο HR System")

    st.write(
        "Συνδέσου με τον εταιρικό ή προσωπικό Google λογαριασμό σου."
    )

    st.button(
        "🔑 Σύνδεση με Google",
        on_click=st.login,
    )

    st.stop()


# ============================================================
# USER / ROLE
# ============================================================

user_email = (st.user.email or "").strip().lower()

admin_emails = [
    str(email).strip().lower()
    for email in st.secrets["roles"]["admin_emails"]
]

hr_emails = [
    str(email).strip().lower()
    for email in st.secrets["roles"]["hr_emails"]
]

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

display_name = getattr(st.user, "name", None)

if not display_name:
    display_name = user_email

st.sidebar.success(
    f"👤 {display_name}"
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

client = OpenAI(api_key=api_key) if api_key else None


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
st.sidebar.caption(
    "AI HR Management System"
)


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

    departments = sorted(
        {
            employee.get("department")
            for employee in employees
            if employee.get("department")
        }
    )

    department_filter = st.selectbox(
        "🏢 Φίλτρο τμήματος",
        ["Όλα"] + departments,
        key="dashboard_department_filter",
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
        (filtered_active / filtered_total) * 100
        if filtered_total > 0
        else 0
    )

    # --------------------------------------------------------
    # KPI ROW 1
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 Σύνολο εργαζομένων",
            filtered_total,
        )

    with col2:
        st.metric(
            "✅ Ενεργοί",
            filtered_active,
        )

    with col3:
        st.metric(
            "📋 Υποψήφιοι",
            stats["total_candidates"],
        )

    with col4:
        st.metric(
            "⏳ Εκκρεμείς άδειες",
            stats["pending_leaves"],
        )

    # --------------------------------------------------------
    # KPI ROW 2
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
            "🏖️ Σύνολο αδειών",
            stats["total_leaves"],
        )

    with col4:
        st.metric(
            "📈 Active Rate",
            f"{active_rate:.1f}%",
        )

    st.divider()

    # --------------------------------------------------------
    # DEPARTMENT ANALYTICS
    # --------------------------------------------------------

    st.subheader(
        "👥 Εργαζόμενοι ανά τμήμα"
    )

    if employees:

        employee_df = pd.DataFrame(employees)

        if "department" in employee_df.columns:

            department_counts = (
                employee_df["department"]
                .fillna("Χωρίς τμήμα")
                .replace("", "Χωρίς τμήμα")
                .value_counts()
            )

            st.bar_chart(
                department_counts
            )

    else:

        st.info(
            "Δεν υπάρχουν εργαζόμενοι."
        )

    st.divider()

    # --------------------------------------------------------
    # EMPLOYEE STATUS
    # --------------------------------------------------------

    st.subheader(
        "📊 Κατάσταση εργαζομένων"
    )

    if filtered_employees:

        filtered_df = pd.DataFrame(
            filtered_employees
        )

        status_counts = (
            filtered_df["status"]
            .fillna("Άγνωστη κατάσταση")
            .value_counts()
        )

        st.bar_chart(
            status_counts
        )

    else:

        st.info(
            "Δεν υπάρχουν δεδομένα για το συγκεκριμένο τμήμα."
        )

    st.divider()

    # --------------------------------------------------------
    # RECRUITMENT
    # --------------------------------------------------------

    st.subheader(
        "📋 Recruitment"
    )

    if candidates:

        candidate_df = pd.DataFrame(
            candidates
        )

        recruitment_counts = (
            candidate_df["status"]
            .fillna("Άγνωστη κατάσταση")
            .value_counts()
        )

        st.bar_chart(
            recruitment_counts
        )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι."
        )

    # --------------------------------------------------------
    # RECRUITMENT FUNNEL
    # --------------------------------------------------------

    st.subheader(
        "🎯 Recruitment Funnel"
    )

    if candidates:

        candidate_df = pd.DataFrame(
            candidates
        )

        if "status" in candidate_df.columns:

            funnel_order = [
                "Νέα αίτηση",
                "Σε αξιολόγηση",
                "Συνέντευξη",
                "Προσλήφθηκε",
                "Απορρίφθηκε",
            ]

            funnel_counts = (
                candidate_df["status"]
                .value_counts()
                .reindex(
                    funnel_order,
                    fill_value=0
                )
            )

            st.bar_chart(
                funnel_counts
            )

            total_candidates = len(
                candidate_df
            )

            hired_candidates = int(
                (
                    candidate_df["status"]
                    == "Προσλήφθηκε"
                ).sum()
            )

            hiring_rate = (
                (hired_candidates / total_candidates) * 100
                if total_candidates > 0
                else 0
            )

            st.metric(
                "📈 Ποσοστό πρόσληψης",
                f"{hiring_rate:.1f}%",
            )

    else:

        st.info(
            "Δεν υπάρχουν δεδομένα recruitment."
        )

    st.divider()

    # --------------------------------------------------------
    # LEAVE ANALYTICS
    # --------------------------------------------------------

    st.subheader(
        "🏖️ Leave Analytics"
    )

    if leaves:

        leave_df = pd.DataFrame(
            leaves
        )

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

    st.subheader(
        "👤 Πρόσφατοι εργαζόμενοι"
    )

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

    st.title(
        "👤 Το προφίλ μου"
    )

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
                employee["first_name"] or "-"
            )

            st.write(
                "**Επώνυμο:**",
                employee["last_name"] or "-"
            )

            st.write(
                "**Email:**",
                employee["email"] or "-"
            )

            st.write(
                "**Τηλέφωνο:**",
                employee["phone"] or "-"
            )

        with col2:

            st.write(
                "**Θέση:**",
                employee["position"] or "-"
            )

            st.write(
                "**Τμήμα:**",
                employee["department"] or "-"
            )

            st.write(
                "**Ημερομηνία πρόσληψης:**",
                employee["hire_date"] or "-"
            )

            st.write(
                "**Κατάσταση:**",
                employee["status"] or "-"
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

        st.subheader(
            "📋 Ιστορικό αδειών"
        )

        if my_leaves:

            leave_data = []

            for leave in my_leaves:

                leave_data.append(
                    {
                        "Τύπος":
                            leave["leave_type"],
                        "Από":
                            leave["start_date"],
                        "Έως":
                            leave["end_date"],
                        "Αιτιολογία":
                            leave["reason"] or "-",
                        "Κατάσταση":
                            leave["status"],
                    }
                )

            st.dataframe(
                pd.DataFrame(leave_data),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "Δεν υπάρχουν καταχωρημένες άδειες."
            )

        st.divider()

        # ----------------------------------------------------
        # LEAVE REQUEST
        # ----------------------------------------------------

        st.subheader(
            "➕ Νέο αίτημα άδειας"
        )

        with st.form(
            "employee_leave_request"
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
                        "✅ Το αίτημα άδειας υποβλήθηκε."
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

            if not first_name.strip():

                st.error(
                    "Το Όνομα είναι υποχρεωτικό."
                )

            elif not last_name.strip():

                st.error(
                    "Το Επώνυμο είναι υποχρεωτικό."
                )

            else:

                normalized_email = (
                    email.strip().lower()
                    if email.strip()
                    else None
                )

                try:

                    add_employee(
                        first_name.strip(),
                        last_name.strip(),
                        normalized_email,
                        phone.strip(),
                        position.strip(),
                        department.strip(),
                        hire_date.strftime(
                            "%Y-%m-%d"
                        ),
                        status,
                    )

                    st.success(
                        "✅ Ο εργαζόμενος προστέθηκε."
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
                            f"❌ Σφάλμα αποθήκευσης: {e}"
                        )

    st.divider()

    # --------------------------------------------------------
    # EMPLOYEE LIST
    # --------------------------------------------------------

    st.subheader(
        "📋 Λίστα εργαζομένων"
    )

    employees = get_employees()

    if employees:

        search_text = st.text_input(
            "🔎 Αναζήτηση",
            placeholder="Όνομα, επώνυμο ή email...",
            key="employee_search",
        )

        department_options = sorted(
            {
                employee.get("department")
                for employee in employees
                if employee.get("department")
            }
        )

        selected_department = st.selectbox(
            "🏢 Τμήμα",
            ["Όλα"] + department_options,
            key="employee_department_filter",
        )

        selected_status = st.selectbox(
            "📌 Κατάσταση",
            [
                "Όλες",
                "Ενεργός",
                "Ανενεργός",
                "Σε άδεια",
            ],
            key="employee_status_filter",
        )

        filtered_employees = employees

        if search_text.strip():

            search_lower = search_text.strip().lower()

            filtered_employees = [
                employee
                for employee in filtered_employees
                if search_lower in (
                    employee.get("first_name")
                    or ""
                ).lower()
                or search_lower in (
                    employee.get("last_name")
                    or ""
                ).lower()
                or search_lower in (
                    employee.get("email")
                    or ""
                ).lower()
            ]

        if selected_department != "Όλα":

            filtered_employees = [
                employee
                for employee in filtered_employees
                if employee.get("department")
                == selected_department
            ]

        if selected_status != "Όλες":

            filtered_employees = [
                employee
                for employee in filtered_employees
                if employee.get("status")
                == selected_status
            ]

        st.caption(
            f"Βρέθηκαν {len(filtered_employees)} εργαζόμενοι."
        )

        employee_data = []

        for employee in filtered_employees:

            employee_data.append(
                {
                    "ID":
                        employee["id"],
                    "Όνομα":
                        employee["first_name"],
                    "Επώνυμο":
                        employee["last_name"],
                    "Email":
                        employee["email"],
                    "Τηλέφωνο":
                        employee["phone"],
                    "Θέση":
                        employee["position"],
                    "Τμήμα":
                        employee["department"],
                    "Ημερομηνία πρόσληψης":
                        employee["hire_date"],
                    "Κατάσταση":
                        employee["status"],
                }
            )

        st.dataframe(
            pd.DataFrame(employee_data),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ----------------------------------------------------
        # EMPLOYEE PROFILE 2.0
        # ----------------------------------------------------

        st.subheader(
            "👤 Employee Profile"
        )

        profile_options = {
            f'{employee["first_name"]} '
            f'{employee["last_name"]} '
            f'— {employee["position"] or "Χωρίς θέση"} '
            f'(ID: {employee["id"]})':
            employee
            for employee in filtered_employees
        }

        if profile_options:

            selected_profile_name = st.selectbox(
                "Επίλεξε εργαζόμενο",
                list(profile_options.keys()),
                key="employee_profile_selector",
            )

            selected_employee = profile_options[
                selected_profile_name
            ]

            st.markdown(
                f"### 👤 "
                f"{selected_employee['first_name']} "
                f"{selected_employee['last_name']}"
            )

            st.caption(
                f"{selected_employee['position'] or 'Χωρίς θέση'} "
                f"• "
                f"{selected_employee['department'] or 'Χωρίς τμήμα'}"
            )

            # ------------------------------------------------
            # LOAD EMPLOYEE HISTORY
            # ------------------------------------------------

            all_leaves = get_leaves()
            all_onboarding = get_onboarding()

            employee_leaves = [
                leave
                for leave in all_leaves
                if leave["employee_id"]
                == selected_employee["id"]
            ]

            employee_onboarding = [
                item
                for item in all_onboarding
                if item["employee_id"]
                == selected_employee["id"]
            ]

            approved_leaves = sum(
                1
                for leave in employee_leaves
                if leave["status"] == "Εγκρίθηκε"
            )

            pending_leaves = sum(
                1
                for leave in employee_leaves
                if leave["status"] == "Εκκρεμεί"
            )

            # ------------------------------------------------
            # PROFILE KPIs
            # ------------------------------------------------

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "📌 Κατάσταση",
                    selected_employee["status"] or "-"
                )

            with col2:
                st.metric(
                    "🏖️ Σύνολο αδειών",
                    len(employee_leaves)
                )

            with col3:
                st.metric(
                    "✅ Εγκεκριμένες",
                    approved_leaves
                )

            with col4:
                st.metric(
                    "⏳ Εκκρεμείς",
                    pending_leaves
                )

            # ------------------------------------------------
            # PROFILE TABS
            # ------------------------------------------------

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "👤 Στοιχεία",
                    "🏖️ Άδειες",
                    "🚀 Onboarding",
                    "📋 Ιστορικό",
                ]
            )

            # =================================================
            # TAB 1 - DETAILS / EDIT
            # =================================================

            with tab1:

                st.subheader(
                    "👤 Στοιχεία εργαζομένου"
                )

                with st.form(
                    f"edit_employee_{selected_employee['id']}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        edit_first_name = st.text_input(
                            "Όνομα",
                            value=selected_employee[
                                "first_name"
                            ] or "",
                        )

                        edit_last_name = st.text_input(
                            "Επώνυμο",
                            value=selected_employee[
                                "last_name"
                            ] or "",
                        )

                        edit_email = st.text_input(
                            "Email",
                            value=selected_employee[
                                "email"
                            ] or "",
                        )

                        edit_phone = st.text_input(
                            "Τηλέφωνο",
                            value=selected_employee[
                                "phone"
                            ] or "",
                        )

                    with col2:

                        edit_position = st.text_input(
                            "Θέση",
                            value=selected_employee[
                                "position"
                            ] or "",
                        )

                        edit_department = st.text_input(
                            "Τμήμα",
                            value=selected_employee[
                                "department"
                            ] or "",
                        )

                        edit_hire_date = st.text_input(
                            "Ημερομηνία πρόσληψης",
                            value=selected_employee[
                                "hire_date"
                            ] or "",
                        )

                        status_options = [
                            "Ενεργός",
                            "Ανενεργός",
                            "Σε άδεια",
                        ]

                        current_status = (
                            selected_employee[
                                "status"
                            ]
                        )

                        edit_status = st.selectbox(
                            "Κατάσταση",
                            status_options,
                            index=(
                                status_options.index(
                                    current_status
                                )
                                if current_status
                                in status_options
                                else 0
                            ),
                        )

                    save_changes = st.form_submit_button(
                        "💾 Αποθήκευση αλλαγών"
                    )

                    if save_changes:

                        if (
                            not edit_first_name.strip()
                            or not edit_last_name.strip()
                        ):

                            st.error(
                                "Το Όνομα και το Επώνυμο "
                                "είναι υποχρεωτικά."
                            )

                        else:

                            normalized_email = (
                                edit_email.strip().lower()
                                if edit_email.strip()
                                else None
                            )

                            try:

                                update_employee(
                                    selected_employee["id"],
                                    edit_first_name.strip(),
                                    edit_last_name.strip(),
                                    normalized_email,
                                    edit_phone.strip(),
                                    edit_position.strip(),
                                    edit_department.strip(),
                                    edit_hire_date.strip(),
                                    edit_status,
                                )

                                st.success(
                                    "✅ Τα στοιχεία "
                                    "ενημερώθηκαν."
                                )

                                st.rerun()

                            except Exception as e:

                                if (
                                    "UniqueViolation"
                                    in str(e)
                                    or "duplicate key"
                                    in str(e).lower()
                                ):

                                    st.error(
                                        "❌ Υπάρχει ήδη εργαζόμενος "
                                        "με αυτό το email."
                                    )

                                else:

                                    st.error(
                                        f"❌ Σφάλμα ενημέρωσης: {e}"
                                    )

            # =================================================
            # TAB 2 - LEAVES
            # =================================================

            with tab2:

                st.subheader(
                    "🏖️ Ιστορικό αδειών"
                )

                if employee_leaves:

                    leave_data = []

                    for leave in employee_leaves:

                        leave_data.append(
                            {
                                "Τύπος":
                                    leave["leave_type"],
                                "Από":
                                    leave["start_date"],
                                "Έως":
                                    leave["end_date"],
                                "Αιτιολογία":
                                    leave["reason"] or "-",
                                "Κατάσταση":
                                    leave["status"],
                            }
                        )

                    st.dataframe(
                        pd.DataFrame(
                            leave_data
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                else:

                    st.info(
                        "Δεν υπάρχουν άδειες."
                    )

            # =================================================
            # TAB 3 - ONBOARDING
            # =================================================

            with tab3:

                st.subheader(
                    "🚀 Onboarding"
                )

                if employee_onboarding:

                    for item in employee_onboarding:

                        completed_tasks = sum(
                            [
                                bool(item["contract"]),
                                bool(item["documents"]),
                                bool(item["email"]),
                                bool(item["equipment"]),
                                bool(item["system_access"]),
                                bool(item["training"]),
                                bool(item["manager_meeting"]),
                            ]
                        )

                        total_tasks = 7

                        completion = (
                            completed_tasks
                            / total_tasks
                        ) * 100

                        st.write(
                            f"**Ημερομηνία έναρξης:** "
                            f"{item['start_date'] or '-'}"
                        )

                        st.progress(
                            completion / 100
                        )

                        st.write(
                            f"**Ολοκλήρωση:** "
                            f"{completed_tasks}/{total_tasks} "
                            f"({completion:.0f}%)"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                "📄 Σύμβαση: "
                                f"{'✅' if item['contract'] else '❌'}"
                            )

                            st.write(
                                "📁 Έγγραφα: "
                                f"{'✅' if item['documents'] else '❌'}"
                            )

                            st.write(
                                "📧 Email: "
                                f"{'✅' if item['email'] else '❌'}"
                            )

                            st.write(
                                "💻 Εξοπλισμός: "
                                f"{'✅' if item['equipment'] else '❌'}"
                            )

                        with col2:

                            st.write(
                                "🔐 Πρόσβαση: "
                                f"{'✅' if item['system_access'] else '❌'}"
                            )

                            st.write(
                                "🎓 Εκπαίδευση: "
                                f"{'✅' if item['training'] else '❌'}"
                            )

                            st.write(
                                "🤝 Manager Meeting: "
                                f"{'✅' if item['manager_meeting'] else '❌'}"
                            )

                        st.divider()

                else:

                    st.info(
                        "Δεν υπάρχει onboarding."
                    )

            # =================================================
            # TAB 4 - HISTORY
            # =================================================

            with tab4:

                st.subheader(
                    "📋 Ιστορικό εργαζομένου"
                )

                st.write(
                    f"📅 Ημερομηνία πρόσληψης: "
                    f"{selected_employee['hire_date'] or '-'}"
                )

                st.write(
                    f"🏢 Τμήμα: "
                    f"{selected_employee['department'] or '-'}"
                )

                st.write(
                    f"💼 Θέση: "
                    f"{selected_employee['position'] or '-'}"
                )

                st.write(
                    f"📌 Κατάσταση: "
                    f"{selected_employee['status'] or '-'}"
                )

                st.divider()

                st.write(
                    f"🏖️ Αιτήματα άδειας: "
                    f"{len(employee_leaves)}"
                )

                st.write(
                    f"✅ Εγκεκριμένες άδειες: "
                    f"{approved_leaves}"
                )

                st.write(
                    f"⏳ Εκκρεμή αιτήματα: "
                    f"{pending_leaves}"
                )

                st.write(
                    f"🚀 Onboarding: "
                    f"{'Υπάρχει' if employee_onboarding else 'Δεν υπάρχει'}"
                )

        else:

            st.info(
                "Δεν βρέθηκαν εργαζόμενοι με τα συγκεκριμένα φίλτρα."
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

        selected_delete_employee = st.selectbox(
            "Επίλεξε εργαζόμενο",
            list(employee_options.keys()),
            key="delete_employee_selector",
        )

        if st.button(
            "🗑️ Διαγραφή εργαζομένου",
            type="secondary",
        ):

            employee_id = employee_options[
                selected_delete_employee
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
# RECRUITMENT 2.0
# ============================================================

elif page == "📋 Recruitment":

    if not IS_HR:
        st.error(
            "⛔ Δεν έχεις δικαίωμα πρόσβασης."
        )
        st.stop()

    st.title("📋 Recruitment 2.0")

    st.caption(
        "Διαχείριση υποψηφίων και pipeline προσλήψεων."
    )

    candidates = get_candidates()

    # ========================================================
    # ADD CANDIDATE
    # ========================================================

    st.subheader("➕ Νέος υποψήφιος")

    with st.form("candidate_form"):

        col1, col2 = st.columns(2)

        with col1:

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

        with col2:

            position = st.text_input(
                "Θέση εργασίας"
            )

            application_date = st.date_input(
                "Ημερομηνία αίτησης",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            status = st.selectbox(
                "Αρχική κατάσταση",
                [
                    "Νέα αίτηση",
                    "Σε αξιολόγηση",
                    "Συνέντευξη",
                    "Προσφορά",
                    "Προσλήφθηκε",
                    "Απορρίφθηκε",
                ],
            )

        submitted = st.form_submit_button(
            "💾 Προσθήκη υποψηφίου"
        )

        if submitted:

            if not first_name.strip():

                st.error(
                    "Το Όνομα είναι υποχρεωτικό."
                )

            elif not last_name.strip():

                st.error(
                    "Το Επώνυμο είναι υποχρεωτικό."
                )

            else:

                add_candidate(
                    first_name.strip(),
                    last_name.strip(),
                    email.strip() or None,
                    phone.strip(),
                    position.strip(),
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

    # ========================================================
    # PIPELINE SUMMARY
    # ========================================================

    st.subheader("🎯 Recruitment Pipeline")

    pipeline_statuses = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
        "Απορρίφθηκε",
    ]

    pipeline_counts = {
        status: 0
        for status in pipeline_statuses
    }

    for candidate in candidates:

        candidate_status = candidate.get(
            "status"
        )

        if candidate_status in pipeline_counts:
            pipeline_counts[candidate_status] += 1

    cols = st.columns(6)

    for index, pipeline_status in enumerate(
        pipeline_statuses
    ):

        with cols[index]:

            st.metric(
                pipeline_status,
                pipeline_counts[pipeline_status],
            )

    st.divider()

    # ========================================================
    # SEARCH / FILTER
    # ========================================================

    st.subheader("🔎 Αναζήτηση υποψηφίων")

    col1, col2 = st.columns(2)

    with col1:

        search_text = st.text_input(
            "Όνομα, επώνυμο ή email",
            placeholder="Αναζήτηση..."
        )

    with col2:

        status_filter = st.selectbox(
            "📌 Κατάσταση",
            ["Όλες"] + pipeline_statuses
        )

    filtered_candidates = candidates

    if search_text.strip():

        search_lower = (
            search_text.strip().lower()
        )

        filtered_candidates = [
            candidate
            for candidate in filtered_candidates
            if search_lower in (
                candidate.get("first_name")
                or ""
            ).lower()
            or search_lower in (
                candidate.get("last_name")
                or ""
            ).lower()
            or search_lower in (
                candidate.get("email")
                or ""
            ).lower()
        ]

    if status_filter != "Όλες":

        filtered_candidates = [
            candidate
            for candidate in filtered_candidates
            if candidate.get("status")
            == status_filter
        ]

    st.caption(
        f"Βρέθηκαν {len(filtered_candidates)} υποψήφιοι."
    )

    # ========================================================
    # KANBAN STYLE PIPELINE
    # ========================================================

    st.subheader("📊 Pipeline")

    visible_pipeline = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
    ]

    pipeline_columns = st.columns(
        len(visible_pipeline)
    )

    for index, pipeline_status in enumerate(
        visible_pipeline
    ):

        with pipeline_columns[index]:

            st.markdown(
                f"### {pipeline_status}"
            )

            status_candidates = [
                candidate
                for candidate in filtered_candidates
                if candidate.get("status")
                == pipeline_status
            ]

            if not status_candidates:

                st.caption(
                    "Κανένας υποψήφιος"
                )

            else:

                for candidate in status_candidates:

                    with st.container(
                        border=True
                    ):

                        full_name = (
                            f'{candidate["first_name"]} '
                            f'{candidate["last_name"]}'
                        )

                        st.write(
                            f"**{full_name}**"
                        )

                        st.caption(
                            candidate.get(
                                "position"
                            )
                            or "Χωρίς θέση"
                        )

                        if candidate.get("email"):

                            st.write(
                                f"📧 "
                                f"{candidate['email']}"
                            )

                        st.write(
                            f"📅 "
                            f"{candidate['application_date']}"
                        )

    st.divider()

    # ========================================================
    # CANDIDATE MANAGEMENT
    # ========================================================

    st.subheader(
        "⚙️ Διαχείριση υποψηφίου"
    )

    if filtered_candidates:

        candidate_options = {
            (
                f'{candidate["first_name"]} '
                f'{candidate["last_name"]} '
                f'(ID: {candidate["id"]})'
            ):
            candidate
            for candidate in filtered_candidates
        }

        selected_candidate_name = st.selectbox(
            "Επίλεξε υποψήφιο",
            list(candidate_options.keys()),
            key="recruitment_candidate_selector",
        )

        selected_candidate = candidate_options[
            selected_candidate_name
        ]

        st.markdown(
            f"### 👤 "
            f"{selected_candidate['first_name']} "
            f"{selected_candidate['last_name']}"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Email:** "
                f"{selected_candidate['email'] or '-'}"
            )

            st.write(
                f"**Τηλέφωνο:** "
                f"{selected_candidate['phone'] or '-'}"
            )

            st.write(
                f"**Θέση:** "
                f"{selected_candidate['position'] or '-'}"
            )

        with col2:

            st.write(
                f"**Ημερομηνία αίτησης:** "
                f"{selected_candidate['application_date']}"
            )

            st.write(
                f"**Τρέχουσα κατάσταση:** "
                f"{selected_candidate['status']}"
            )

        new_status = st.selectbox(
            "🔄 Νέα κατάσταση",
            pipeline_statuses,
            index=(
                pipeline_statuses.index(
                    selected_candidate["status"]
                )
                if selected_candidate["status"]
                in pipeline_statuses
                else 0
            ),
            key="candidate_new_status",
        )

        if st.button(
            "💾 Ενημέρωση κατάστασης",
            key="update_candidate_status",
        ):

            st.warning(
                "Η αλλαγή status απαιτεί "
                "τη νέα συνάρτηση update_candidate(), "
                "την οποία θα προσθέσουμε στο database.py "
                "στο επόμενο βήμα."
            )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι με τα συγκεκριμένα φίλτρα."
        )

    st.divider()

    # ========================================================
    # RECRUITMENT TABLE
    # ========================================================

    st.subheader(
        "📋 Πλήρης λίστα υποψηφίων"
    )

    if filtered_candidates:

        candidate_table = []

        for candidate in filtered_candidates:

            candidate_table.append(
                {
                    "ID":
                        candidate["id"],
                    "Όνομα":
                        candidate["first_name"],
                    "Επώνυμο":
                        candidate["last_name"],
                    "Email":
                        candidate["email"],
                    "Θέση":
                        candidate["position"],
                    "Ημερομηνία":
                        candidate["application_date"],
                    "Κατάσταση":
                        candidate["status"],
                }
            )

        st.dataframe(
            pd.DataFrame(candidate_table),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι."
        )



    # --------------------------------------------------------
    # CANDIDATE LIST
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
                    "ID":
                        candidate["id"],
                    "Όνομα":
                        candidate["first_name"],
                    "Επώνυμο":
                        candidate["last_name"],
                    "Email":
                        candidate["email"],
                    "Τηλέφωνο":
                        candidate["phone"],
                    "Θέση":
                        candidate["position"],
                    "Ημερομηνία αίτησης":
                        candidate["application_date"],
                    "Κατάσταση":
                        candidate["status"],
                }
            )

        st.dataframe(
            pd.DataFrame(candidate_data),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι."
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

    st.caption(
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
                    "✅ Το onboarding δημιουργήθηκε."
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
                        value=bool(item["contract"]),
                        key=f"contract_{item['id']}",
                    )

                    documents = st.checkbox(
                        "📁 Έγγραφα",
                        value=bool(item["documents"]),
                        key=f"documents_{item['id']}",
                    )

                    email_setup = st.checkbox(
                        "📧 Email",
                        value=bool(item["email"]),
                        key=f"email_{item['id']}",
                    )

                    equipment = st.checkbox(
                        "💻 Εξοπλισμός",
                        value=bool(item["equipment"]),
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
                        value=bool(item["training"]),
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
                            "✅ Το checklist ενημερώθηκε."
                        )

                        st.rerun()

        else:

            st.info(
                "Δεν υπάρχουν onboarding διαδικασίες."
            )


# ============================================================
# HR LEAVE MANAGEMENT
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
        # CREATE LEAVE
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
                        "Εκκρεμεί",
                    )

                    st.success(
                        "✅ Η αίτηση άδειας καταχωρήθηκε."
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
                        "ID":
                            leave["id"],
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
                            leave["reason"] or "-",
                        "Κατάσταση":
                            leave["status"],
                    }
                )

            st.dataframe(
                pd.DataFrame(leave_data),
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

    st.caption(
        "Ο έξυπνος βοηθός του τμήματος Ανθρώπινου Δυναμικού."
    )

    if client is None:

        st.error(
            "Δεν βρέθηκε το OPENAI_API_KEY."
        )

        st.info(
            "Στο Streamlit Cloud πρόσθεσε το "
            "OPENAI_API_KEY στα Secrets."
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
        # CHAT INPUT
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

            with st.chat_message(
                "user"
            ):

                st.markdown(
                    question
                )

            with st.chat_message(
                "assistant"
            ):

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
- Employee Management
- Onboarding
- HR Administration
- HR KPIs
- HR emails
- Job descriptions
- Job advertisements
- HR processes
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

                        answer = response.output_text

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

