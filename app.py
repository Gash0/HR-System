from datetime import date, datetime, timedelta

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

    if value is None:
        return ""

    return str(value)


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

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                text[:19],
                fmt,
            ).date()

        except ValueError:
            pass

    return default


def format_date(value):

    if not value:
        return "-"

    return parse_date(
        value
    ).strftime(
        "%d/%m/%Y"
    )


def get_role(user_email):

    email = safe_text(
        user_email
    ).strip().lower()

    try:

        roles = st.secrets.get(
            "roles",
            {},
        )

        admin_emails = [
            str(item).lower()
            for item
            in roles.get(
                "admin_emails",
                [],
            )
        ]

        hr_emails = [
            str(item).lower()
            for item
            in roles.get(
                "hr_emails",
                [],
            )
        ]

    except Exception:

        admin_emails = []
        hr_emails = []

    if email in admin_emails:
        return "Admin"

    if email in hr_emails:
        return "HR"

    return "Employee"


def onboarding_progress(row):

    task_keys = [
        "contract",
        "documents",
        "email",
        "equipment",
        "system_access",
        "training",
        "manager_meeting",
    ]

    completed = sum(
        int(
            bool(
                row.get(key)
            )
        )
        for key
        in task_keys
    )

    percentage = round(
        completed / 7 * 100
    )

    return completed, percentage


def onboarding_status_from_row(row):

    completed, _ = onboarding_progress(
        row
    )

    if completed == 7:
        return "Ολοκληρώθηκε"

    if completed > 0:
        return "Σε εξέλιξη"

    return "Δεν ξεκίνησε"


# ============================================================
# LOGIN
# ============================================================

if not st.user.is_logged_in:

    st.title(
        "👥 AI HR System"
    )

    st.write(
        "Συνδέσου με τον λογαριασμό σου."
    )

    st.button(
        "🔑 Σύνδεση με Google",
        on_click=st.login,
    )

    st.stop()


user_email = st.user.get(
    "email",
    "",
)

user_name = st.user.get(
    "name",
    user_email,
)

user_role = get_role(
    user_email
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🤖 AI HR System"
)

st.sidebar.write(
    user_name
)

st.sidebar.caption(
    f"Ρόλος: {user_role}"
)

st.sidebar.markdown(
    "---"
)


if user_role in (
    "Admin",
    "HR",
):

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


st.sidebar.markdown(
    "---"
)


if st.sidebar.button(
    "🚪 Αποσύνδεση"
):

    st.logout()


# ============================================================
# DASHBOARD 2.0
# ============================================================

