import streamlit as st
import pandas as pd
from datetime import date

from database import (
    create_tables,
    add_employee,
    get_employees,
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
    get_hr_statistics
)


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
    st.markdown("Διαχείριση υποψηφίων και διαδικασίας προσλήψεων.")

    status_options = [
        "Νέα αίτηση",
        "Σε αξιολόγηση",
        "Συνέντευξη",
        "Προσφορά",
        "Προσλήφθηκε",
        "Απορρίφθηκε"
    ]

    # --------------------------------------------------------
    # ADD CANDIDATE
    # --------------------------------------------------------

    st.subheader("➕ Προσθήκη υποψηφίου")

    with st.form("candidate_form"):

        first_name = st.text_input("Όνομα")
        last_name = st.text_input("Επώνυμο")
        email = st.text_input("Email")
        phone = st.text_input("Τηλέφωνο")
        position = st.text_input("Θέση εργασίας")

        application_date = st.date_input(
            "Ημερομηνία αίτησης",
            value=date.today(),
            format="DD/MM/YYYY"
        )

        status = st.selectbox("Κατάσταση", status_options)

        interview_date = st.text_input(
            "📅 Ημερομηνία / ώρα συνέντευξης",
            placeholder="π.χ. 10/09/2026 11:00"
        )

        rating = st.selectbox(
            "⭐ Αξιολόγηση",
            [None, 1, 2, 3, 4, 5],
            format_func=lambda x: "Χωρίς αξιολόγηση" if x is None else str(x)
        )

        recruiter = st.text_input("👤 Recruiter")
        notes = st.text_area("📝 Σημειώσεις HR")

        submitted = st.form_submit_button("💾 Αποθήκευση υποψηφίου")

        if submitted:

            if not first_name or not last_name:
                st.error("Το Όνομα και το Επώνυμο είναι υποχρεωτικά.")

            else:
                try:
                    add_candidate(
                        first_name,
                        last_name,
                        email,
                        phone,
                        position,
                        application_date.strftime("%Y-%m-%d"),
                        status,
                        interview_date.strip() or None,
                        rating,
                        notes.strip() or None,
                        recruiter.strip() or None
                    )

                    st.success("Ο υποψήφιος προστέθηκε!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Σφάλμα προσθήκης: {e}")

    st.markdown("---")

    # --------------------------------------------------------
    # CANDIDATES / PIPELINE
    # --------------------------------------------------------

    st.subheader("📊 Recruitment Pipeline")

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
                "Κατάσταση": candidate["status"],
                "Συνέντευξη": candidate.get("interview_date"),
                "Αξιολόγηση": candidate.get("rating"),
                "Recruiter": candidate.get("recruiter")
            })

        df_candidates = pd.DataFrame(candidate_data)

        st.dataframe(
            df_candidates,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("👤 Διαχείριση υποψηφίου")

        candidate_options = {
            f'{candidate["first_name"]} {candidate["last_name"]} '
            f'(ID: {candidate["id"]})': candidate
            for candidate in candidates
        }

        selected_candidate_name = st.selectbox(
            "Επίλεξε υποψήφιο",
            list(candidate_options.keys())
        )

        selected_candidate = candidate_options[selected_candidate_name]

        current_status = selected_candidate.get("status") or "Νέα αίτηση"
        status_index = (
            status_options.index(current_status)
            if current_status in status_options
            else 0
        )

        with st.form(f'candidate_management_{selected_candidate["id"]}'):

            new_status = st.selectbox(
                "Κατάσταση υποψηφίου",
                status_options,
                index=status_index
            )

            interview_date_edit = st.text_input(
                "📅 Ημερομηνία / ώρα συνέντευξης",
                value=selected_candidate.get("interview_date") or ""
            )

            rating_values = [None, 1, 2, 3, 4, 5]
            current_rating = selected_candidate.get("rating")
            rating_index = (
                rating_values.index(current_rating)
                if current_rating in rating_values
                else 0
            )

            rating_edit = st.selectbox(
                "⭐ Αξιολόγηση",
                rating_values,
                index=rating_index,
                format_func=lambda x: "Χωρίς αξιολόγηση" if x is None else str(x)
            )

            recruiter_edit = st.text_input(
                "👤 Recruiter",
                value=selected_candidate.get("recruiter") or ""
            )

            notes_edit = st.text_area(
                "📝 Σημειώσεις HR",
                value=selected_candidate.get("notes") or ""
            )

            save_candidate = st.form_submit_button("💾 Αποθήκευση αλλαγών")

            if save_candidate:
                try:
                    update_candidate(
                        selected_candidate["id"],
                        new_status,
                        None,
                        interview_date_edit.strip() or None,
                        rating_edit,
                        notes_edit.strip() or None,
                        recruiter_edit.strip() or None
                    )

                    st.success("✅ Ο υποψήφιος ενημερώθηκε!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Σφάλμα ενημέρωσης: {e}")

        # ----------------------------------------------------
        # CANDIDATE -> EMPLOYEE
        # ----------------------------------------------------

        if selected_candidate.get("status") == "Προσλήφθηκε":

            st.markdown("---")
            st.subheader("👥 Μεταφορά στους εργαζομένους")

            st.info(
                "Ο υποψήφιος έχει προσληφθεί. "
                "Πάτησε το κουμπί για να δημιουργηθεί Employee Profile."
            )

            if st.button(
                "👥 Δημιουργία εργαζομένου",
                key=f'create_employee_{selected_candidate["id"]}'
            ):
                try:
                    employee_id = create_employee_from_candidate(
                        selected_candidate["id"]
                    )

                    st.success(
                        f"✅ Ο εργαζόμενος δημιουργήθηκε/υπάρχει ήδη. "
                        f"Employee ID: {employee_id}"
                    )

                except Exception as e:
                    st.error(f"❌ Σφάλμα δημιουργίας εργαζομένου: {e}")

        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        st.markdown("---")
        st.subheader("📋 Ιστορικό υποψηφίου")

        try:
            history = get_candidate_history(selected_candidate["id"])

            if history:
                history_data = []

                for item in history:
                    history_data.append({
                        "Από": item.get("old_status") or "-",
                        "Σε": item.get("new_status"),
                        "Άλλαξε από": item.get("changed_by") or "-",
                        "Ημερομηνία": item.get("changed_at")
                    })

                st.dataframe(
                    pd.DataFrame(history_data),
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.info("Δεν υπάρχει ιστορικό αλλαγών.")

        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης ιστορικού: {e}")

    else:
        st.info("Δεν υπάρχουν υποψήφιοι ακόμη.")


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
        "Ο AI Assistant θα λειτουργεί ως βοηθός του HR."
    )

    st.info(
        "🚧 Το AI module είναι το επόμενο στάδιο ανάπτυξης."
    )

    st.markdown("### Παραδείγματα λειτουργιών")

    st.write(
        "💬 Απάντηση σε ερωτήσεις HR"
    )

    st.write(
        "📄 Δημιουργία αγγελιών εργασίας"
    )

    st.write(
        "📝 Δημιουργία περιγραφών θέσεων"
    )

    st.write(
        "📊 Ανάλυση εργαζομένων και KPIs"
    )

    st.write(
        "🎯 Βοήθεια στην αξιολόγηση υποψηφίων"
    )

    st.write(
        "📧 Δημιουργία επαγγελματικών email HR"
    )

    st.markdown("---")

    question = st.text_area(
        "Γράψε την ερώτησή σου:"
    )

    if st.button("🤖 Ρώτησε τον AI Assistant"):

        if question:

            st.info(
                "Το AI μοντέλο θα συνδεθεί στο επόμενο στάδιο."
            )

        else:

            st.warning(
                "Γράψε πρώτα μια ερώτηση."
            )