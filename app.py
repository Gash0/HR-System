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
    return "" if value is None else str(value)


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


def get_role(user_email):
    email = safe_text(user_email).strip().lower()

    try:
        roles = st.secrets.get("roles", {})
        admin_emails = [
            str(item).lower()
            for item in roles.get("admin_emails", [])
        ]
        hr_emails = [
            str(item).lower()
            for item in roles.get("hr_emails", [])
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
        int(bool(row.get(key)))
        for key in task_keys
    )

    progress_percent = round(
        (completed / 7) * 100
    )

    return completed, progress_percent


def onboarding_status_from_row(row):
    completed, _ = onboarding_progress(row)

    if completed == 7:
        return "Ολοκληρώθηκε"

    if completed > 0:
        return "Σε εξέλιξη"

    return "Δεν ξεκίνησε"


# ============================================================
# LOGIN
# ============================================================

if not st.user.is_logged_in:

    st.title("👥 AI HR System")

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
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.title(
        "📊 Dashboard"
    )

    st.caption(
        "Κεντρική εικόνα του Ανθρώπινου Δυναμικού."
    )


    stats = get_hr_statistics()


    col1, col2, col3, col4 = st.columns(
        4
    )


    col1.metric(
        "Εργαζόμενοι",
        stats.get(
            "total_employees",
            0,
        ),
    )


    col2.metric(
        "Ενεργοί",
        stats.get(
            "active_employees",
            0,
        ),
    )


    col3.metric(
        "Υποψήφιοι",
        stats.get(
            "total_candidates",
            0,
        ),
    )


    col4.metric(
        "Άδειες σε αναμονή",
        stats.get(
            "pending_leaves",
            0,
        ),
    )


    st.markdown(
        "---"
    )


    employees = get_employees()


    if employees:

        departments = {}

        for employee in employees:

            department = (
                safe_text(
                    employee.get(
                        "department"
                    )
                ).strip()
                or "Χωρίς τμήμα"
            )

            departments[
                department
            ] = (
                departments.get(
                    department,
                    0,
                )
                + 1
            )


        st.subheader(
            "👥 Εργαζόμενοι ανά τμήμα"
        )


        department_df = pd.DataFrame(
            [
                {
                    "Τμήμα": key,
                    "Εργαζόμενοι": value,
                }
                for key, value
                in departments.items()
            ]
        ).set_index(
            "Τμήμα"
        )


        st.bar_chart(
            department_df
        )


    st.subheader(
        "📌 Σύνοψη"
    )


    summary_df = pd.DataFrame(
        [
            {
                "Δείκτης":
                    "Ενεργοί εργαζόμενοι",

                "Τιμή":
                    stats.get(
                        "active_employees",
                        0,
                    ),
            },

            {
                "Δείκτης":
                    "Ανενεργοί εργαζόμενοι",

                "Τιμή":
                    stats.get(
                        "inactive_employees",
                        0,
                    ),
            },

            {
                "Δείκτης":
                    "Προσληφθέντες υποψήφιοι",

                "Τιμή":
                    stats.get(
                        "hired_candidates",
                        0,
                    ),
            },

            {
                "Δείκτης":
                    "Σύνολο αδειών",

                "Τιμή":
                    stats.get(
                        "total_leaves",
                        0,
                    ),
            },
        ]
    )


    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# EMPLOYEES
# ============================================================

