from datetime import datetime

import psycopg
import streamlit as st
from psycopg.rows import dict_row


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    # --------------------------------------------
    # Περίπτωση 1:
    # DATABASE_URL μέσα στα Streamlit Secrets
    # --------------------------------------------

    if "DATABASE_URL" in st.secrets:

        return psycopg.connect(
            st.secrets["DATABASE_URL"],
            row_factory=dict_row,
        )

    # --------------------------------------------
    # Περίπτωση 2:
    # [postgres] μέσα στα Streamlit Secrets
    # --------------------------------------------

    if "postgres" in st.secrets:

        db = st.secrets["postgres"]

        return psycopg.connect(
            host=db["host"],
            port=db.get("port", 5432),
            dbname=db.get("dbname", "postgres"),
            user=db["user"],
            password=db["password"],
            sslmode=db.get("sslmode", "require"),
            row_factory=dict_row,
        )

    raise RuntimeError(
        "Δεν βρέθηκαν PostgreSQL στοιχεία στα Streamlit Secrets."
    )


# ============================================================
# TEST CONNECTION
# ============================================================

def test_postgres_connection():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                "SELECT 1 AS test"
            )

            result = cur.fetchone()

            return result["test"] == 1

    finally:

        conn.close()


# ============================================================
# EMPLOYEES TABLE
# ============================================================

def create_tables():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    position TEXT,
                    department TEXT,
                    hire_date TEXT,
                    status TEXT DEFAULT 'Ενεργός',
                    termination_date TEXT,
                    termination_reason TEXT
                )
                """
            )

            # Για υπάρχουσα βάση
            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS termination_date TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE employees
                ADD COLUMN IF NOT EXISTS termination_reason TEXT
                """
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# ADD EMPLOYEE
# ============================================================

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

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
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
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    first_name,
                    last_name,
                    email,
                    phone,
                    position,
                    department,
                    hire_date,
                    status,
                ),
            )

            result = cur.fetchone()

        conn.commit()

        return result["id"]

    finally:

        conn.close()


# ============================================================
# GET EMPLOYEES
# ============================================================

def get_employees():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM employees
                ORDER BY id DESC
                """
            )

            return cur.fetchall()

    finally:

        conn.close()


# ============================================================
# GET EMPLOYEE BY EMAIL
# ============================================================

def get_employee_by_email(email):

    if not email:
        return None

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM employees
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1
                """,
                (email,),
            )

            return cur.fetchone()

    finally:

        conn.close()


# ============================================================
# UPDATE EMPLOYEE
# ============================================================

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
    termination_date=None,
    termination_reason=None,
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE employees
                SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    phone = %s,
                    position = %s,
                    department = %s,
                    hire_date = %s,
                    status = %s,
                    termination_date = %s,
                    termination_reason = %s
                WHERE id = %s
                """,
                (
                    first_name,
                    last_name,
                    email,
                    phone,
                    position,
                    department,
                    hire_date,
                    status,
                    termination_date,
                    termination_reason,
                    employee_id,
                ),
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# DELETE EMPLOYEE
# ============================================================

def delete_employee(employee_id):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM employees
                WHERE id = %s
                """,
                (employee_id,),
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# RECRUITMENT TABLES
# ============================================================

def create_recruitment_table():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id SERIAL PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    position TEXT,
                    application_date TEXT,
                    status TEXT DEFAULT 'Νέα αίτηση',
                    interview_date TEXT,
                    rating INTEGER,
                    notes TEXT,
                    recruiter TEXT
                )
                """
            )

            cur.execute(
                """
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
                """
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# ADD CANDIDATE
# ============================================================

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

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
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
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
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
                ),
            )

            result = cur.fetchone()

            candidate_id = result["id"]

            cur.execute(
                """
                INSERT INTO candidate_history (
                    candidate_id,
                    old_status,
                    new_status,
                    changed_by
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    candidate_id,
                    None,
                    status,
                    recruiter,
                ),
            )

        conn.commit()

        return candidate_id

    finally:

        conn.close()


# ============================================================
# GET CANDIDATES
# ============================================================

