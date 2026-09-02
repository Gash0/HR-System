import streamlit as st
import pandas as pd
from datetime import date

from openai import OpenAI
import os
from dotenv import load_dotenv

from database import (
    create_tables,
    add_employee,
    get_employees,
    delete_employee,
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
    get_hr_statistics
)

if not st.user.is_logged_in:
    st.title("🔐 AI HR System")
    st.subheader("Σύνδεση")
    st.button("Σύνδεση με Google", on_click=st.login)
    st.stop()

st.sidebar.success(f"Συνδεδεμένος: {st.user.name}")

if st.sidebar.button("Αποσύνδεση"):
    st.logout()


# ============================================================
# ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ
# ============================================================

st.set_page_config(
    page_title="AI HR System",
    page_icon="👥",
    layout="wide"
)


# ============================================================
# ΔΗΜΙΟΥΡΓΙΑ DATABASE TABLES
# ============================================================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None

create_tables()
create_recruitment_table()
create_onboarding_table()
create_leave_table()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🤖 AI HR System")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Μενού",
    [
        "📊 Dashboard",
        "👥 Εργαζόμενοι",
        "📋 Recruitment",
        "🚀 Onboarding",
        "🏖️ Άδειες",
        "🤖 AI Assistant"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("AI HR Management System")


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.title("📊 HR Dashboard")
    st.markdown("Κεντρική εικόνα του τμήματος Ανθρώπινου Δυναμικού.")

    stats = get_hr_statistics()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 Σύνολο εργαζομένων",
            stats["total_employees"]
        )

    with col2:
        st.metric(
            "✅ Ενεργοί",
            stats["active_employees"]
        )

    with col3:
        st.metric(
            "📋 Υποψήφιοι",
            stats["total_candidates"]
        )

    with col4:
        st.metric(
            "🏖️ Εκκρεμείς άδειες",
            stats["pending_leaves"]
        )

    st.markdown("---")

    # --------------------------------------------------------
    # ΔΕΥΤΕΡΑ KPI
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "❌ Ανενεργοί",
            stats["inactive_employees"]
        )

    with col2:
        st.metric(
            "🎯 Προσλήψεις",
            stats["hired_candidates"]
        )

    with col3:
        st.metric(
            "🏖️ Σύνολο αιτήσεων άδειας",
            stats["total_leaves"]
        )

    with col4:
        active = stats["active_employees"]
        total = stats["total_employees"]

        if total > 0:
            percentage = round((active / total) * 100, 1)
        else:
            percentage = 0

        st.metric(
            "📈 Ποσοστό ενεργών",
            f"{percentage}%"
        )

    st.markdown("---")

    # --------------------------------------------------------
    # EMPLOYEE ANALYTICS
    # --------------------------------------------------------

    st.subheader("📈 Ανάλυση εργαζομένων")

    employees = get_employees()

    if employees:

        employee_data = []

        for employee in employees:
            employee_data.append({
                "Όνομα": employee["first_name"],
                "Επώνυμο": employee["last_name"],
                "Email": employee["email"],
                "Τηλέφωνο": employee["phone"],
                "Θέση": employee["position"],
                "Τμήμα": employee["department"],
                "Ημερομηνία πρόσληψης": employee["hire_date"],
                "Κατάσταση": employee["status"]
            })

        df_employees = pd.DataFrame(employee_data)

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### Εργαζόμενοι ανά τμήμα")

            department_counts = (
                df_employees["Τμήμα"]
                .fillna("Χωρίς τμήμα")
                .value_counts()
            )

            st.bar_chart(department_counts)

        with col2:

            st.markdown("### Εργαζόμενοι ανά κατάσταση")

            status_counts = df_employees["Κατάσταση"].value_counts()

            st.bar_chart(status_counts)

    else:

        st.info(
            "Δεν υπάρχουν εργαζόμενοι ακόμη. "
            "Πρόσθεσε τον πρώτο εργαζόμενο από την ενότητα «Εργαζόμενοι»."
        )


# ============================================================
# ΕΡΓΑΖΟΜΕΝΟΙ
# ============================================================