elif page == "👥 Εργαζόμενοι":

    st.title(
        "👥 Εργαζόμενοι"
    )

    st.caption(
        "Διαχείριση εργαζομένων."
    )


    with st.expander(
        "➕ Νέος εργαζόμενος",
        expanded=False,
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


            submitted = (
                st.form_submit_button(
                    "💾 Αποθήκευση εργαζομένου",
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

                    try:

                        add_employee(
                            first_name.strip(),
                            last_name.strip(),
                            email.strip()
                            or None,
                            phone.strip()
                            or None,
                            position.strip()
                            or None,
                            department.strip()
                            or None,
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
            "🔎 Αναζήτηση εργαζομένου"
        )


        filtered_employees = employees


        if search.strip():

            term = (
                search.strip().lower()
            )


            filtered_employees = [
                employee
                for employee
                in employees
                if term
                in (
                    f"{safe_text(employee.get('first_name'))} "
                    f"{safe_text(employee.get('last_name'))} "
                    f"{safe_text(employee.get('email'))} "
                    f"{safe_text(employee.get('position'))} "
                    f"{safe_text(employee.get('department'))}"
                ).lower()
            ]


        st.subheader(
            "📋 Λίστα εργαζομένων"
        )


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
                in filtered_employees
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
                "Επιλογή εργαζομένου",
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


            edit_first_name = (
                col1.text_input(
                    "Όνομα",
                    value=safe_text(
                        selected_employee.get(
                            "first_name"
                        )
                    ),
                )
            )


            edit_last_name = (
                col2.text_input(
                    "Επώνυμο",
                    value=safe_text(
                        selected_employee.get(
                            "last_name"
                        )
                    ),
                )
            )


            col3, col4 = st.columns(
                2
            )


            edit_email = (
                col3.text_input(
                    "Email",
                    value=safe_text(
                        selected_employee.get(
                            "email"
                        )
                    ),
                )
            )


            edit_phone = (
                col4.text_input(
                    "Τηλέφωνο",
                    value=safe_text(
                        selected_employee.get(
                            "phone"
                        )
                    ),
                )
            )


            col5, col6 = st.columns(
                2
            )


            edit_position = (
                col5.text_input(
                    "Θέση",
                    value=safe_text(
                        selected_employee.get(
                            "position"
                        )
                    ),
                )
            )


            edit_department = (
                col6.text_input(
                    "Τμήμα",
                    value=safe_text(
                        selected_employee.get(
                            "department"
                        )
                    ),
                )
            )


            col7, col8 = st.columns(
                2
            )


            edit_hire_date = (
                col7.date_input(
                    "Ημερομηνία πρόσληψης",

                    value=parse_date(
                        selected_employee.get(
                            "hire_date"
                        )
                    ),

                    format="DD/MM/YYYY",
                )
            )


            current_status = (
                selected_employee.get(
                    "status"
                )
                or "Ενεργός"
            )


            edit_status = (
                col8.selectbox(
                    "Κατάσταση",

                    [
                        "Ενεργός",
                        "Ανενεργός",
                    ],

                    index=(
                        0
                        if current_status
                        == "Ενεργός"
                        else 1
                    ),
                )
            )


            save_employee = (
                st.form_submit_button(
                    "💾 Αποθήκευση αλλαγών",
                    type="primary",
                )
            )


            if save_employee:

                try:

                    update_employee(
                        selected_employee[
                            "id"
                        ],

                        edit_first_name.strip(),

                        edit_last_name.strip(),

                        edit_email.strip()
                        or None,

                        edit_phone.strip()
                        or None,

                        edit_position.strip()
                        or None,

                        edit_department.strip()
                        or None,

                        edit_hire_date.strftime(
                            "%Y-%m-%d"
                        ),

                        edit_status,
                    )


                    st.success(
                        "✅ Οι αλλαγές αποθηκεύτηκαν."
                    )


                    st.rerun()


                except Exception as exc:

                    st.error(
                        f"Σφάλμα: {exc}"
                    )


        if st.button(
            "🗑️ Διαγραφή εργαζομένου",

            key=(
                f"delete_employee_"
                f"{selected_employee['id']}"
            ),
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
        "➕ Νέος υποψήφιος",
        expanded=False,
    ):

        with st.form(
            "add_candidate_form",
            clear_on_submit=True,
        ):

            col1, col2 = st.columns(
                2
            )


            candidate_first_name = (
                col1.text_input(
                    "Όνομα *"
                )
            )


            candidate_last_name = (
                col2.text_input(
                    "Επώνυμο *"
                )
            )


            col3, col4 = st.columns(
                2
            )


            candidate_email = (
                col3.text_input(
                    "Email"
                )
            )


            candidate_phone = (
                col4.text_input(
                    "Τηλέφωνο"
                )
            )


            col5, col6 = st.columns(
                2
            )


            candidate_position = (
                col5.text_input(
                    "Θέση"
                )
            )


            candidate_application_date = (
                col6.date_input(
                    "Ημερομηνία αίτησης",
                    value=date.today(),
                    format="DD/MM/YYYY",
                )
            )


            candidate_status = (
                st.selectbox(
                    "Κατάσταση",
                    recruitment_statuses,
                )
            )


            candidate_recruiter = (
                st.text_input(
                    "Recruiter",
                    value=safe_text(
                        user_name
                    ),
                )
            )


            candidate_notes = (
                st.text_area(
                    "Σημειώσεις"
                )
            )


            add_candidate_button = (
                st.form_submit_button(
                    "💾 Προσθήκη υποψηφίου",
                    type="primary",
                )
            )


            if add_candidate_button:

                if (
                    not candidate_first_name.strip()
                    or not candidate_last_name.strip()
                ):

                    st.error(
                        "Συμπλήρωσε Όνομα και Επώνυμο."
                    )

                else:

                    try:

                        add_candidate(
                            candidate_first_name.strip(),
                            candidate_last_name.strip(),
                            candidate_email.strip()
                            or None,
                            candidate_phone.strip()
                            or None,
                            candidate_position.strip()
                            or None,
                            candidate_application_date.strftime(
                                "%Y-%m-%d"
                            ),
                            candidate_status,
                            None,
                            None,
                            candidate_notes.strip()
                            or None,
                            candidate_recruiter.strip()
                            or None,
                        )


                        st.success(
                            "✅ Ο υποψήφιος προστέθηκε."
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Σφάλμα: {exc}"
                        )


    candidates = get_candidates()


    if not candidates:

        st.info(
            "Δεν υπάρχουν υποψήφιοι."
        )


    else:

        st.subheader(
            "📌 Pipeline"
        )


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


        st.subheader(
            "👤 Διαχείριση υποψηφίου"
        )


        candidate_options = {

            (
                f"{candidate['first_name']} "
                f"{candidate['last_name']} "
                f"— "
                f"{candidate.get('position') or 'Χωρίς θέση'} "
                f"— ID {candidate['id']}"
            ): candidate

            for candidate
            in candidates
        }


        selected_candidate_label = (
            st.selectbox(
                "Επιλογή υποψηφίου",

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


        if (
            current_status
            in recruitment_statuses
        ):

            current_status_index = (
                recruitment_statuses.index(
                    current_status
                )
            )

        else:

            current_status_index = 0


        with st.form(
            f"candidate_update_"
            f"{selected_candidate['id']}"
        ):

            new_status = (
                st.selectbox(
                    "Κατάσταση",

                    recruitment_statuses,

                    index=(
                        current_status_index
                    ),
                )
            )


            interview_enabled = (
                st.checkbox(
                    "Έχει οριστεί συνέντευξη",

                    value=bool(
                        selected_candidate.get(
                            "interview_date"
                        )
                    ),
                )
            )


            interview_date = (
                st.date_input(
                    "Ημερομηνία συνέντευξης",

                    value=parse_date(
                        selected_candidate.get(
                            "interview_date"
                        )
                    ),

                    format="DD/MM/YYYY",

                    disabled=(
                        not interview_enabled
                    ),
                )
            )


            current_rating = (
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
                        current_rating
                    )
                    if current_rating
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


            update_candidate_button = (
                st.form_submit_button(
                    "💾 Αποθήκευση υποψηφίου",
                    type="primary",
                )
            )


            if update_candidate_button:

                try:

                    update_candidate(
                        selected_candidate[
                            "id"
                        ],

                        new_status,

                        changed_by=safe_text(
                            user_email
                            or user_name
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


                except Exception as exc:

                    st.error(
                        f"Σφάλμα: {exc}"
                    )


        if (
            selected_candidate.get(
                "status"
            )
            == "Προσλήφθηκε"
        ):

            st.success(
                "✅ Ο υποψήφιος έχει κατάσταση Προσλήφθηκε."
            )


            if st.button(
                "👥 Δημιουργία εργαζομένου + Onboarding",

                key=(
                    "create_employee_onboarding_"
                    f"{selected_candidate['id']}"
                ),

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
                                or user_email
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
                            "✅ Δημιουργήθηκε εργαζόμενος και ξεκίνησε αυτόματα Onboarding."
                        )


                    st.rerun()


                except Exception as exc:

                    st.error(
                        f"Σφάλμα: {exc}"
                    )


        with st.expander(
            "🕘 Ιστορικό υποψηφίου"
        ):

            history = (
                get_candidate_history(
                    selected_candidate[
                        "id"
                    ]
                )
            )


            if history:

                history_df = (
                    pd.DataFrame(
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
                                    )
                                    or "-",

                                "Από χρήστη":
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
                )


                st.dataframe(
                    history_df,
                    use_container_width=True,
                    hide_index=True,
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

    onboarding_rows = (
        get_onboarding()
    )


    # --------------------------------------------------------
    # NEW ONBOARDING
    # --------------------------------------------------------

    st.subheader(
        "➕ Νέο Onboarding"
    )


    if not employees:

        st.info(
            "Πρέπει πρώτα να υπάρχει τουλάχιστον ένας εργαζόμενος."
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
            "new_onboarding_form",
            clear_on_submit=False,
        ):

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


            col1, col2 = st.columns(
                2
            )


            onboarding_start_date = (
                col1.date_input(
                    "Ημερομηνία έναρξης",

                    value=date.today(),

                    format="DD/MM/YYYY",
                )
            )


            onboarding_deadline = (
                col2.date_input(
                    "📅 Deadline",

                    value=(
                        date.today()
                        + timedelta(
                            days=14
                        )
                    ),

                    format="DD/MM/YYYY",
                )
            )


            onboarding_responsible = (
                st.text_input(
                    "👤 Υπεύθυνος Onboarding",

                    value=safe_text(
                        user_name
                        or user_email
                    ),
                )
            )


            create_onboarding_button = (
                st.form_submit_button(
                    "🚀 Δημιουργία Onboarding",
                    type="primary",
                )
            )


            if create_onboarding_button:

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

                    try:

                        create_onboarding(
                            selected_employee[
                                "id"
                            ],

                            onboarding_start_date.strftime(
                                "%Y-%m-%d"
                            ),

                            onboarding_responsible.strip()
                            or None,

                            onboarding_deadline.strftime(
                                "%Y-%m-%d"
                            ),
                        )


                        st.success(
                            "✅ Το Onboarding δημιουργήθηκε."
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Σφάλμα: {exc}"
                        )


    # --------------------------------------------------------
    # ONBOARDING LIST
    # --------------------------------------------------------

    st.markdown(
        "---"
    )


    st.subheader(
        "📋 Onboarding Checklist"
    )


    onboarding_rows = (
        get_onboarding()
    )


    if not onboarding_rows:

        st.info(
            "Δεν υπάρχουν Onboarding εγγραφές."
        )


    else:

        for row in onboarding_rows:

            employee_name = (
                f"{row.get('first_name', '')} "
                f"{row.get('last_name', '')}"
            ).strip()


            completed, progress_percent = (
                onboarding_progress(
                    row
                )
            )


            computed_status = (
                onboarding_status_from_row(
                    row
                )
            )


            title = (
                f"👤 {employee_name} "
                f"— {progress_percent}% "
                f"— {computed_status}"
            )


            with st.expander(
                title
            ):

                metric1, metric2, metric3, metric4 = (
                    st.columns(
                        4
                    )
                )


                metric1.metric(
                    "📊 Progress",
                    f"{progress_percent}%",
                )


                metric2.metric(
                    "✅ Tasks",
                    f"{completed}/7",
                )


                metric3.metric(
                    "🔄 Status",
                    computed_status,
                )


                metric4.metric(
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


                st.caption(
                    f"Πρόοδος: "
                    f"{completed}/7 "
                    f"({progress_percent}%)"
                )


                deadline_value = (
                    row.get(
                        "deadline"
                    )
                )


                if (
                    deadline_value
                    and computed_status
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
                            "⚠️ Εκπρόθεσμο Onboarding "
                            f"— deadline "
                            f"{deadline_date.strftime('%d/%m/%Y')}"
                        )


                with st.form(
                    f"onboarding_form_"
                    f"{row['id']}"
                ):

                    col1, col2 = (
                        st.columns(
                            2
                        )
                    )


                    responsible = (
                        col1.text_input(
                            "👤 Υπεύθυνος Onboarding",

                            value=safe_text(
                                row.get(
                                    "responsible"
                                )
                            ),

                            key=(
                                "responsible_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    deadline = (
                        col2.date_input(
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

                            key=(
                                "deadline_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    st.caption(
                        "Ημερομηνία έναρξης: "
                        f"{format_date(row.get('start_date'))}"
                    )


                    check1, check2 = (
                        st.columns(
                            2
                        )
                    )


                    contract = (
                        check1.checkbox(
                            "📄 Σύμβαση",

                            value=bool(
                                row.get(
                                    "contract"
                                )
                            ),

                            key=(
                                "contract_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    documents = (
                        check2.checkbox(
                            "🪪 Έγγραφα εργαζομένου",

                            value=bool(
                                row.get(
                                    "documents"
                                )
                            ),

                            key=(
                                "documents_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    check3, check4 = (
                        st.columns(
                            2
                        )
                    )


                    company_email = (
                        check3.checkbox(
                            "📧 Εταιρικό email",

                            value=bool(
                                row.get(
                                    "email"
                                )
                            ),

                            key=(
                                "email_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    equipment = (
                        check4.checkbox(
                            "💻 Εξοπλισμός",

                            value=bool(
                                row.get(
                                    "equipment"
                                )
                            ),

                            key=(
                                "equipment_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    check5, check6 = (
                        st.columns(
                            2
                        )
                    )


                    system_access = (
                        check5.checkbox(
                            "🔐 Πρόσβαση στα συστήματα",

                            value=bool(
                                row.get(
                                    "system_access"
                                )
                            ),

                            key=(
                                "system_access_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    training = (
                        check6.checkbox(
                            "🎓 Εκπαίδευση",

                            value=bool(
                                row.get(
                                    "training"
                                )
                            ),

                            key=(
                                "training_"
                                f"{row['id']}"
                            ),
                        )
                    )


                    manager_meeting = (
                        st.checkbox(
                            "🤝 Συνάντηση με Manager",

                            value=bool(
                                row.get(
                                    "manager_meeting"
                                )
                            ),

                            key=(
                                "manager_meeting_"
                                f"{row['id']}"
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

                        try:

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


                        except Exception as exc:

                            st.error(
                                f"Σφάλμα: {exc}"
                            )


# ============================================================
# LEAVES - HR / ADMIN
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

    st.caption(
        "Διαχείριση αιτημάτων αδείας."
    )


    employees = get_employees()


    if employees:

        employee_options = {

            (
                f"{employee['first_name']} "
                f"{employee['last_name']} "
                f"— ID {employee['id']}"
            ): employee

            for employee
            in employees
        }


        with st.expander(
            "➕ Νέα άδεια",
            expanded=False,
        ):

            with st.form(
                "hr_add_leave_form",
                clear_on_submit=True,
            ):

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


                leave_type = st.selectbox(
                    "Τύπος άδειας",

                    [
                        "Κανονική",
                        "Αναρρωτική",
                        "Άδεια άνευ αποδοχών",
                        "Άλλη",
                    ],
                )


                col1, col2 = st.columns(
                    2
                )


                start_date = (
                    col1.date_input(
                        "Από",

                        value=date.today(),

                        format="DD/MM/YYYY",
                    )
                )


                end_date = (
                    col2.date_input(
                        "Έως",

                        value=date.today(),

                        format="DD/MM/YYYY",
                    )
                )


                reason = st.text_area(
                    "Αιτιολογία"
                )


                submit_leave = (
                    st.form_submit_button(
                        "💾 Καταχώρηση άδειας",
                        type="primary",
                    )
                )


                if submit_leave:

                    if (
                        end_date
                        < start_date
                    ):

                        st.error(
                            "Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την έναρξη."
                        )


                    else:

                        try:

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
                                "✅ Η άδεια καταχωρήθηκε."
                            )


                            st.rerun()


                        except Exception as exc:

                            st.error(
                                f"Σφάλμα: {exc}"
                            )


    leaves = get_leaves()


    if not leaves:

        st.info(
            "Δεν υπάρχουν αιτήματα αδείας."
        )


    else:

        for leave in leaves:

            employee_name = (
                f"{leave.get('first_name', '')} "
                f"{leave.get('last_name', '')}"
            ).strip()


            with st.expander(
                f"{employee_name} "
                f"— {leave.get('leave_type')} "
                f"— {leave.get('status')}"
            ):

                st.write(
                    "**Από:** "
                    f"{format_date(leave.get('start_date'))}"
                )


                st.write(
                    "**Έως:** "
                    f"{format_date(leave.get('end_date'))}"
                )


                st.write(
                    "**Αιτιολογία:** "
                    f"{leave.get('reason') or '-'}"
                )


                current_leave_status = (
                    leave.get(
                        "status"
                    )
                    or "Εκκρεμεί"
                )


                leave_statuses = [
                    "Εκκρεμεί",
                    "Εγκρίθηκε",
                    "Απορρίφθηκε",
                ]


                if (
                    current_leave_status
                    in leave_statuses
                ):

                    status_index = (
                        leave_statuses.index(
                            current_leave_status
                        )
                    )

                else:

                    status_index = 0


                new_leave_status = (
                    st.selectbox(
                        "Κατάσταση",

                        leave_statuses,

                        index=status_index,

                        key=(
                            "leave_status_"
                            f"{leave['id']}"
                        ),
                    )
                )


                if st.button(
                    "💾 Ενημέρωση κατάστασης",

                    key=(
                        "update_leave_"
                        f"{leave['id']}"
                    ),
                ):

                    try:

                        update_leave_status(
                            leave[
                                "id"
                            ],

                            new_leave_status,
                        )


                        st.success(
                            "✅ Η κατάσταση ενημερώθηκε."
                        )


                        st.rerun()


                    except Exception as exc:

                        st.error(
                            f"Σφάλμα: {exc}"
                        )


# ============================================================
# EMPLOYEE PROFILE
# ============================================================

elif page == "👤 Το προφίλ μου":

    st.title(
        "👤 Το προφίλ μου"
    )


    employee = (
        get_employee_by_email(
            user_email
        )
    )


    if not employee:

        st.warning(
            "Δεν βρέθηκε εργαζόμενος με το email του λογαριασμού σου."
        )


    else:

        col1, col2, col3 = (
            st.columns(
                3
            )
        )


        col1.metric(
            "Ονοματεπώνυμο",

            (
                f"{employee.get('first_name')} "
                f"{employee.get('last_name')}"
            ),
        )


        col2.metric(
            "Θέση",
            employee.get(
                "position"
            )
            or "-",
        )


        col3.metric(
            "Τμήμα",
            employee.get(
                "department"
            )
            or "-",
        )


        st.write(
            "**Email:** "
            f"{employee.get('email') or '-'}"
        )


        st.write(
            "**Τηλέφωνο:** "
            f"{employee.get('phone') or '-'}"
        )


        st.write(
            "**Ημερομηνία πρόσληψης:** "
            f"{format_date(employee.get('hire_date'))}"
        )


        st.write(
            "**Κατάσταση:** "
            f"{employee.get('status') or '-'}"
        )


# ============================================================
# EMPLOYEE LEAVES
# ============================================================

elif page == "🏖️ Οι άδειές μου":

    st.title(
        "🏖️ Οι άδειές μου"
    )


    employee = (
        get_employee_by_email(
            user_email
        )
    )


    if not employee:

        st.warning(
            "Δεν βρέθηκε εργαζόμενος με το email του λογαριασμού σου."
        )


    else:

        with st.expander(
            "➕ Νέο αίτημα άδειας",
            expanded=False,
        ):

            with st.form(
                "employee_leave_form",
                clear_on_submit=True,
            ):

                leave_type = (
                    st.selectbox(
                        "Τύπος άδειας",

                        [
                            "Κανονική",
                            "Αναρρωτική",
                            "Άδεια άνευ αποδοχών",
                            "Άλλη",
                        ],
                    )
                )


                col1, col2 = (
                    st.columns(
                        2
                    )
                )


                start_date = (
                    col1.date_input(
                        "Από",

                        value=date.today(),

                        format="DD/MM/YYYY",
                    )
                )


                end_date = (
                    col2.date_input(
                        "Έως",

                        value=date.today(),

                        format="DD/MM/YYYY",
                    )
                )


                reason = (
                    st.text_area(
                        "Αιτιολογία"
                    )
                )


                submit_my_leave = (
                    st.form_submit_button(
                        "📨 Υποβολή αιτήματος",
                        type="primary",
                    )
                )


                if submit_my_leave:

                    if (
                        end_date
                        < start_date
                    ):

                        st.error(
                            "Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την έναρξη."
                        )


                    else:

                        try:

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
                                "✅ Το αίτημα άδειας υποβλήθηκε."
                            )


                            st.rerun()


                        except Exception as exc:

                            st.error(
                                f"Σφάλμα: {exc}"
                            )


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


        if not my_leaves:

            st.info(
                "Δεν έχεις αιτήματα αδείας."
            )


        else:

            my_leave_df = (
                pd.DataFrame(
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

                            "Αιτιολογία":
                                leave.get(
                                    "reason"
                                )
                                or "-",

                            "Κατάσταση":
                                leave.get(
                                    "status"
                                ),
                        }

                        for leave
                        in my_leaves
                    ]
                )
            )


            st.dataframe(
                my_leave_df,
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title(
        "🤖 AI Assistant"
    )


    st.caption(
        "Ο AI Assistant είναι έτοιμος ως module, "
        "αλλά δεν χρησιμοποιεί πληρωμένο OpenAI API."
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
                "Το HR σύστημα λειτουργεί κανονικά. "
                "Το επόμενο βήμα μπορεί να είναι σύνδεση "
                "με δωρεάν/local AI μοντέλο χωρίς OpenAI credits."
            )