if page == "📊 Dashboard":

    st.title(
        "📊 HR Dashboard"
    )

    st.caption(
        "Συνολική εικόνα Ανθρώπινου Δυναμικού, Recruitment, Onboarding και Αδειών."
    )


    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    stats = get_hr_statistics()

    employees = get_employees()

    candidates = get_candidates()

    onboarding_rows = get_onboarding()

    leaves = get_leaves()


    # --------------------------------------------------------
    # EMPLOYEE KPIS
    # --------------------------------------------------------

    st.subheader(
        "👥 Workforce"
    )

    total_employees = stats.get(
        "total_employees",
        0,
    )

    active_employees = stats.get(
        "active_employees",
        0,
    )

    active_employee_rate = (
        round(
            active_employees / total_employees * 100
        )
        if total_employees
        else 0
    )

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric(
        "Σύνολο εργαζομένων",
        stats.get(
            "total_employees",
            0,
        ),
    )

    kpi2.metric(
        "Ενεργοί",
        stats.get(
            "active_employees",
            0,
        ),
    )

    kpi3.metric(
        "Ανενεργοί",
        stats.get(
            "inactive_employees",
            0,
        ),
    )

    departments = set()

    for employee in employees:
        department = safe_text(
            employee.get(
                "department"
            )
        ).strip()

        if department:
            departments.add(
                department
            )

    kpi4.metric(
        "Τμήματα",
        len(
            departments
        ),
    )

    kpi5.metric(
        "Active Employee Rate",
        f"{active_employee_rate}%",
    )


    st.markdown(
        "---"
    )


    # --------------------------------------------------------
    # RECRUITMENT KPIS
    # --------------------------------------------------------

    st.subheader(
        "📋 Recruitment"
    )


    recruitment_statuses = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
        "Απορρίφθηκε",
    ]


    recruitment_counts = {

        status: sum(
            1
            for candidate
            in candidates
            if candidate.get(
                "status"
            )
            == status
        )

        for status
        in recruitment_statuses
    }


    hired_count = recruitment_counts.get(
        "Προσλήφθηκε",
        0,
    )


    total_candidates = len(
        candidates
    )


    hire_rate = (

        round(
            hired_count
            / total_candidates
            * 100
        )

        if total_candidates
        else 0
    )


    rec1, rec2, rec3, rec4 = st.columns(
        4
    )


    rec1.metric(
        "Υποψήφιοι",
        total_candidates,
    )


    rec2.metric(
        "Συνεντεύξεις",
        recruitment_counts.get(
            "Συνέντευξη",
            0,
        ),
    )


    rec3.metric(
        "Προσλήψεις",
        hired_count,
    )


    rec4.metric(
        "Hire Rate",
        f"{hire_rate}%",
    )


    recruitment_df = pd.DataFrame(
        {
            "Status":
                list(
                    recruitment_counts.keys()
                ),

            "Υποψήφιοι":
                list(
                    recruitment_counts.values()
                ),
        }
    )


    if not recruitment_df.empty:

        recruitment_df = (
            recruitment_df.set_index(
                "Status"
            )
        )

        st.bar_chart(
            recruitment_df
        )


    st.markdown(
        "---"
    )


    # --------------------------------------------------------
    # ONBOARDING KPIS
    # --------------------------------------------------------

    st.subheader(
        "🚀 Onboarding"
    )


    onboarding_not_started = 0

    onboarding_in_progress = 0

    onboarding_completed = 0

    overdue_onboarding = 0

    total_progress = 0


    for row in onboarding_rows:

        completed, progress_percent = (
            onboarding_progress(
                row
            )
        )

        total_progress += (
            progress_percent
        )


        onboarding_status = (
            onboarding_status_from_row(
                row
            )
        )


        if onboarding_status == "Δεν ξεκίνησε":

            onboarding_not_started += 1


        elif onboarding_status == "Σε εξέλιξη":

            onboarding_in_progress += 1


        elif onboarding_status == "Ολοκληρώθηκε":

            onboarding_completed += 1


        deadline_value = row.get(
            "deadline"
        )


        if (
            deadline_value
            and onboarding_status
            != "Ολοκληρώθηκε"
        ):

            deadline_date = parse_date(
                deadline_value
            )

            if deadline_date < date.today():

                overdue_onboarding += 1


    average_onboarding_progress = (

        round(
            total_progress
            / len(
                onboarding_rows
            )
        )

        if onboarding_rows
        else 0
    )

    onboarding_completion_rate = (
    round(
        onboarding_completed / len(onboarding_rows) * 100
    )
    if onboarding_rows
    else 0
)


    onb1, onb2, onb3, onb4, onb5,onb6 = (
        st.columns(
            6
        )
    )


    onb1.metric(
        "Δεν ξεκίνησε",
        onboarding_not_started,
    )


    onb2.metric(
        "Σε εξέλιξη",
        onboarding_in_progress,
    )


    onb3.metric(
        "Ολοκληρώθηκαν",
        onboarding_completed,
    )


    onb4.metric(
        "Μέση πρόοδος",
        f"{average_onboarding_progress}%",
    )


    onb5.metric(
        "Εκπρόθεσμα",
        overdue_onboarding,
    )

    onb6.metric(
        "Ρυθμός ολοκλήρωσης",
        f"{onboarding_completion_rate}%",
    )


    if onboarding_rows:

        onboarding_chart = pd.DataFrame(
            {
                "Status": [
                    "Δεν ξεκίνησε",
                    "Σε εξέλιξη",
                    "Ολοκληρώθηκε",
                ],

                "Onboarding": [
                    onboarding_not_started,
                    onboarding_in_progress,
                    onboarding_completed,
                ],
            }
        ).set_index(
            "Status"
        )


        st.bar_chart(
            onboarding_chart
        )


    st.markdown(
        "---"
    )


    # --------------------------------------------------------
    # LEAVE KPIS
    # --------------------------------------------------------

    st.subheader(
        "🏖️ Άδειες"
    )


    pending_leaves = sum(
        1
        for leave
        in leaves
        if leave.get(
            "status"
        )
        == "Εκκρεμεί"
    )


    approved_leaves = sum(
        1
        for leave
        in leaves
        if leave.get(
            "status"
        )
        == "Εγκρίθηκε"
    )


    rejected_leaves = sum(
        1
        for leave
        in leaves
        if leave.get(
            "status"
        )
        == "Απορρίφθηκε"
    )


    leave1, leave2, leave3, leave4 = (
        st.columns(
            4
        )
    )


    leave1.metric(
        "Σύνολο αδειών",
        len(
            leaves
        ),
    )


    leave2.metric(
        "Εκκρεμείς",
        pending_leaves,
    )


    leave3.metric(
        "Εγκεκριμένες",
        approved_leaves,
    )


    leave4.metric(
        "Απορριφθείσες",
        rejected_leaves,
    )


    st.markdown(
        "---"
    )


    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    st.subheader(
        "🔔 HR Alerts"
    )


    alerts_found = False


    if overdue_onboarding > 0:

        st.error(
            f"⚠️ Υπάρχουν {overdue_onboarding} εκπρόθεσμα Onboarding."
        )

        alerts_found = True


    if pending_leaves > 0:

        st.warning(
            f"🏖️ Υπάρχουν {pending_leaves} αιτήματα άδειας σε αναμονή."
        )

        alerts_found = True


    interview_candidates = [

        candidate
        for candidate
        in candidates
        if candidate.get(
            "status"
        )
        == "Συνέντευξη"

    ]


    if interview_candidates:

        st.info(
            f"📅 {len(interview_candidates)} υποψήφιοι βρίσκονται στο στάδιο Συνέντευξη."
        )

        alerts_found = True


    if not alerts_found:

        st.success(
            "✅ Δεν υπάρχουν σημαντικές εκκρεμότητες αυτή τη στιγμή."
        )


    st.markdown(
        "---"
    )


    # --------------------------------------------------------
    # DEPARTMENTS
    # --------------------------------------------------------


    # --------------------------------------------------------
