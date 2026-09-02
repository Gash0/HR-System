import streamlit as st
import psycopg
from psycopg.rows import dict_row


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    return psycopg.connect(
        st.secrets["database"]["url"],
        row_factory=dict_row,
        connect_timeout=10
    )


# ==========================================
# TEST CONNECTION
# ==========================================

def test_postgres_connection():
    connection = get_connection()
    connection.close()
    return True


# ==========================================
# EMPLOYEES
# ==========================================

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
    connection.close()


def add_employee(
    first_name,
    last_name,
    email,
    phone,
    position,
    department,
    hire_date,
    status
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
        status
    ))

    connection.commit()
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

    connection.close()
    return employees


def get_employee_by_email(email):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM employees
        WHERE email = %s
        LIMIT 1
    """, (email,))

    employee = cursor.fetchone()

    connection.close()
    return employee


def delete_employee(employee_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = %s
    """, (employee_id,))

    connection.commit()
    connection.close()


# ==========================================
# RECRUITMENT
# ==========================================

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

    connection.commit()
    connection.close()


def add_candidate(
    first_name,
    last_name,
    email,
    phone,
    position,
    application_date,
    status
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
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        first_name,
        last_name,
        email,
        phone,
        position,
        application_date,
        status
    ))

    connection.commit()
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

    connection.close()
    return candidates


# ==========================================
# ONBOARDING
# ==========================================

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
            FOREIGN KEY (employee_id)
                REFERENCES employees(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def create_onboarding(employee_id, start_date):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO onboarding (
            employee_id,
            start_date
        )
        VALUES (%s, %s)
    """, (
        employee_id,
        start_date
    ))

    connection.commit()
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
    manager_meeting
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE onboarding
        SET
            contract = %s,
            documents = %s,
            email = %s,
            equipment = %s,
            system_access = %s,
            training = %s,
            manager_meeting = %s
        WHERE id = %s
    """, (
        contract,
        documents,
        email,
        equipment,
        system_access,
        training,
        manager_meeting,
        onboarding_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# LEAVES
# ==========================================

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
    connection.close()


def add_leave(
    employee_id,
    leave_type,
    start_date,
    end_date,
    reason,
    status="Εκκρεμεί"
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
        status
    ))

    connection.commit()
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
        leave_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# HR STATISTICS
# ==========================================

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

    connection.close()

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_candidates": total_candidates,
        "hired_candidates": hired_candidates,
        "total_leaves": total_leaves,
        "pending_leaves": pending_leaves
    }