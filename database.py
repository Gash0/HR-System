
import streamlit as st
import psycopg
from datetime import datetime
from psycopg.rows import dict_row


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return psycopg.connect(
        st.secrets["database"]["url"],
        row_factory=dict_row,
        connect_timeout=10,
    )


# ============================================================
# TEST CONNECTION
# ============================================================

def test_postgres_connection():
    connection = get_connection()
    connection.close()
    return True


# ============================================================
# EMPLOYEES
# ============================================================

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            position TEXT,
            department TEXT,
            hire_date TEXT,
            status TEXT DEFAULT 'Ενεργός'
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


def add_employee(
    first_name,
    last_name,
    email,
    phone,
    position,
    department,
    hire_date,
    status="Ενεργός",
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO employees (
            first_name,
            last_name,
            email,
            phone,
            position,
            department,
            hire_date,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        first_name,
        last_name,
        email,
        phone,
        position,
        department,
        hire_date,
        status,
    ))

    connection.commit()
    cursor.close()
    connection.close()


def get_employees():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM employees
        ORDER BY id DESC
    """)

    employees = cursor.fetchall()

    cursor.close()
    connection.close()

    return employees


def get_employee_by_email(email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM employees
        WHERE LOWER(email) = LOWER(%s)
        LIMIT 1
    """, (email,))

    employee = cursor.fetchone()

    cursor.close()
    connection.close()

    return employee


def update_employee(
    employee_id,
    first_name,
    last_name,
    email,
    phone,
    position,
    department,
    hire_date,
    status,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE employees
        SET
            first_name = %s,
            last_name = %s,
            email = %s,
            phone = %s,
            position = %s,
            department = %s,
            hire_date = %s,
            status = %s
        WHERE id = %s
    """, (
        first_name,
        last_name,
        email,
        phone,
        position,
        department,
        hire_date,
        status,
        employee_id,
    ))

    connection.commit()
    cursor.close()
    connection.close()


def delete_employee(employee_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = %s
    """, (employee_id,))

    connection.commit()
    cursor.close()
    connection.close()


# ============================================================
# RECRUITMENT
# ============================================================

def create_recruitment_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            position TEXT,
            application_date TEXT,
            status TEXT DEFAULT 'Νέα αίτηση'
        )
    """)

    # Νέα πεδία Recruitment
    cursor.execute("""
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS interview_date TEXT
    """)

    cursor.execute("""
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS rating INTEGER
    """)

    cursor.execute("""
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS notes TEXT
    """)

    cursor.execute("""
        ALTER TABLE candidates
        ADD COLUMN IF NOT EXISTS recruiter TEXT
    """)

    # Ιστορικό αλλαγών υποψηφίων
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_history (
            id SERIAL PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by TEXT,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id)
                REFERENCES candidates(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


def add_candidate(
    first_name,
    last_name,
    email,
    phone,
    position,
    application_date,
    status="Νέα αίτηση",
    interview_date=None,
    rating=None,
    notes=None,
    recruiter=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO candidates (
            first_name,
            last_name,
            email,
            phone,
            position,
            application_date,
            status,
            interview_date,
            rating,
            notes,
            recruiter
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        RETURNING id
    """, (
        first_name,
        last_name,
        email,
        phone,
        position,
        application_date,
        status,
        interview_date,
        rating,
        notes,
        recruiter,
    ))

    candidate_id = cursor.fetchone()["id"]

    # Αρχική εγγραφή στο history
    cursor.execute("""
        INSERT INTO candidate_history (
            candidate_id,
            old_status,
            new_status,
            changed_by
        )
        VALUES (%s, %s, %s, %s)
    """, (
        candidate_id,
        None,
        status,
        recruiter,
    ))

    connection.commit()

    cursor.close()
    connection.close()


def get_candidates():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM candidates
        ORDER BY id DESC
    """)

    candidates = cursor.fetchall()

    cursor.close()
    connection.close()

    return candidates


def update_candidate(
    candidate_id,
    status,
    changed_by=None,
    interview_date=None,
    rating=None,
    notes=None,
    recruiter=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status
        FROM candidates
        WHERE id = %s
    """, (candidate_id,))

    candidate = cursor.fetchone()

    if candidate is None:
        connection.close()
        raise ValueError("Ο υποψήφιος δεν βρέθηκε.")

    old_status = candidate["status"]

    cursor.execute("""
        UPDATE candidates
        SET
            status = %s,
            interview_date = %s,
            rating = %s,
            notes = %s,
            recruiter = %s
        WHERE id = %s
    """, (
        status,
        interview_date,
        rating,
        notes,
        recruiter,
        candidate_id,
    ))

    if old_status != status:

        cursor.execute("""
            INSERT INTO candidate_history (
                candidate_id,
                old_status,
                new_status,
                changed_by
            )
            VALUES (%s, %s, %s, %s)
        """, (
            candidate_id,
            old_status,
            status,
            changed_by,
        ))

    connection.commit()

    cursor.close()
    connection.close()