# HIRES PER MONTH
# --------------------------------------------------------

st.subheader(
    "📅 Προσλήψεις ανά μήνα"
)

hires_per_month = {}

for employee in employees:

    hire_date_value = employee.get(
        "hire_date"
    )

    if hire_date_value:

        hire_date_obj = parse_date(
            hire_date_value
        )

        month_key = hire_date_obj.strftime(
            "%Y-%m"
        )

        hires_per_month[
            month_key
        ] = (
            hires_per_month.get(
                month_key,
                0,
            )
            + 1
        )


if hires_per_month:

    hires_df = pd.DataFrame(
        {
            "Μήνας": list(
                hires_per_month.keys()
            ),

            "Προσλήψεις": list(
                hires_per_month.values()
            ),
        }
    )

    hires_df = hires_df.sort_values(
        "Μήνας"
    )

    hires_df = hires_df.set_index(
        "Μήνας"
    )

    st.bar_chart(
        hires_df
    )

else:

    st.info(
        "Δεν υπάρχουν δεδομένα προσλήψεων."
    )


st.markdown(
    "---"
)

st.subheader(
    "🏢 Εργαζόμενοι ανά τμήμα"
)


department_counts = {}


for employee in employees:

    department = (
        safe_text(
            employee.get(
                "department"
            )
        ).strip()
        or "Χωρίς τμήμα"
    )


    department_counts[
        department
    ] = (
        department_counts.get(
            department,
            0,
        )
        + 1
    )


if department_counts:

    department_df = pd.DataFrame(
        {
            "Τμήμα":
                list(
                    department_counts.keys()
                ),

            "Εργαζόμενοι":
                list(
                    department_counts.values()
                ),
        }
    ).set_index(
        "Τμήμα"
    )

    st.bar_chart(
        department_df
    )

else:

    st.info(
        "Δεν υπάρχουν δεδομένα εργαζομένων."
    )


    # --------------------------------------------------------
# LEAVES PER MONTH
# --------------------------------------------------------

st.subheader(
    "🏖️ Άδειες ανά μήνα"
)

leaves_per_month = {}

for leave in leaves:

    start_date_value = leave.get(
        "start_date"
    )

    if start_date_value:

        leave_date_obj = parse_date(
            start_date_value
        )

        month_key = leave_date_obj.strftime(
            "%Y-%m"
        )

        leaves_per_month[
            month_key
        ] = (
            leaves_per_month.get(
                month_key,
                0,
            )
            + 1
        )


if leaves_per_month:

    leaves_month_df = pd.DataFrame(
        {
            "Μήνας": list(
                leaves_per_month.keys()
            ),
            "Άδειες": list(
                leaves_per_month.values()
            ),
        }
    )

    leaves_month_df = leaves_month_df.sort_values(
        "Μήνας"
    )

    leaves_month_df = leaves_month_df.set_index(
        "Μήνας"
    )

    st.bar_chart(
        leaves_month_df
    )

else:

    st.info(
        "Δεν υπάρχουν δεδομένα αδειών."
    )


st.markdown(
    "---"
)


# ============================================================
# EMPLOYEES
# ============================================================