elif page == "👥 Εργαζόμενοι":

    st.title("👥 Διαχείριση Εργαζομένων")

    # --------------------------------------------------------
    # ADD EMPLOYEE
    # --------------------------------------------------------

    st.subheader("➕ Προσθήκη εργαζομένου")

    with st.form("employee_form"):

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
            format="DD/MM/YYYY"
        )

        status = st.selectbox(
            "Κατάσταση",
            [
                "Ενεργός",
                "Ανενεργός",
                "Σε άδεια"
            ]
        )

        submitted = st.form_submit_button(
            "💾 Αποθήκευση εργαζομένου"
        )

        if submitted:

            if not first_name or not last_name:

                st.error(
                    "Το Όνομα και το Επώνυμο είναι υποχρεωτικά."
                )

            else:

                add_employee(
                    first_name,
                    last_name,
                    email,
                    phone,
                    position,
                    department,
                    hire_date.strftime("%Y-%m-%d"),
                    status
                )

                st.success(
                    "Ο εργαζόμενος προστέθηκε επιτυχώς!"
                )

                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # EMPLOYEE LIST
    # --------------------------------------------------------

    st.subheader("📋 Λίστα εργαζομένων")

    employees = get_employees()

    if employees:

        employee_data = []

        for employee in employees:

            employee_data.append({
                "ID": employee["id"],
                "Όνομα": employee["first_name"],
                "Επώνυμο": employee["last_name"],
                "Email": employee["email"],
                "Τηλέφωνο": employee["phone"],
                "Θέση": employee["position"],
                "Τμήμα": employee["department"],
                "Ημερομηνία πρόσληψης": employee["hire_date"],
                "Κατάσταση": employee["status"]
            })

        df = pd.DataFrame(employee_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        st.subheader("🗑️ Διαγραφή εργαζομένου")

        employee_options = {
            f'{employee["first_name"]} {employee["last_name"]} (ID: {employee["id"]})':
            employee["id"]
            for employee in employees
        }

        selected_employee = st.selectbox(
            "Επίλεξε εργαζόμενο",
            list(employee_options.keys())
        )

        if st.button("🗑️ Διαγραφή"):

            employee_id = employee_options[selected_employee]

            delete_employee(employee_id)

            st.success(
                "Ο εργαζόμενος διαγράφηκε."
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

    st.title("📋 Recruitment")

    st.markdown(
        "Διαχείριση υποψηφίων και διαδικασίας προσλήψεων."
    )

    # --------------------------------------------------------
    # ADD CANDIDATE
    # --------------------------------------------------------

    st.subheader("➕ Προσθήκη υποψηφίου")

    with st.form("candidate_form"):

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
            format="DD/MM/YYYY"
        )

        status = st.selectbox(
            "Κατάσταση",
            [
                "Νέα αίτηση",
                "Σε αξιολόγηση",
                "Συνέντευξη",
                "Προσλήφθηκε",
                "Απορρίφθηκε"
            ]
        )

        submitted = st.form_submit_button(
            "💾 Αποθήκευση υποψηφίου"
        )

        if submitted:

            if not first_name or not last_name:

                st.error(
                    "Το Όνομα και το Επώνυμο είναι υποχρεωτικά."
                )

            else:

                add_candidate(
                    first_name,
                    last_name,
                    email,
                    phone,
                    position,
                    application_date.strftime("%Y-%m-%d"),
                    status
                )

                st.success(
                    "Ο υποψήφιος προστέθηκε!"
                )

                st.rerun()

    st.markdown("---")

    # --------------------------------------------------------
    # CANDIDATES
    # --------------------------------------------------------

    st.subheader("👤 Υποψήφιοι")

    candidates = get_candidates()

    if candidates:

        candidate_data = []

        for candidate in candidates:

            candidate_data.append({
                "ID": candidate["id"],
                "Όνομα": candidate["first_name"],
                "Επώνυμο": candidate["last_name"],
                "Email": candidate["email"],
                "Τηλέφωνο": candidate["phone"],
                "Θέση": candidate["position"],
                "Ημερομηνία αίτησης": candidate["application_date"],
                "Κατάσταση": candidate["status"]
            })

        df_candidates = pd.DataFrame(
            candidate_data
        )

        st.dataframe(
            df_candidates,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Δεν υπάρχουν υποψήφιοι ακόμη."
        )


# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    st.title("🚀 Employee Onboarding")

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

        st.subheader("➕ Νέο Onboarding")

        employee_options = {
            f'{employee["first_name"]} {employee["last_name"]}':
            employee["id"]
            for employee in employees
        }

        with st.form("onboarding_form"):

            selected_employee = st.selectbox(
                "Εργαζόμενος",
                list(employee_options.keys())
            )

            start_date = st.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY"
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
                    start_date.strftime("%Y-%m-%d")
                )

                st.success(
                    "Το onboarding δημιουργήθηκε!"
                )

                st.rerun()

        st.markdown("---")

        # ----------------------------------------------------
        # ONBOARDING LIST
        # ----------------------------------------------------

        st.subheader("📋 Onboarding Checklist")

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
                        f"Ημερομηνία έναρξης: "
                        f"{item['start_date']}"
                    )

                    contract = st.checkbox(
                        "📄 Σύμβαση",
                        value=bool(item["contract"]),
                        key=f"contract_{item['id']}"
                    )

                    documents = st.checkbox(
                        "📁 Έγγραφα",
                        value=bool(item["documents"]),
                        key=f"documents_{item['id']}"
                    )

                    email = st.checkbox(
                        "📧 Email",
                        value=bool(item["email"]),
                        key=f"email_{item['id']}"
                    )

                    equipment = st.checkbox(
                        "💻 Εξοπλισμός",
                        value=bool(item["equipment"]),
                        key=f"equipment_{item['id']}"
                    )

                    system_access = st.checkbox(
                        "🔐 Πρόσβαση σε συστήματα",
                        value=bool(item["system_access"]),
                        key=f"system_{item['id']}"
                    )

                    training = st.checkbox(
                        "🎓 Εκπαίδευση",
                        value=bool(item["training"]),
                        key=f"training_{item['id']}"
                    )

                    manager_meeting = st.checkbox(
                        "🤝 Συνάντηση με Manager",
                        value=bool(item["manager_meeting"]),
                        key=f"manager_{item['id']}"
                    )

                    if st.button(
                        "💾 Αποθήκευση Checklist",
                        key=f"save_onboarding_{item['id']}"
                    ):

                        update_onboarding(
                            item["id"],
                            int(contract),
                            int(documents),
                            int(email),
                            int(equipment),
                            int(system_access),
                            int(training),
                            int(manager_meeting)
                        )

                        st.success(
                            "Το checklist ενημερώθηκε!"
                        )

                        st.rerun()

        else:

            st.info(
                "Δεν υπάρχουν onboarding διαδικασίες."
            )