def get_candidates():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM candidates
                ORDER BY id DESC
                """
            )

            return cur.fetchall()

    finally:

        conn.close()


# ============================================================
# UPDATE CANDIDATE
# ============================================================

def update_candidate(
    candidate_id,
    status,
    changed_by=None,
    interview_date=None,
    rating=None,
    notes=None,
    recruiter=None,
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT status
                FROM candidates
                WHERE id = %s
                """,
                (candidate_id,),
            )

            candidate = cur.fetchone()

            if not candidate:
                raise ValueError(
                    "Ο υποψήφιος δεν βρέθηκε."
                )

            old_status = candidate["status"]

            cur.execute(
                """
                UPDATE candidates
                SET
                    status = %s,
                    interview_date = %s,
                    rating = %s,
                    notes = %s,
                    recruiter = %s
                WHERE id = %s
                """,
                (
                    status,
                    interview_date,
                    rating,
                    notes,
                    recruiter,
                    candidate_id,
                ),
            )

            if old_status != status:

                cur.execute(
                    """
                    INSERT INTO candidate_history (
                        candidate_id,
                        old_status,
                        new_status,
                        changed_by
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        candidate_id,
                        old_status,
                        status,
                        changed_by,
                    ),
                )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# CANDIDATE HISTORY
# ============================================================

def get_candidate_history(candidate_id):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM candidate_history
                WHERE candidate_id = %s
                ORDER BY changed_at DESC, id DESC
                """,
                (candidate_id,),
            )

            return cur.fetchall()

    finally:

        conn.close()


# ============================================================
# CREATE EMPLOYEE FROM CANDIDATE
# ============================================================

def create_employee_from_candidate(candidate_id):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM candidates
                WHERE id = %s
                """,
                (candidate_id,),
            )

            candidate = cur.fetchone()

            if not candidate:

                raise ValueError(
                    "Ο υποψήφιος δεν βρέθηκε."
                )

            if candidate["status"] != "Προσλήφθηκε":

                raise ValueError(
                    "Ο υποψήφιος πρέπει πρώτα να έχει κατάσταση 'Προσλήφθηκε'."
                )

            candidate_email = candidate.get(
                "email"
            )

            if candidate_email:

                cur.execute(
                    """
                    SELECT id
                    FROM employees
                    WHERE LOWER(email) = LOWER(%s)
                    LIMIT 1
                    """,
                    (candidate_email,),
                )

                existing = cur.fetchone()

                if existing:

                    return existing["id"]

            cur.execute(
                """
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
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    candidate["first_name"],
                    candidate["last_name"],
                    candidate.get("email"),
                    candidate.get("phone"),
                    candidate.get("position"),
                    None,
                    datetime.today().strftime(
                        "%Y-%m-%d"
                    ),
                    "Ενεργός",
                ),
            )

            result = cur.fetchone()

        conn.commit()

        return result["id"]

    finally:

        conn.close()


# ============================================================
# ONBOARDING TABLE
# ============================================================

def create_onboarding_table():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
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
                """
            )

            cur.execute(
                """
                ALTER TABLE onboarding
                ADD COLUMN IF NOT EXISTS responsible TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE onboarding
                ADD COLUMN IF NOT EXISTS deadline TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE onboarding
                ADD COLUMN IF NOT EXISTS status TEXT
                DEFAULT 'Δεν ξεκίνησε'
                """
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# CREATE ONBOARDING
# ============================================================

def create_onboarding(
    employee_id,
    start_date,
    responsible=None,
    deadline=None,
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO onboarding (
                    employee_id,
                    start_date,
                    responsible,
                    deadline,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    employee_id,
                    start_date,
                    responsible,
                    deadline,
                    "Δεν ξεκίνησε",
                ),
            )

            result = cur.fetchone()

        conn.commit()

        return result["id"]

    finally:

        conn.close()


# ============================================================
# GET ONBOARDING
# ============================================================

def get_onboarding():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    o.*,
                    e.first_name,
                    e.last_name,
                    e.email AS employee_email,
                    e.position,
                    e.department
                FROM onboarding o
                JOIN employees e
                    ON e.id = o.employee_id
                ORDER BY o.id DESC
                """
            )

            return cur.fetchall()

    finally:

        conn.close()