if page == "👥 Εργαζόμενοι":

    st.title(
        "👥 Εργαζόμενοι"
    )

    st.caption(
        "Διαχείριση εργαζομένων."
    )


    with st.expander(
        "➕ Νέος εργαζόμενος"
    ):

        with st.form(
            "add_employee_form",
            clear_on_submit=True,
        ):

            col1, col2 = st.columns(
                2
            )


            first_name = col1.text_input(
                "Όνομα *"
            )


            last_name = col2.text_input(
                "Επώνυμο *"
            )


            col3, col4 = st.columns(
                2
            )


            email = col3.text_input(
                "Email"
            )


            phone = col4.text_input(
                "Τηλέφωνο"
            )


            col5, col6 = st.columns(
                2
            )


            position = col5.text_input(
                "Θέση"
            )


            department = col6.text_input(
                "Τμήμα"
            )


            col7, col8 = st.columns(
                2
            )


            hire_date = col7.date_input(
                "Ημερομηνία πρόσληψης",
                value=date.today(),
                format="DD/MM/YYYY",
            )


            status = col8.selectbox(
                "Κατάσταση",
                [
                    "Ενεργός",
                    "Ανενεργός",
                ],
            )


            save = st.form_submit_button(
                "💾 Αποθήκευση",
                type="primary",
            )


            if save:

                if (
                    not first_name.strip()
                    or not last_name.strip()
                ):

                    st.error(
                        "Συμπλήρωσε Όνομα και Επώνυμο."
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
                            hire_date.strftime(
                                "%Y-%m-%d"
                            ),
                            status,
                        )


                        st.success(
                            "✅ Ο εργαζόμενος προστέθηκε."
                        )

                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Σφάλμα: {exc}"
                        )


    employees = get_employees()


    if not employees:

        st.info(
            "Δεν υπάρχουν εργαζόμενοι."
        )

    else:

        search = st.text_input(
            "🔎 Αναζήτηση"
        )


        filtered = employees


        if search.strip():

            term = (
                search.lower().strip()
            )


            filtered = [

                employee
                for employee
                in employees

                if term in (

                    f"{safe_text(employee.get('first_name'))} "
                    f"{safe_text(employee.get('last_name'))} "
                    f"{safe_text(employee.get('email'))} "
                    f"{safe_text(employee.get('position'))} "
                    f"{safe_text(employee.get('department'))}"

                ).lower()

            ]


        employee_df = pd.DataFrame(

            [
                {
                    "ID":
                        employee.get(
                            "id"
                        ),

                    "Όνομα":
                        employee.get(
                            "first_name"
                        ),

                    "Επώνυμο":
                        employee.get(
                            "last_name"
                        ),

                    "Email":
                        employee.get(
                            "email"
                        ),

                    "Τηλέφωνο":
                        employee.get(
                            "phone"
                        ),

                    "Θέση":
                        employee.get(
                            "position"
                        ),

                    "Τμήμα":
                        employee.get(
                            "department"
                        ),

                    "Πρόσληψη":
                        format_date(
                            employee.get(
                                "hire_date"
                            )
                        ),

                    "Κατάσταση":
                        employee.get(
                            "status"
                        ),
                }

                for employee
                in filtered
            ]
        )


        st.dataframe(
            employee_df,
            use_container_width=True,
            hide_index=True,
        )


        st.markdown(
            "---"
        )


        st.subheader(
            "✏️ Επεξεργασία εργαζομένου"
        )


        employee_options = {

            (
                f"{employee['first_name']} "
                f"{employee['last_name']} "
                f"— ID {employee['id']}"
            ): employee

            for employee
            in employees
        }


        selected_employee_label = (
            st.selectbox(
                "Εργαζόμενος",
                list(
                    employee_options.keys()
                ),
            )
        )


        selected_employee = (
            employee_options[
                selected_employee_label
            ]
        )


        with st.form(
            f"edit_employee_{selected_employee['id']}"
        ):

            col1, col2 = st.columns(
                2
            )


            edit_first_name = col1.text_input(
                "Όνομα",
                value=safe_text(
                    selected_employee.get(
                        "first_name"
                    )
                ),
            )


            edit_last_name = col2.text_input(
                "Επώνυμο",
                value=safe_text(
                    selected_employee.get(
                        "last_name"
                    )
                ),
            )


            col3, col4 = st.columns(
                2
            )


            edit_email = col3.text_input(
                "Email",
                value=safe_text(
                    selected_employee.get(
                        "email"
                    )
                ),
            )


            edit_phone = col4.text_input(
                "Τηλέφωνο",
                value=safe_text(
                    selected_employee.get(
                        "phone"
                    )
                ),
            )


            col5, col6 = st.columns(
                2
            )


            edit_position = col5.text_input(
                "Θέση",
                value=safe_text(
                    selected_employee.get(
                        "position"
                    )
                ),
            )


            edit_department = col6.text_input(
                "Τμήμα",
                value=safe_text(
                    selected_employee.get(
                        "department"
                    )
                ),
            )


            col7, col8 = st.columns(
                2
            )


            edit_hire_date = col7.date_input(
                "Ημερομηνία πρόσληψης",
                value=parse_date(
                    selected_employee.get(
                        "hire_date"
                    )
                ),
                format="DD/MM/YYYY",
            )


            status_options = [
                "Ενεργός",
                "Ανενεργός",
            ]


            current_status = (
                selected_employee.get(
                    "status"
                )
                or "Ενεργός"
            )


            edit_status = col8.selectbox(

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


            save_changes = (
                st.form_submit_button(
                    "💾 Αποθήκευση αλλαγών",
                    type="primary",
                )
            )


            if save_changes:

                try:

                    update_employee(
                        selected_employee[
                            "id"
                        ],
                        edit_first_name.strip(),
                        edit_last_name.strip(),
                        edit_email.strip() or None,
                        edit_phone.strip() or None,
                        edit_position.strip() or None,
                        edit_department.strip() or None,
                        edit_hire_date.strftime(
                            "%Y-%m-%d"
                        ),
                        edit_status,
                    )


                    st.success(
                        "✅ Αποθηκεύτηκαν οι αλλαγές."
                    )

                    st.rerun()


                except Exception as exc:

                    st.error(
                        f"Σφάλμα: {exc}"
                    )


        if st.button(
            "🗑️ Διαγραφή εργαζομένου",
            key=f"delete_employee_{selected_employee['id']}",
        ):

            try:

                delete_employee(
                    selected_employee[
                        "id"
                    ]
                )

                st.success(
                    "✅ Ο εργαζόμενος διαγράφηκε."
                )

                st.rerun()


            except Exception as exc:

                st.error(
                    f"Σφάλμα: {exc}"
                )


# ============================================================
# RECRUITMENT
# ============================================================

elif page == "📋 Recruitment":

    st.title(
        "📋 Recruitment"
    )

    st.caption(
        "Διαχείριση υποψηφίων και διαδικασίας πρόσληψης."
    )


    recruitment_statuses = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
        "Απορρίφθηκε",
    ]


    with st.expander(
        "➕ Νέος υποψήφιος"
    ):

        with st.form(
            "candidate_form",
            clear_on_submit=True,
        ):

            c1, c2 = st.columns(
                2
            )


            first_name = c1.text_input(
                "Όνομα *"
            )


            last_name = c2.text_input(
                "Επώνυμο *"
            )


            c3, c4 = st.columns(
                2
            )


            email = c3.text_input(
                "Email"
            )


            phone = c4.text_input(
                "Τηλέφωνο"
            )


            c5, c6 = st.columns(
                2
            )


            position = c5.text_input(
                "Θέση"
            )


            application_date = c6.date_input(
                "Ημερομηνία αίτησης",
                value=date.today(),
                format="DD/MM/YYYY",
            )


            status = st.selectbox(
                "Κατάσταση",
                recruitment_statuses,
            )


            recruiter = st.text_input(
                "Recruiter",
                value=safe_text(
                    user_name
                ),
            )


            notes = st.text_area(
                "Σημειώσεις"
            )


            submitted = (
                st.form_submit_button(
                    "💾 Προσθήκη υποψηφίου",
                    type="primary",
                )
            )


            if submitted:

                if (
                    not first_name.strip()
                    or not last_name.strip()
                ):

                    st.error(
                        "Συμπλήρωσε Όνομα και Επώνυμο."
                    )

                else:

                    add_candidate(
                        first_name.strip(),
                        last_name.strip(),
                        email.strip() or None,
                        phone.strip() or None,
                        position.strip() or None,
                        application_date.strftime(
                            "%Y-%m-%d"
                        ),
                        status,
                        None,
                        None,
                        notes.strip() or None,
                        recruiter.strip() or None,
                    )

                    st.success(
                        "✅ Ο υποψήφιος προστέθηκε."
                    )

                    st.rerun()


    candidates = get_candidates()


    if not candidates:

        st.info(
            "Δεν υπάρχουν υποψήφιοι."
        )

    else:

        pipeline_columns = st.columns(
            len(
                recruitment_statuses
            )
        )


        for index, status_name in enumerate(
            recruitment_statuses
        ):

            count = sum(

                1
                for candidate
                in candidates

                if candidate.get(
                    "status"
                )
                == status_name

            )


            pipeline_columns[
                index
            ].metric(
                status_name,
                count,
            )


        st.markdown(
            "---"
        )


        candidate_options = {

            (
                f"{candidate['first_name']} "
                f"{candidate['last_name']} "
                f"— {candidate.get('position') or 'Χωρίς θέση'} "
                f"— ID {candidate['id']}"
            ): candidate

            for candidate
            in candidates
        }


        selected_candidate_label = (
            st.selectbox(
                "Υποψήφιος",
                list(
                    candidate_options.keys()
                ),
            )
        )


        selected_candidate = (
            candidate_options[
                selected_candidate_label
            ]
        )


        current_status = (
            selected_candidate.get(
                "status"
            )
            or "Νέα αίτηση"
        )


        status_index = (

            recruitment_statuses.index(
                current_status
            )

            if current_status
            in recruitment_statuses

            else 0
        )


        with st.form(
            f"candidate_{selected_candidate['id']}"
        ):

            new_status = st.selectbox(
                "Κατάσταση",
                recruitment_statuses,
                index=status_index,
            )


            interview_enabled = st.checkbox(

                "Έχει οριστεί συνέντευξη",

                value=bool(
                    selected_candidate.get(
                        "interview_date"
                    )
                ),
            )


            interview_date = st.date_input(

                "Ημερομηνία συνέντευξης",

                value=parse_date(
                    selected_candidate.get(
                        "interview_date"
                    )
                ),

                format="DD/MM/YYYY",

                disabled=not interview_enabled,
            )


            rating_value = (
                selected_candidate.get(
                    "rating"
                )
            )


            rating = st.slider(

                "Αξιολόγηση",

                min_value=0,

                max_value=5,

                value=(
                    int(
                        rating_value
                    )
                    if rating_value
                    is not None
                    else 0
                ),
            )


            recruiter = st.text_input(

                "Recruiter",

                value=safe_text(
                    selected_candidate.get(
                        "recruiter"
                    )
                    or user_name
                ),
            )


            notes = st.text_area(

                "Σημειώσεις",

                value=safe_text(
                    selected_candidate.get(
                        "notes"
                    )
                ),
            )


            save_candidate = (
                st.form_submit_button(
                    "💾 Αποθήκευση",
                    type="primary",
                )
            )


            if save_candidate:

                update_candidate(

                    selected_candidate[
                        "id"
                    ],

                    new_status,

                    changed_by=safe_text(
                        user_email
                    ),

                    interview_date=(
                        interview_date.strftime(
                            "%Y-%m-%d"
                        )
                        if interview_enabled
                        else None
                    ),

                    rating=(
                        rating
                        if rating > 0
                        else None
                    ),

                    notes=(
                        notes.strip()
                        or None
                    ),

                    recruiter=(
                        recruiter.strip()
                        or None
                    ),
                )


                st.success(
                    "✅ Ο υποψήφιος ενημερώθηκε."
                )

                st.rerun()


        if (
            selected_candidate.get(
                "status"
            )
            == "Προσλήφθηκε"
        ):

            st.success(
                "✅ Ο υποψήφιος έχει προσληφθεί."
            )


            if st.button(
                "👥 Δημιουργία εργαζομένου + Onboarding",
                key=f"hire_{selected_candidate['id']}",
                type="primary",
            ):

                try:

                    employee_id = (
                        create_employee_from_candidate(
                            selected_candidate[
                                "id"
                            ]
                        )
                    )


                    existing_onboarding = [

                        row
                        for row
                        in get_onboarding()

                        if row.get(
                            "employee_id"
                        )
                        == employee_id

                    ]


                    if existing_onboarding:

                        st.warning(
                            "Ο εργαζόμενος υπάρχει ήδη και έχει ήδη Onboarding."
                        )

                    else:

                        create_onboarding(

                            employee_id,

                            date.today().strftime(
                                "%Y-%m-%d"
                            ),

                            safe_text(
                                user_name
                            ).strip()
                            or None,

                            (
                                date.today()
                                + timedelta(
                                    days=14
                                )
                            ).strftime(
                                "%Y-%m-%d"
                            ),
                        )


                        st.success(
                            "✅ Δημιουργήθηκε εργαζόμενος και Onboarding."
                        )


                    st.rerun()


                except Exception as exc:

                    st.error(
                        f"Σφάλμα: {exc}"
                    )


        with st.expander(
            "🕘 Ιστορικό υποψηφίου"
        ):

            history = get_candidate_history(
                selected_candidate[
                    "id"
                ]
            )


            if history:

                history_df = pd.DataFrame(

                    [
                        {
                            "Από":
                                row.get(
                                    "old_status"
                                )
                                or "-",

                            "Σε":
                                row.get(
                                    "new_status"
                                ),

                            "Χρήστης":
                                row.get(
                                    "changed_by"
                                )
                                or "-",

                            "Ημερομηνία":
                                safe_text(
                                    row.get(
                                        "changed_at"
                                    )
                                ),
                        }

                        for row
                        in history
                    ]
                )


                st.dataframe(
                    history_df,
                    hide_index=True,
                    use_container_width=True,
                )

            else:

                st.info(
                    "Δεν υπάρχει ιστορικό."
                )


# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    st.title(
        "🚀 Employee Onboarding"
    )

    st.caption(
        "Checklist για την ένταξη νέων εργαζομένων."
    )


    employees = get_employees()

    onboarding_rows = get_onboarding()


    st.subheader(
        "➕ Νέο Onboarding"
    )


    if not employees:

        st.info(
            "Δεν υπάρχουν εργαζόμενοι."
        )

    else:

        employee_options = {

            (
                f"{employee['first_name']} "
                f"{employee['last_name']} "
                f"— ID {employee['id']}"
            ): employee

            for employee
            in employees
        }


        with st.form(
            "new_onboarding"
        ):

            selected_label = st.selectbox(
                "Εργαζόμενος",
                list(
                    employee_options.keys()
                ),
            )


            selected_employee = (
                employee_options[
                    selected_label
                ]
            )


            col1, col2 = st.columns(
                2
            )


            start_date = col1.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY",
            )


            deadline = col2.date_input(
                "📅 Deadline",
                value=(
                    date.today()
                    + timedelta(
                        days=14
                    )
                ),
                format="DD/MM/YYYY",
            )


            responsible = st.text_input(
                "👤 Υπεύθυνος Onboarding",
                value=safe_text(
                    user_name
                ),
            )


            create_button = (
                st.form_submit_button(
                    "🚀 Δημιουργία Onboarding",
                    type="primary",
                )
            )


            if create_button:

                existing = [

                    row
                    for row
                    in onboarding_rows

                    if row.get(
                        "employee_id"
                    )
                    == selected_employee[
                        "id"
                    ]

                ]


                if existing:

                    st.warning(
                        "Υπάρχει ήδη Onboarding για αυτόν τον εργαζόμενο."
                    )

                else:

                    create_onboarding(

                        selected_employee[
                            "id"
                        ],

                        start_date.strftime(
                            "%Y-%m-%d"
                        ),

                        responsible.strip()
                        or None,

                        deadline.strftime(
                            "%Y-%m-%d"
                        ),
                    )


                    st.success(
                        "✅ Δημιουργήθηκε το Onboarding."
                    )

                    st.rerun()


    st.markdown(
        "---"
    )


    st.subheader(
        "📋 Onboarding Checklist"
    )


    onboarding_rows = get_onboarding()


    if not onboarding_rows:

        st.info(
            "Δεν υπάρχουν Onboarding."
        )

    else:

        for row in onboarding_rows:

            employee_name = (
                f"{safe_text(row.get('first_name'))} "
                f"{safe_text(row.get('last_name'))}"
            ).strip()


            completed, progress_percent = (
                onboarding_progress(
                    row
                )
            )


            onboarding_status = (
                onboarding_status_from_row(
                    row
                )
            )


            with st.expander(

                f"👤 {employee_name} "
                f"— {progress_percent}% "
                f"— {onboarding_status}"

            ):

                m1, m2, m3, m4 = st.columns(
                    4
                )


                m1.metric(
                    "📊 Progress",
                    f"{progress_percent}%",
                )


                m2.metric(
                    "✅ Tasks",
                    f"{completed}/7",
                )


                m3.metric(
                    "🔄 Status",
                    onboarding_status,
                )


                m4.metric(
                    "📅 Deadline",
                    format_date(
                        row.get(
                            "deadline"
                        )
                    ),
                )


                st.progress(
                    completed / 7
                )


                deadline_value = row.get(
                    "deadline"
                )


                if (
                    deadline_value
                    and onboarding_status
                    != "Ολοκληρώθηκε"
                ):

                    deadline_date = (
                        parse_date(
                            deadline_value
                        )
                    )


                    if (
                        deadline_date
                        < date.today()
                    ):

                        st.error(
                            "⚠️ Εκπρόθεσμο Onboarding"
                        )


                with st.form(
                    f"onboarding_{row['id']}"
                ):

                    col1, col2 = st.columns(
                        2
                    )


                    responsible = col1.text_input(

                        "👤 Υπεύθυνος Onboarding",

                        value=safe_text(
                            row.get(
                                "responsible"
                            )
                        ),
                    )


                    deadline = col2.date_input(

                        "📅 Deadline",

                        value=parse_date(

                            row.get(
                                "deadline"
                            ),

                            date.today()
                            + timedelta(
                                days=14
                            ),
                        ),

                        format="DD/MM/YYYY",
                    )


                    st.caption(
                        "Ημερομηνία έναρξης: "
                        f"{format_date(row.get('start_date'))}"
                    )


                    c1, c2 = st.columns(
                        2
                    )


                    contract = c1.checkbox(
                        "📄 Σύμβαση",
                        value=bool(
                            row.get(
                                "contract"
                            )
                        ),
                    )


                    documents = c2.checkbox(
                        "🪪 Έγγραφα εργαζομένου",
                        value=bool(
                            row.get(
                                "documents"
                            )
                        ),
                    )


                    c3, c4 = st.columns(
                        2
                    )


                    company_email = c3.checkbox(
                        "📧 Εταιρικό email",
                        value=bool(
                            row.get(
                                "email"
                            )
                        ),
                    )


                    equipment = c4.checkbox(
                        "💻 Εξοπλισμός",
                        value=bool(
                            row.get(
                                "equipment"
                            )
                        ),
                    )


                    c5, c6 = st.columns(
                        2
                    )


                    system_access = c5.checkbox(
                        "🔐 Πρόσβαση στα συστήματα",
                        value=bool(
                            row.get(
                                "system_access"
                            )
                        ),
                    )


                    training = c6.checkbox(
                        "🎓 Εκπαίδευση",
                        value=bool(
                            row.get(
                                "training"
                            )
                        ),
                    )


                    manager_meeting = (
                        st.checkbox(
                            "🤝 Συνάντηση με Manager",
                            value=bool(
                                row.get(
                                    "manager_meeting"
                                )
                            ),
                        )
                    )


                    save_onboarding = (
                        st.form_submit_button(
                            "💾 Αποθήκευση Onboarding",
                            type="primary",
                        )
                    )


                    if save_onboarding:

                        update_onboarding(

                            row[
                                "id"
                            ],

                            int(
                                contract
                            ),

                            int(
                                documents
                            ),

                            int(
                                company_email
                            ),

                            int(
                                equipment
                            ),

                            int(
                                system_access
                            ),

                            int(
                                training
                            ),

                            int(
                                manager_meeting
                            ),

                            responsible.strip()
                            or None,

                            deadline.strftime(
                                "%Y-%m-%d"
                            ),
                        )


                        st.success(
                            "✅ Το Onboarding ενημερώθηκε."
                        )

                        st.rerun()