def get_candidate_history(candidate_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            candidate_id,
            old_status,
            new_status,
            changed_by,
            changed_at
        FROM candidate_history
        WHERE candidate_id = %s
        ORDER BY changed_at DESC, id DESC
    """, (candidate_id,))

    history = cursor.fetchall()

    cursor.close()
    connection.close()

    return history


# ============================================================
# ONBOARDING
# ============================================================

def create_onboarding_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            contract INTEGER DEFAULT 0,
            documents INTEGER DEFAULT 0,
            email INTEGER DEFAULT 0,
            equipment INTEGER DEFAULT 0,
            system_access INTEGER DEFAULT 0,
            training INTEGER DEFAULT 0,
            manager_meeting INTEGER DEFAULT 0,
            start_date TEXT,
            responsible TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'Δεν ξεκίνησε',
            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        ALTER TABLE onboarding
        ADD COLUMN IF NOT EXISTS responsible TEXT
    """)

    cursor.execute("""
        ALTER TABLE onboarding
        ADD COLUMN IF NOT EXISTS deadline TEXT
    """)

    cursor.execute("""
        ALTER TABLE onboarding
        ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Δεν ξεκίνησε'
    """)

    cursor.execute("""
        UPDATE onboarding
        SET status = CASE
            WHEN COALESCE(contract, 0) + COALESCE(documents, 0) +
                 COALESCE(email, 0) + COALESCE(equipment, 0) +
                 COALESCE(system_access, 0) + COALESCE(training, 0) +
                 COALESCE(manager_meeting, 0) = 7
                THEN 'Ολοκληρώθηκε'
            WHEN COALESCE(contract, 0) + COALESCE(documents, 0) +
                 COALESCE(email, 0) + COALESCE(equipment, 0) +
                 COALESCE(system_access, 0) + COALESCE(training, 0) +
                 COALESCE(manager_meeting, 0) > 0
                THEN 'Σε εξέλιξη'
            ELSE 'Δεν ξεκίνησε'
        END
        WHERE status IS NULL OR status = ''
    """)

    connection.commit()
    cursor.close()
    connection.close()


def create_onboarding(
    employee_id,
    start_date,
    responsible=None,
    deadline=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO onboarding (
            employee_id,
            start_date,
            responsible,
            deadline,
            status
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        employee_id,
        start_date,
        responsible,
        deadline,
        'Δεν ξεκίνησε',
    ))

    connection.commit()
    cursor.close()
    connection.close()


def get_onboarding():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            onboarding.*,
            employees.first_name,
            employees.last_name
        FROM onboarding
        JOIN employees
            ON onboarding.employee_id = employees.id
        ORDER BY onboarding.id DESC
    """)

    onboarding = cursor.fetchall()

    cursor.close()
    connection.close()

    return onboarding


def update_onboarding(
    onboarding_id,
    contract,
    documents,
    email,
    equipment,
    system_access,
    training,
    manager_meeting,
    responsible=None,
    deadline=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    completed_tasks = sum([
        int(bool(contract)),
        int(bool(documents)),
        int(bool(email)),
        int(bool(equipment)),
        int(bool(system_access)),
        int(bool(training)),
        int(bool(manager_meeting)),
    ])

    if completed_tasks == 7:
        status = 'Ολοκληρώθηκε'
    elif completed_tasks > 0:
        status = 'Σε εξέλιξη'
    else:
        status = 'Δεν ξεκίνησε'

    cursor.execute("""
        UPDATE onboarding
        SET
            contract = %s,
            documents = %s,
            email = %s,
            equipment = %s,
            system_access = %s,
            training = %s,
            manager_meeting = %s,
            responsible = %s,
            deadline = %s,
            status = %s
        WHERE id = %s
    """, (
        contract,
        documents,
        email,
        equipment,
        system_access,
        training,
        manager_meeting,
        responsible,
        deadline,
        status,
        onboarding_id,
    ))

    connection.commit()
    cursor.close()
    connection.close()


# ============================================================
# LEAVES
# ============================================================

def create_leave_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Εκκρεμεί',
            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


def add_leave(
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason,
    status="Εκκρεμεί",
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO leaves (
            employee_id,
            leave_type,
            start_date,
            end_date,
            reason,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        employee_id,
        leave_type,
        start_date,
        end_date,
        reason,
        status,
    ))

    connection.commit()
    cursor.close()
    connection.close()


def get_leaves():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            leaves.*,
            employees.first_name,
            employees.last_name
        FROM leaves
        JOIN employees
            ON leaves.employee_id = employees.id
        ORDER BY leaves.id DESC
    """)

    leaves = cursor.fetchall()

    cursor.close()
    connection.close()

    return leaves