# ============================================================
# UPDATE ONBOARDING
# ============================================================

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

    values = [
        contract,
        documents,
        email,
        equipment,
        system_access,
        training,
        manager_meeting,
    ]

    completed = sum(
        int(bool(value))
        for value in values
    )

    if completed == 7:

        status = "Ολοκληρώθηκε"

    elif completed > 0:

        status = "Σε εξέλιξη"

    else:

        status = "Δεν ξεκίνησε"

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
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
                """,
                (
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
                ),
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# LEAVE TABLE
# ============================================================

def create_leave_table():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leaves (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL,
                    leave_type TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    reason TEXT,
                    status TEXT DEFAULT 'Εκκρεμεί',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id)
                    REFERENCES employees(id)
                    ON DELETE CASCADE
                )
                """
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# ADD LEAVE
# ============================================================

def add_leave(
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason=None,
    status="Εκκρεμεί",
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO leaves (
                    employee_id,
                    leave_type,
                    start_date,
                    end_date,
                    reason,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    employee_id,
                    leave_type,
                    start_date,
                    end_date,
                    reason,
                    status,
                ),
            )

            result = cur.fetchone()

        conn.commit()

        return result["id"]

    finally:

        conn.close()


# ============================================================
# GET LEAVES
# ============================================================

def get_leaves():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    l.*,
                    e.first_name,
                    e.last_name,
                    e.email AS employee_email,
                    e.department,
                    e.position
                FROM leaves l
                JOIN employees e
                    ON e.id = l.employee_id
                ORDER BY l.id DESC
                """
            )

            return cur.fetchall()

    finally:

        conn.close()


# ============================================================
# UPDATE LEAVE STATUS
# ============================================================

def update_leave_status(
    leave_id,
    status,
):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE leaves
                SET status = %s
                WHERE id = %s
                """,
                (
                    status,
                    leave_id,
                ),
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# HR STATISTICS
# ============================================================

def get_hr_statistics():

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_employees,
                    COUNT(*) FILTER (
                        WHERE status = 'Ενεργός'
                    ) AS active_employees,
                    COUNT(*) FILTER (
                        WHERE status = 'Ανενεργός'
                    ) AS inactive_employees
                FROM employees
                """
            )

            result = cur.fetchone()

            return {
                "total_employees": (
                    result.get(
                        "total_employees"
                    )
                    or 0
                ),
                "active_employees": (
                    result.get(
                        "active_employees"
                    )
                    or 0
                ),
                "inactive_employees": (
                    result.get(
                        "inactive_employees"
                    )
                    or 0
                ),
            }

    finally:

        conn.close()


# ============================================================
# TIME TO HIRE
# ============================================================

def get_time_to_hire_stats():

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

            application_date = row.get(
                "application_date"
            )

            hired_at = row.get(
                "hired_at"
            )

            if not application_date or not hired_at:
                continue

            # Application Date
            if isinstance(
                application_date,
                str,
            ):

                application_date_obj = (
                    datetime.strptime(
                        application_date[:10],
                        "%Y-%m-%d",
                    ).date()
                )

            elif isinstance(
                application_date,
                datetime,
            ):

                application_date_obj = (
                    application_date.date()
                )

            else:

                application_date_obj = (
                    application_date
                )

            # Hired Date
            if isinstance(
                hired_at,
                datetime,
            ):

                hired_date_obj = hired_at.date()

            elif isinstance(
                hired_at,
                str,
            ):

                hired_date_obj = (
                    datetime.fromisoformat(
                        hired_at
                    ).date()
                )

            else:

                hired_date_obj = hired_at

            days_to_hire = (
                hired_date_obj
                - application_date_obj
            ).days

            if days_to_hire >= 0:

                results.append(
                    {
                        "id": row.get(
                            "id"
                        ),
                        "first_name": row.get(
                            "first_name"
                        ),
                        "last_name": row.get(
                            "last_name"
                        ),
                        "position": row.get(
                            "position"
                        ),
                        "application_date": (
                            application_date_obj
                        ),
                        "hired_date": (
                            hired_date_obj
                        ),
                        "days_to_hire": (
                            days_to_hire
                        ),
                    }
                )

        return results

    finally:

        conn.close()