# ============================================================
# LEAVES - HR
# ============================================================

elif (
    page == "🏖️ Άδειες"
    and user_role
    in (
        "Admin",
        "HR",
    )
):

    st.title(
        "🏖️ Άδειες"
    )


    employees = get_employees()


    if employees:

        employee_options = {

            (
                f"{employee['first_name']} "
                f"{employee['last_name']}"
            ): employee

            for employee
            in employees
        }


        with st.expander(
            "➕ Νέα άδεια"
        ):

            with st.form(
                "leave_form"
            ):

                selected_label = st.selectbox(
                    "Εργαζόμενος",
                    list(
                        employee_options.keys()
                    ),
                )


                selected_employee = (
                    employee_options[
                        selected_label
                    ]
                )


                leave_type = st.selectbox(
                    "Τύπος άδειας",
                    [
                        "Κανονική",
                        "Αναρρωτική",
                        "Άδεια άνευ αποδοχών",
                        "Άλλη",
                    ],
                )


                c1, c2 = st.columns(
                    2
                )


                start_date = c1.date_input(
                    "Από",
                    format="DD/MM/YYYY",
                )


                end_date = c2.date_input(
                    "Έως",
                    format="DD/MM/YYYY",
                )


                reason = st.text_area(
                    "Αιτιολογία"
                )


                submit = (
                    st.form_submit_button(
                        "💾 Καταχώρηση",
                        type="primary",
                    )
                )


                if submit:

                    if end_date < start_date:

                        st.error(
                            "Λάθος ημερομηνίες."
                        )

                    else:

                        add_leave(

                            selected_employee[
                                "id"
                            ],

                            leave_type,

                            start_date.strftime(
                                "%Y-%m-%d"
                            ),

                            end_date.strftime(
                                "%Y-%m-%d"
                            ),

                            reason.strip()
                            or None,

                            "Εκκρεμεί",
                        )


                        st.success(
                            "✅ Καταχωρήθηκε."
                        )

                        st.rerun()


    leaves = get_leaves()


    for leave in leaves:

        employee_name = (
            f"{leave.get('first_name')} "
            f"{leave.get('last_name')}"
        )


        with st.expander(
            f"{employee_name} "
            f"— {leave.get('leave_type')} "
            f"— {leave.get('status')}"
        ):

            st.write(
                f"**Από:** {format_date(leave.get('start_date'))}"
            )

            st.write(
                f"**Έως:** {format_date(leave.get('end_date'))}"
            )

            st.write(
                f"**Αιτιολογία:** {leave.get('reason') or '-'}"
            )


            statuses = [
                "Εκκρεμεί",
                "Εγκρίθηκε",
                "Απορρίφθηκε",
            ]


            current = leave.get(
                "status"
            )


            new_status = st.selectbox(

                "Κατάσταση",

                statuses,

                index=(
                    statuses.index(
                        current
                    )
                    if current
                    in statuses
                    else 0
                ),

                key=f"leave_status_{leave['id']}",
            )


            if st.button(
                "💾 Ενημέρωση",
                key=f"leave_{leave['id']}",
            ):

                update_leave_status(
                    leave[
                        "id"
                    ],
                    new_status,
                )

                st.success(
                    "✅ Ενημερώθηκε."
                )

                st.rerun()


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
            "Δεν βρέθηκε εργαζόμενος με αυτό το email."
        )

    else:

        c1, c2, c3 = st.columns(
            3
        )


        c1.metric(

            "Ονοματεπώνυμο",

            f"{employee.get('first_name')} "
            f"{employee.get('last_name')}",
        )


        c2.metric(
            "Θέση",
            employee.get(
                "position"
            )
            or "-",
        )


        c3.metric(
            "Τμήμα",
            employee.get(
                "department"
            )
            or "-",
        )


        st.write(
            f"**Email:** {employee.get('email') or '-'}"
        )

        st.write(
            f"**Τηλέφωνο:** {employee.get('phone') or '-'}"
        )

        st.write(
            f"**Ημερομηνία πρόσληψης:** "
            f"{format_date(employee.get('hire_date'))}"
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
            "Δεν βρέθηκε ο εργαζόμενος."
        )

    else:

        with st.expander(
            "➕ Νέο αίτημα άδειας"
        ):

            with st.form(
                "my_leave"
            ):

                leave_type = st.selectbox(
                    "Τύπος άδειας",
                    [
                        "Κανονική",
                        "Αναρρωτική",
                        "Άδεια άνευ αποδοχών",
                        "Άλλη",
                    ],
                )


                c1, c2 = st.columns(
                    2
                )


                start_date = c1.date_input(
                    "Από",
                    format="DD/MM/YYYY",
                )


                end_date = c2.date_input(
                    "Έως",
                    format="DD/MM/YYYY",
                )


                reason = st.text_area(
                    "Αιτιολογία"
                )


                submit = (
                    st.form_submit_button(
                        "📨 Υποβολή",
                        type="primary",
                    )
                )


                if submit:

                    if end_date < start_date:

                        st.error(
                            "Λάθος ημερομηνίες."
                        )

                    else:

                        add_leave(

                            employee[
                                "id"
                            ],

                            leave_type,

                            start_date.strftime(
                                "%Y-%m-%d"
                            ),

                            end_date.strftime(
                                "%Y-%m-%d"
                            ),

                            reason.strip()
                            or None,

                            "Εκκρεμεί",
                        )


                        st.success(
                            "✅ Το αίτημα υποβλήθηκε."
                        )

                        st.rerun()


        my_leaves = [

            leave
            for leave
            in get_leaves()

            if leave.get(
                "employee_id"
            )
            == employee[
                "id"
            ]

        ]


        if my_leaves:

            leave_df = pd.DataFrame(

                [
                    {
                        "Τύπος":
                            leave.get(
                                "leave_type"
                            ),

                        "Από":
                            format_date(
                                leave.get(
                                    "start_date"
                                )
                            ),

                        "Έως":
                            format_date(
                                leave.get(
                                    "end_date"
                                )
                            ),

                        "Κατάσταση":
                            leave.get(
                                "status"
                            ),
                    }

                    for leave
                    in my_leaves
                ]
            )


            st.dataframe(
                leave_df,
                hide_index=True,
                use_container_width=True,
            )

        else:

            st.info(
                "Δεν υπάρχουν αιτήματα άδειας."
            )


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title(
        "🤖 AI Assistant"
    )

    st.caption(
        "HR AI Assistant χωρίς πληρωμένο OpenAI API."
    )


    question = st.text_area(
        "Γράψε μια HR ερώτηση"
    )


    if st.button(
        "Αποστολή"
    ):

        if not question.strip():

            st.warning(
                "Γράψε πρώτα μια ερώτηση."
            )

        else:

            st.info(
                "Το AI module θα συνδεθεί αργότερα με local/free AI model."
            )