def update_leave_status(leave_id, status):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leaves
        SET status = %s
        WHERE id = %s
    """, (
        status,
        leave_id,
    ))

    connection.commit()
    cursor.close()
    connection.close()


# ============================================================
# HR STATISTICS
# ============================================================

def get_hr_statistics():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM employees
    """)
    total_employees = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS active
        FROM employees
        WHERE status = 'Ενεργός'
    """)
    active_employees = cursor.fetchone()["active"]

    cursor.execute("""
        SELECT COUNT(*) AS inactive
        FROM employees
        WHERE status = 'Ανενεργός'
    """)
    inactive_employees = cursor.fetchone()["inactive"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM candidates
    """)
    total_candidates = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS hired
        FROM candidates
        WHERE status = 'Προσλήφθηκε'
    """)
    hired_candidates = cursor.fetchone()["hired"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM leaves
    """)
    total_leaves = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS pending
        FROM leaves
        WHERE status = 'Εκκρεμεί'
    """)
    pending_leaves = cursor.fetchone()["pending"]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_candidates": total_candidates,
        "hired_candidates": hired_candidates,
        "total_leaves": total_leaves,
        "pending_leaves": pending_leaves,
    }

def create_employee_from_candidate(candidate_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM candidates
        WHERE id = %s
        LIMIT 1
    """, (candidate_id,))

    candidate = cursor.fetchone()

    if candidate is None:
        cursor.close()
        connection.close()
        raise ValueError("Ο υποψήφιος δεν βρέθηκε.")

    if candidate["status"] != "Προσλήφθηκε":
        cursor.close()
        connection.close()
        raise ValueError(
            "Ο υποψήφιος πρέπει πρώτα να έχει κατάσταση «Προσλήφθηκε»."
        )

    email = candidate["email"]

    if email:
        cursor.execute("""
            SELECT id
            FROM employees
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
        """, (email,))

        existing_employee = cursor.fetchone()

        if existing_employee:
            cursor.close()
            connection.close()
            return existing_employee["id"]

    cursor.execute("""
        INSERT INTO employees (
            first_name,
            last_name,
            email,
            phone,
            position,
            department,
            hire_date,
            status
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING id
    """, (
        candidate["first_name"],
        candidate["last_name"],
        email,
        candidate["phone"],
        candidate["position"],
        None,
        candidate["application_date"],
        "Ενεργός",
    ))

    employee_id = cursor.fetchone()["id"]

    connection.commit()

    cursor.close()
    connection.close()

    return employee_id

def get_time_to_hire_stats():
    """
    Υπολογίζει Time to Hire από:
    application_date -> ημερομηνία που ο candidate έγινε 'Προσλήφθηκε'
    """

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    c.id,
                    c.first_name,
                    c.last_name,
                    c.position,
                    c.application_date,
                    MIN(ch.changed_at) AS hired_at
                FROM candidates c
                JOIN candidate_history ch
                    ON ch.candidate_id = c.id
                WHERE ch.new_status = 'Προσλήφθηκε'
                GROUP BY
                    c.id,
                    c.first_name,
                    c.last_name,
                    c.position,
                    c.application_date
                ORDER BY hired_at DESC
                """
            )

            rows = cur.fetchall()

        results = []

        for row in rows:

            application_date = row.get("application_date")
            hired_at = row.get("hired_at")

            if not application_date or not hired_at:
                continue

            if isinstance(application_date, str):
                application_date_obj = datetime.strptime(
                    application_date[:10],
                    "%Y-%m-%d",
                ).date()
            else:
                application_date_obj = application_date

            if isinstance(hired_at, datetime):
                hired_date_obj = hired_at.date()
            elif isinstance(hired_at, str):
                hired_date_obj = datetime.fromisoformat(
                    hired_at
                ).date()
            else:
                hired_date_obj = hired_at

            days_to_hire = (
                hired_date_obj - application_date_obj
            ).days

            if days_to_hire >= 0:
                results.append(
                    {
                        "id": row.get("id"),
                        "first_name": row.get("first_name"),
                        "last_name": row.get("last_name"),
                        "position": row.get("position"),
                        "application_date": application_date_obj,
                        "hired_date": hired_date_obj,
                        "days_to_hire": days_to_hire,
                    }
                )

        return results

    finally:
        conn.close()