# ============================================================
# ΑΔΕΙΕΣ
# ============================================================

elif page == "🏖️ Άδειες":

    st.title("🏖️ Διαχείριση Αδειών")

    employees = get_employees()

    if not employees:

        st.warning(
            "Πρέπει πρώτα να προσθέσεις εργαζόμενο."
        )

    else:

        # ----------------------------------------------------
        # ADD LEAVE
        # ----------------------------------------------------

        st.subheader("➕ Νέα αίτηση άδειας")

        employee_options = {
            f'{employee["first_name"]} {employee["last_name"]}':
            employee["id"]
            for employee in employees
        }

        with st.form("leave_form"):

            selected_employee = st.selectbox(
                "Εργαζόμενος",
                list(employee_options.keys())
            )

            leave_type = st.selectbox(
                "Τύπος άδειας",
                [
                    "Κανονική",
                    "Αναρρωτική",
                    "Άδεια άνευ αποδοχών",
                    "Ειδική",
                    "Άλλο"
                ]
            )

            start_date = st.date_input(
                "Ημερομηνία έναρξης",
                value=date.today(),
                format="DD/MM/YYYY"
            )

            end_date = st.date_input(
                "Ημερομηνία λήξης",
                value=date.today(),
                format="DD/MM/YYYY"
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
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        reason
                    )

                    st.success(
                        "Η αίτηση άδειας καταχωρήθηκε!"
                    )

                    st.rerun()

        st.markdown("---")

        # ----------------------------------------------------
        # LEAVE REQUESTS
        # ----------------------------------------------------

        st.subheader("📋 Αιτήσεις αδειών")

        leaves = get_leaves()

        if leaves:

            leave_data = []

            for leave in leaves:

                leave_data.append({
                    "ID": leave["id"],
                    "Εργαζόμενος":
                        f'{leave["first_name"]} {leave["last_name"]}',
                    "Τύπος": leave["leave_type"],
                    "Από": leave["start_date"],
                    "Έως": leave["end_date"],
                    "Αιτιολογία": leave["reason"],
                    "Κατάσταση": leave["status"]
                })

            df_leaves = pd.DataFrame(
                leave_data
            )

            st.dataframe(
                df_leaves,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            st.subheader("🔄 Ενημέρωση κατάστασης")

            leave_options = {
                f'#{leave["id"]} - '
                f'{leave["first_name"]} '
                f'{leave["last_name"]} '
                f'({leave["start_date"]})':
                leave["id"]
                for leave in leaves
            }

            selected_leave = st.selectbox(
                "Αίτηση",
                list(leave_options.keys())
            )

            new_status = st.selectbox(
                "Νέα κατάσταση",
                [
                    "Εκκρεμεί",
                    "Εγκρίθηκε",
                    "Απορρίφθηκε"
                ]
            )

            if st.button(
                "💾 Ενημέρωση"
            ):

                leave_id = leave_options[
                    selected_leave
                ]

                update_leave_status(
                    leave_id,
                    new_status
                )

                st.success(
                    "Η κατάσταση ενημερώθηκε!"
                )

                st.rerun()

        else:

            st.info(
                "Δεν υπάρχουν αιτήσεις άδειας."
            )


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title("🤖 AI HR Assistant")

    st.markdown(
        "Ο έξυπνος βοηθός του τμήματος Ανθρώπινου Δυναμικού."
    )

    if client is None:

        st.error(
            "Δεν βρέθηκε το OPENAI_API_KEY. "
            "Έλεγξε το αρχείο .env."
        )

    else:

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Εμφάνιση προηγούμενων μηνυμάτων
        for message in st.session_state.messages:

            with st.chat_message(message["role"]):

                st.markdown(message["content"])

        # Πεδίο ερώτησης
        question = st.chat_input(
            "Γράψε την ερώτησή σου..."
        )

        if question:

            # Εμφάνιση ερώτησης χρήστη
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            with st.chat_message("user"):
                st.markdown(question)

            # AI απάντηση
            with st.chat_message("assistant"):

                with st.spinner("Το AI σκέφτεται..."):

                    try:

                        response = client.responses.create(
                            model="gpt-5-mini",
                            instructions="""
                            Είσαι ένας επαγγελματικός AI HR Assistant.

                            Βοηθάς έναν HR Manager σε:
                            - Recruitment
                            - Onboarding
                            - Employee Management
                            - HR Administration
                            - HR KPIs
                            - Επαγγελματικά HR emails
                            - Περιγραφές θέσεων εργασίας
                            - Αγγελίες εργασίας

                            Απαντάς πάντα στα ελληνικά,
                            εκτός αν ο χρήστης ζητήσει άλλη γλώσσα.

                            Οι απαντήσεις σου πρέπει να είναι
                            επαγγελματικές, πρακτικές και κατανοητές.
                            """,
                            input=question
                        )

                        answer = response.output_text

                        st.markdown(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })

                    except Exception as e:

                        st.error(
                            f"Παρουσιάστηκε σφάλμα: {e}"
                        )

        if st.session_state.messages:

            st.markdown("---")

            if st.button("🗑️ Καθαρισμός συνομιλίας"):

                st.session_state.messages = []

                st.rerun()