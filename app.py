import os
from datetime import date, datetime

import pandas as pd
import altair as alt
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
    update_candidate,
    get_candidate_history,
    create_onboarding_table,
    create_onboarding,
    get_onboarding,
    update_onboarding,
    create_leave_table,
    add_leave,
    get_leaves,
    update_leave_status,
    get_hr_statistics,
    get_time_to_hire_stats,
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
# PREMIUM UI / THEME
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --hr-primary: #1f5eff;
        --hr-primary-dark: #1748c7;
        --hr-soft: #eef4ff;
        --hr-bg: #f6f8fc;
        --hr-card: #ffffff;
        --hr-text: #162033;
        --hr-muted: #6b7280;
        --hr-border: #e5e9f2;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, rgba(31,94,255,0.06), transparent 30%),
            var(--hr-bg);
        color: var(--hr-text);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
        color: var(--hr-text);
    }

    h1 {
        font-weight: 800 !important;
        margin-bottom: 0.35rem !important;
    }

    h2, h3 {
        font-weight: 700 !important;
    }

    p, label, .stCaption {
        color: var(--hr-muted);
    }

    hr {
        border-color: var(--hr-border) !important;
        margin: 1.5rem 0 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1f3d 0%, #152a50 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }

    [data-testid="stSidebar"] .stCaption {
        color: #aebbd0 !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 10px;
        padding: 0.35rem 0.5rem;
        transition: all 0.18s ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.08);
        transform: translateX(2px);
    }

    [data-testid="stMetric"] {
        background: var(--hr-card);
        border: 1px solid var(--hr-border);
        border-radius: 16px;
        padding: 1rem 1.05rem;
        min-height: 118px;
        box-shadow: 0 6px 24px rgba(31, 41, 55, 0.05);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(31, 41, 55, 0.09);
    }

    [data-testid="stMetricLabel"] {
        font-weight: 600;
        color: var(--hr-muted);
    }

    [data-testid="stMetricValue"] {
        font-weight: 800;
        color: var(--hr-text);
    }

    [data-testid="stForm"] {
        background: var(--hr-card);
        border: 1px solid var(--hr-border);
        border-radius: 16px;
        padding: 1.1rem 1.2rem 0.4rem 1.2rem;
        box-shadow: 0 5px 18px rgba(31, 41, 55, 0.04);
    }

    [data-testid="stExpander"] {
        background: var(--hr-card);
        border: 1px solid var(--hr-border);
        border-radius: 14px;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border-color: var(--hr-border) !important;
        background: var(--hr-card);
        box-shadow: 0 4px 16px rgba(31, 41, 55, 0.035);
    }

    .stTextInput input,
    .stTextArea textarea,
    .stDateInput input,
    [data-baseweb="select"] > div {
        border-radius: 10px !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        transition: all 0.18s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, var(--hr-primary), var(--hr-primary-dark)) !important;
        border: none !important;
        box-shadow: 0 5px 14px rgba(31, 94, 255, 0.22);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        background: #edf1f8;
        padding: 0.35rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 9px;
        padding: 0.45rem 0.9rem;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 2px 8px rgba(31,41,55,0.08);
    }

    [data-testid="stDataFrame"] {
        background: var(--hr-card);
        border: 1px solid var(--hr-border);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(31, 41, 55, 0.035);
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
        border-width: 1px;
    }

    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"] {
        background: var(--hr-card);
        border: 1px solid var(--hr-border);
        border-radius: 16px;
        padding: 0.55rem;
        box-shadow: 0 4px 16px rgba(31, 41, 55, 0.035);
    }

    ::-webkit-scrollbar {
        width: 9px;
        height: 9px;
    }

    ::-webkit-scrollbar-thumb {
        background: #c4ccda;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1.25rem;
        }

        [data-testid="stMetric"] {
            min-height: 100px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GOOGLE LOGIN
# ============================================================

if not st.user.is_logged_in:
    st.title("🔐 AI HR System")
    st.subheader("Σύνδεση στο HR System")
    st.write("Συνδέσου με Google για να συνεχίσεις.")
    st.button("🔑 Σύνδεση με Google", on_click=st.login)
    st.stop()


# ============================================================
# USER / ROLE
# ============================================================

user_email = (st.user.email or "").strip().lower()

def _get_secret_list(key):
    value = st.secrets.get("roles", {}).get(key, [])
    if isinstance(value, str):
        return [value.strip().lower()]
    return [str(item).strip().lower() for item in value]

admin_emails = _get_secret_list("admin_emails")
hr_emails = _get_secret_list("hr_emails")

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
# SIDEBAR
# ============================================================

display_name = getattr(st.user, "name", None) or user_email

st.sidebar.success(f"👤 {display_name}")
st.sidebar.info(f"Ρόλος: {user_role}")

if st.sidebar.button("🚪 Αποσύνδεση"):
    st.logout()

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

page = st.sidebar.radio("Μενού", menu_options)
st.sidebar.markdown("---")
st.sidebar.caption("AI HR Management System")


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
# HELPERS
# ============================================================

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



st.markdown(
    """
    <style>
    /* Dashboard 4.0 */
    .hr-hero {
        padding: 1.45rem 1.6rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #102a56 0%, #1f5eff 100%);
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 14px 34px rgba(31, 94, 255, 0.18);
    }

    .hr-hero h1 {
        color: white !important;
        margin: 0 !important;
        font-size: 2rem !important;
    }

    .hr-hero p {
        color: rgba(255,255,255,0.82) !important;
        margin: 0.45rem 0 0 0 !important;
        font-size: 0.98rem;
    }

    .hr-section-label {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        background: #eaf1ff;
        color: #1f5eff;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .hr-section-title {
        font-size: 1.28rem;
        font-weight: 800;
        color: #162033;
        margin-bottom: 0.8rem;
    }

    .hr-panel {
        background: #ffffff;
        border: 1px solid #e5e9f2;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        box-shadow: 0 5px 18px rgba(31,41,55,0.04);
        margin-bottom: 0.75rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        width: 100% !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.14) !important;
        border-color: rgba(255,255,255,0.20) !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] p {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# ============================================================
# CHART HELPERS
# ============================================================

def render_horizontal_bar(data, category, value, title=None):
    if data is None or data.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return

    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
        .encode(
            x=alt.X(f"{value}:Q", title=None, axis=alt.Axis(grid=True, tickMinStep=1)),
            y=alt.Y(
                f"{category}:N",
                title=None,
                sort="-x",
                axis=alt.Axis(labelLimit=180),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title=category),
                alt.Tooltip(f"{value}:Q", title=value),
            ],
        )
        .properties(height=max(180, min(340, 42 * len(data))), title=title)
    )

    st.altair_chart(chart, use_container_width=True)


def render_donut(data, category, value, title=None):
    if data is None or data.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return

    chart = (
        alt.Chart(data)
        .mark_arc(innerRadius=62, outerRadius=95)
        .encode(
            theta=alt.Theta(f"{value}:Q"),
            color=alt.Color(
                f"{category}:N",
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title=category),
                alt.Tooltip(f"{value}:Q", title=value),
            ],
        )
        .properties(height=300, title=title)
    )

    st.altair_chart(chart, use_container_width=True)


def render_vertical_bar(data, category, value, title=None):
    if data is None or data.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return

    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=7, cornerRadiusTopRight=7)
        .encode(
            x=alt.X(
                f"{category}:N",
                title=None,
                sort=None,
                axis=alt.Axis(labelAngle=-20, labelLimit=120),
            ),
            y=alt.Y(
                f"{value}:Q",
                title=None,
                axis=alt.Axis(grid=True, tickMinStep=1),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title=category),
                alt.Tooltip(f"{value}:Q", title=value),
            ],
        )
        .properties(height=300, title=title)
    )

    st.altair_chart(chart, use_container_width=True)


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
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    employees = get_employees()
    candidates = get_candidates()
    leaves = get_leaves()
    onboarding_rows = get_onboarding()

    try:
        time_to_hire_data = get_time_to_hire_stats()
    except Exception:
        time_to_hire_data = []

    current_year = date.today().year

    st.markdown(
        f"""
        <div class="hr-hero">
            <h1>HR Overview</h1>
            <p>Καλώς ήρθες, {display_name}. Μια καθαρή εικόνα για ανθρώπους, προσλήψεις και HR λειτουργίες.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    departments = sorted({
        employee.get("department")
        for employee in employees
        if employee.get("department")
    })

    filter_col, info_col = st.columns([2.2, 1])

    with filter_col:
        department_filter = st.selectbox(
            "🏢 Τμήμα",
            ["Όλα"] + departments,
            key="dashboard_department_filter",
        )

    with info_col:
        st.info(f"📅 Αναφορά έτους: {current_year}")

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
        filtered_active / filtered_total * 100
        if filtered_total
        else 0
    )

    total_candidates = len(candidates)

    hired_candidates = sum(
        1
        for candidate in candidates
        if candidate.get("status") == "Προσλήφθηκε"
    )

    pending_leaves = sum(
        1
        for leave in leaves
        if leave.get("status") == "Εκκρεμεί"
    )

    st.markdown(
        '<span class="hr-section-label">Executive summary</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">Βασικοί δείκτες HR</div>',
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Εργαζόμενοι", filtered_total)
    k2.metric("✅ Ενεργοί", filtered_active)
    k3.metric("📋 Υποψήφιοι", total_candidates)
    k4.metric("⏳ Εκκρεμείς άδειες", pending_leaves)

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("❌ Ανενεργοί", filtered_inactive)
    k6.metric("🎯 Προσλήψεις", hired_candidates)
    k7.metric("🏖️ Αιτήσεις αδειών", len(leaves))
    k8.metric("📈 Active Rate", f"{active_rate:.1f}%")

    # ========================================================
    # WORKFORCE SNAPSHOT
    # ========================================================

    st.divider()
    st.markdown(
        '<span class="hr-section-label">Workforce</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">Εικόνα προσωπικού</div>',
        unsafe_allow_html=True,
    )

    workforce_left, workforce_right = st.columns(2)

    with workforce_left:
        st.markdown("#### 👥 Εργαζόμενοι ανά τμήμα")

        if filtered_employees:
            workforce_df = pd.DataFrame(filtered_employees)

            department_counts = (
                workforce_df["department"]
                .fillna("Χωρίς τμήμα")
                .replace("", "Χωρίς τμήμα")
                .value_counts()
                .rename_axis("Τμήμα")
                .reset_index(name="Εργαζόμενοι")
            )

            render_horizontal_bar(
                department_counts,
                "Τμήμα",
                "Εργαζόμενοι",
            )
        else:
            st.info("Δεν υπάρχουν εργαζόμενοι.")

    with workforce_right:
        st.markdown("#### 📊 Κατάσταση εργαζομένων")

        if filtered_employees:
            workforce_df = pd.DataFrame(filtered_employees)

            status_counts = (
                workforce_df["status"]
                .fillna("Άγνωστη κατάσταση")
                .value_counts()
                .rename_axis("Κατάσταση")
                .reset_index(name="Εργαζόμενοι")
            )

            render_donut(
                status_counts,
                "Κατάσταση",
                "Εργαζόμενοι",
            )
        else:
            st.info("Δεν υπάρχουν δεδομένα.")

    # ========================================================
    # EMPLOYEE TURNOVER
    # ========================================================

    st.divider()
    st.markdown(
        '<span class="hr-section-label">Retention</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">📉 Employee Turnover</div>',
        unsafe_allow_html=True,
    )

    year_start = date(current_year, 1, 1)
    departures_this_year = []

    for employee in filtered_employees:
        termination_value = employee.get("termination_date")

        if not termination_value:
            continue

        termination_date_obj = parse_date(termination_value)

        if termination_date_obj.year == current_year:
            departures_this_year.append(employee)

    headcount_start = 0

    for employee in filtered_employees:
        hire_value = employee.get("hire_date")

        if not hire_value:
            continue

        hire_date_obj = parse_date(hire_value)
        termination_value = employee.get("termination_date")

        termination_date_obj = (
            parse_date(termination_value)
            if termination_value
            else None
        )

        if (
            hire_date_obj < year_start
            and (
                termination_date_obj is None
                or termination_date_obj >= year_start
            )
        ):
            headcount_start += 1

    headcount_now = filtered_active

    # Για αξιόπιστο annual turnover χρειάζεται headcount στην αρχή του έτους.
    if headcount_start > 0:
        average_headcount = (headcount_start + headcount_now) / 2
        turnover_rate = (
            len(departures_this_year) / average_headcount * 100
            if average_headcount > 0
            else 0
        )
        turnover_display = f"{turnover_rate:.1f}%"
    else:
        turnover_rate = None
        turnover_display = "N/A"

    t1, t2, t3, t4 = st.columns(4)
    t1.metric(f"Turnover Rate {current_year}", turnover_display)
    t2.metric("Αποχωρήσεις", len(departures_this_year))
    t3.metric("Headcount αρχής έτους", headcount_start)
    t4.metric("Τωρινό Headcount", headcount_now)

    if headcount_start == 0:
        st.caption(
            "ℹ️ Το Turnover Rate εμφανίζεται N/A επειδή δεν υπάρχει διαθέσιμο "
            "headcount στην αρχή του έτους. Έτσι αποφεύγεται παραπλανητικό ποσοστό."
        )

    if departures_this_year:
        turnover_left, turnover_right = st.columns([1, 1.3])

        with turnover_left:
            st.markdown("#### Αποχωρήσεις ανά λόγο")

            reason_counts = {}

            for employee in departures_this_year:
                reason = employee.get("termination_reason") or "Δεν καταχωρήθηκε"
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

            reason_df = pd.DataFrame(
                {
                    "Λόγος": list(reason_counts.keys()),
                    "Αποχωρήσεις": list(reason_counts.values()),
                }
            )

            render_horizontal_bar(
                reason_df,
                "Λόγος",
                "Αποχωρήσεις",
            )

        with turnover_right:
            st.markdown("#### Πρόσφατες αποχωρήσεις")

            departure_rows = [
                {
                    "Εργαζόμενος": (
                        f"{employee.get('first_name', '')} "
                        f"{employee.get('last_name', '')}"
                    ).strip(),
                    "Τμήμα": employee.get("department") or "-",
                    "Αποχώρηση": format_date(
                        employee.get("termination_date")
                    ),
                    "Λόγος": employee.get("termination_reason") or "-",
                }
                for employee in departures_this_year
            ]

            st.dataframe(
                pd.DataFrame(departure_rows),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.success(f"✅ Δεν υπάρχουν καταχωρημένες αποχωρήσεις για το {current_year}.")

    # ========================================================
    # RECRUITMENT
    # ========================================================

    st.divider()
    st.markdown(
        '<span class="hr-section-label">Talent acquisition</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">🎯 Recruitment Performance</div>',
        unsafe_allow_html=True,
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
            for candidate in candidates
            if candidate.get("status") == status
        )
        for status in recruitment_statuses
    }

    interviews = recruitment_counts["Συνέντευξη"]
    offers = recruitment_counts["Προσφορά"]
    hired = recruitment_counts["Προσλήφθηκε"]

    hire_rate = (
        hired / total_candidates * 100
        if total_candidates
        else 0
    )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("📋 Υποψήφιοι", total_candidates)
    r2.metric("🗣️ Συνεντεύξεις", interviews)
    r3.metric("📨 Προσφορές", offers)
    r4.metric("🎯 Hire Rate", f"{hire_rate:.1f}%")

    recruitment_left, recruitment_right = st.columns([1.15, 1])

    with recruitment_left:
        st.markdown("#### Recruitment Pipeline")

        if candidates:
            pipeline_df = pd.DataFrame(
                {
                    "Στάδιο": recruitment_statuses,
                    "Υποψήφιοι": [
                        recruitment_counts[status]
                        for status in recruitment_statuses
                    ],
                }
            )

            render_horizontal_bar(
                pipeline_df,
                "Στάδιο",
                "Υποψήφιοι",
            )
        else:
            st.info("Δεν υπάρχουν υποψήφιοι.")

    with recruitment_right:
        st.markdown("#### ⏱️ Time to Hire")

        if time_to_hire_data:
            average_time_to_hire = round(
                sum(
                    item["days_to_hire"]
                    for item in time_to_hire_data
                )
                / len(time_to_hire_data),
                1,
            )

            fastest_hire = min(
                item["days_to_hire"]
                for item in time_to_hire_data
            )

            slowest_hire = max(
                item["days_to_hire"]
                for item in time_to_hire_data
            )

            th1, th2, th3 = st.columns(3)
            th1.metric("Μέσο", f"{average_time_to_hire} ημ.")
            th2.metric("Ταχύτερο", f"{fastest_hire} ημ.")
            th3.metric("Μέγιστο", f"{slowest_hire} ημ.")

            time_to_hire_df = pd.DataFrame(
                [
                    {
                        "Υποψήφιος": (
                            f"{item.get('first_name', '')} "
                            f"{item.get('last_name', '')}"
                        ).strip(),
                        "Θέση": item.get("position") or "-",
                        "Ημέρες": item["days_to_hire"],
                    }
                    for item in time_to_hire_data
                ]
            )

            st.dataframe(
                time_to_hire_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Δεν υπάρχουν ακόμη αρκετά δεδομένα.")

    # ========================================================
    # HR OPERATIONS
    # ========================================================

    st.divider()
    st.markdown(
        '<span class="hr-section-label">Operations</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">HR Operations</div>',
        unsafe_allow_html=True,
    )

    operations_left, operations_right = st.columns(2)

    with operations_left:
        st.markdown("#### 🏖️ Άδειες")

        if leaves:
            leave_df = pd.DataFrame(leaves)

            approved = int(
                (leave_df["status"] == "Εγκρίθηκε").sum()
            )
            rejected = int(
                (leave_df["status"] == "Απορρίφθηκε").sum()
            )
            pending = int(
                (leave_df["status"] == "Εκκρεμεί").sum()
            )

            l1, l2, l3 = st.columns(3)
            l1.metric("✅ Εγκεκριμένες", approved)
            l2.metric("⏳ Εκκρεμείς", pending)
            l3.metric("❌ Απορριφθείσες", rejected)

            leave_counts = (
                leave_df["status"]
                .fillna("Άγνωστη κατάσταση")
                .value_counts()
                .rename_axis("Κατάσταση")
                .reset_index(name="Αιτήσεις")
            )

            render_donut(
                leave_counts,
                "Κατάσταση",
                "Αιτήσεις",
            )
        else:
            st.info("Δεν υπάρχουν αιτήματα άδειας.")

    with operations_right:
        st.markdown("#### 🚀 Onboarding")

        if onboarding_rows:
            onboarding_completed = 0
            onboarding_in_progress = 0
            onboarding_not_started = 0

            for row in onboarding_rows:
                completed = sum(
                    int(bool(row.get(key)))
                    for key in [
                        "contract",
                        "documents",
                        "email",
                        "equipment",
                        "system_access",
                        "training",
                        "manager_meeting",
                    ]
                )

                if completed == 7:
                    onboarding_completed += 1
                elif completed > 0:
                    onboarding_in_progress += 1
                else:
                    onboarding_not_started += 1

            o1, o2, o3 = st.columns(3)
            o1.metric("Δεν ξεκίνησε", onboarding_not_started)
            o2.metric("Σε εξέλιξη", onboarding_in_progress)
            o3.metric("Ολοκληρώθηκε", onboarding_completed)

            onboarding_chart = pd.DataFrame(
                {
                    "Κατάσταση": [
                        "Δεν ξεκίνησε",
                        "Σε εξέλιξη",
                        "Ολοκληρώθηκε",
                    ],
                    "Πλήθος": [
                        onboarding_not_started,
                        onboarding_in_progress,
                        onboarding_completed,
                    ],
                }
            )

            render_vertical_bar(
                onboarding_chart,
                "Κατάσταση",
                "Πλήθος",
            )
        else:
            st.info("Δεν υπάρχουν onboarding διαδικασίες.")

    # ========================================================
    # RECENT EMPLOYEES
    # ========================================================

    st.divider()
    st.markdown(
        '<span class="hr-section-label">Directory</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hr-section-title">👤 Πρόσφατοι εργαζόμενοι</div>',
        unsafe_allow_html=True,
    )

    if filtered_employees:
        recent_rows = [
            {
                "Εργαζόμενος": (
                    f"{employee.get('first_name', '')} "
                    f"{employee.get('last_name', '')}"
                ).strip(),
                "Email": employee.get("email") or "-",
                "Θέση": employee.get("position") or "-",
                "Τμήμα": employee.get("department") or "-",
                "Κατάσταση": employee.get("status") or "-",
                "Πρόσληψη": format_date(employee.get("hire_date")),
            }
            for employee in filtered_employees[:10]
        ]

        st.dataframe(
            pd.DataFrame(recent_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")


# ============================================================
# EMPLOYEE PROFILE
# ============================================================

elif page == "👤 Το προφίλ μου":

    st.title("👤 Το προφίλ μου")
    employee = get_employee_by_email(user_email)

    if employee is None:
        st.warning("Δεν βρέθηκε εργαζόμενος με αυτό το Google email. Επικοινώνησε με το HR.")
    else:
        st.subheader(f"{employee['first_name']} {employee['last_name']}")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Όνομα:**", employee["first_name"] or "-")
            st.write("**Επώνυμο:**", employee["last_name"] or "-")
            st.write("**Email:**", employee["email"] or "-")
            st.write("**Τηλέφωνο:**", employee["phone"] or "-")
        with c2:
            st.write("**Θέση:**", employee["position"] or "-")
            st.write("**Τμήμα:**", employee["department"] or "-")
            st.write("**Ημερομηνία πρόσληψης:**", employee["hire_date"] or "-")
            st.write("**Κατάσταση:**", employee["status"] or "-")


# ============================================================
# EMPLOYEE LEAVES
# ============================================================

elif page == "🏖️ Οι άδειές μου":

    st.title("🏖️ Οι άδειές μου")
    employee = get_employee_by_email(user_email)

    if employee is None:
        st.warning("Δεν βρέθηκε εργαζόμενος με αυτό το Google email. Επικοινώνησε με το HR.")
    else:
        leaves = [
            leave for leave in get_leaves()
            if leave["employee_id"] == employee["id"]
        ]

        st.subheader("📋 Ιστορικό αδειών")
        if leaves:
            rows = [{
                "Τύπος": l["leave_type"],
                "Από": l["start_date"],
                "Έως": l["end_date"],
                "Αιτιολογία": l["reason"] or "-",
                "Κατάσταση": l["status"],
            } for l in leaves]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν καταχωρημένες άδειες.")

        st.divider()
        st.subheader("➕ Νέο αίτημα άδειας")
        with st.form("employee_leave_request"):
            leave_type = st.selectbox("Τύπος άδειας", [
                "Κανονική", "Αναρρωτική", "Άδεια άνευ αποδοχών", "Ειδική"
            ])
            c1, c2 = st.columns(2)
            with c1:
                start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            with c2:
                end_date = st.date_input("Ημερομηνία λήξης", value=date.today(), format="DD/MM/YYYY")
            reason = st.text_area("Αιτιολογία")
            submitted = st.form_submit_button("📤 Υποβολή αιτήματος")

            if submitted:
                if end_date < start_date:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την ημερομηνία έναρξης.")
                else:
                    add_leave(
                        employee["id"], leave_type,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        reason, "Εκκρεμεί"
                    )
                    st.success("✅ Το αίτημα άδειας υποβλήθηκε.")
                    st.rerun()


# ============================================================
# EMPLOYEES
# ============================================================

elif page == "👥 Εργαζόμενοι":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("👥 Διαχείριση Εργαζομένων")

    st.subheader("➕ Προσθήκη εργαζομένου")
    with st.form("employee_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Όνομα")
            last_name = st.text_input("Επώνυμο")
            email = st.text_input("Email")
            phone = st.text_input("Τηλέφωνο")
        with c2:
            position = st.text_input("Θέση")
            department = st.text_input("Τμήμα")
            hire_date = st.date_input("Ημερομηνία πρόσληψης", value=date.today(), format="DD/MM/YYYY")
            status = st.selectbox("Κατάσταση", ["Ενεργός", "Ανενεργός", "Σε άδεια"])

        submitted = st.form_submit_button("💾 Αποθήκευση εργαζομένου")
        if submitted:
            if not first_name.strip() or not last_name.strip():
                st.error("Το Όνομα και το Επώνυμο είναι υποχρεωτικά.")
            else:
                try:
                    add_employee(
                        first_name.strip(), last_name.strip(),
                        email.strip().lower() or None,
                        phone.strip(), position.strip(), department.strip(),
                        hire_date.strftime("%Y-%m-%d"), status
                    )
                    st.success("✅ Ο εργαζόμενος προστέθηκε.")
                    st.rerun()
                except Exception as e:
                    if "UniqueViolation" in str(e) or "duplicate key" in str(e).lower():
                        st.error("❌ Υπάρχει ήδη εργαζόμενος με αυτό το email.")
                    else:
                        st.error(f"❌ Σφάλμα αποθήκευσης: {e}")

    st.divider()
    st.subheader("📋 Λίστα εργαζομένων")
    employees = get_employees()

    if employees:
        search_text = st.text_input("🔎 Αναζήτηση", placeholder="Όνομα, επώνυμο ή email...")
        dept_options = sorted({e.get("department") for e in employees if e.get("department")})
        selected_department = st.selectbox("🏢 Τμήμα", ["Όλα"] + dept_options)
        selected_status = st.selectbox("📌 Κατάσταση", ["Όλες", "Ενεργός", "Ανενεργός", "Σε άδεια"])

        filtered_employees = employees
        if search_text.strip():
            q = search_text.strip().lower()
            filtered_employees = [
                e for e in filtered_employees
                if q in (e.get("first_name") or "").lower()
                or q in (e.get("last_name") or "").lower()
                or q in (e.get("email") or "").lower()
            ]
        if selected_department != "Όλα":
            filtered_employees = [e for e in filtered_employees if e.get("department") == selected_department]
        if selected_status != "Όλες":
            filtered_employees = [e for e in filtered_employees if e.get("status") == selected_status]

        st.caption(f"Βρέθηκαν {len(filtered_employees)} εργαζόμενοι.")

        table = [{
            "ID": e["id"],
            "Όνομα": e["first_name"],
            "Επώνυμο": e["last_name"],
            "Email": e["email"],
            "Τηλέφωνο": e["phone"],
            "Θέση": e["position"],
            "Τμήμα": e["department"],
            "Ημερομηνία πρόσληψης": format_date(e.get("hire_date")),
            "Κατάσταση": e["status"],
            "Ημερομηνία αποχώρησης": format_date(e.get("termination_date")),
            "Λόγος αποχώρησης": e.get("termination_reason") or "-",
        } for e in filtered_employees]
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("👤 Employee Profile")

        if filtered_employees:
            profile_options = {
                f'{e["first_name"]} {e["last_name"]} — {e["position"] or "Χωρίς θέση"} (ID: {e["id"]})': e
                for e in filtered_employees
            }
            profile_label = st.selectbox("Επίλεξε εργαζόμενο", list(profile_options.keys()), key="employee_profile_selector")
            selected_employee = profile_options[profile_label]

            all_leaves = get_leaves()
            all_onboarding = get_onboarding()
            employee_leaves = [l for l in all_leaves if l["employee_id"] == selected_employee["id"]]
            employee_onboarding = [o for o in all_onboarding if o["employee_id"] == selected_employee["id"]]
            approved = sum(1 for l in employee_leaves if l["status"] == "Εγκρίθηκε")
            pending = sum(1 for l in employee_leaves if l["status"] == "Εκκρεμεί")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📌 Κατάσταση", selected_employee["status"] or "-")
            with c2:
                st.metric("🏖️ Σύνολο αδειών", len(employee_leaves))
            with c3:
                st.metric("✅ Εγκεκριμένες", approved)
            with c4:
                st.metric("⏳ Εκκρεμείς", pending)

            tab1, tab2, tab3, tab4 = st.tabs(["👤 Στοιχεία", "🏖️ Άδειες", "🚀 Onboarding", "📋 Ιστορικό"])

            with tab1:
                with st.form(f"edit_employee_{selected_employee['id']}"):
                    c1, c2 = st.columns(2)

                    with c1:
                        edit_first = st.text_input(
                            "Όνομα",
                            value=selected_employee["first_name"] or "",
                        )
                        edit_last = st.text_input(
                            "Επώνυμο",
                            value=selected_employee["last_name"] or "",
                        )
                        edit_email = st.text_input(
                            "Email",
                            value=selected_employee["email"] or "",
                        )
                        edit_phone = st.text_input(
                            "Τηλέφωνο",
                            value=selected_employee["phone"] or "",
                        )

                    with c2:
                        edit_position = st.text_input(
                            "Θέση",
                            value=selected_employee["position"] or "",
                        )
                        edit_department = st.text_input(
                            "Τμήμα",
                            value=selected_employee["department"] or "",
                        )
                        edit_hire = st.date_input(
                            "Ημερομηνία πρόσληψης",
                            value=parse_date(selected_employee.get("hire_date")),
                            format="DD/MM/YYYY",
                        )

                        status_options = [
                            "Ενεργός",
                            "Ανενεργός",
                            "Σε άδεια",
                        ]

                        current_status = (
                            selected_employee.get("status")
                            or "Ενεργός"
                        )

                        edit_status = st.selectbox(
                            "Κατάσταση",
                            status_options,
                            index=(
                                status_options.index(current_status)
                                if current_status in status_options
                                else 0
                            ),
                        )

                    st.markdown("#### 📉 Στοιχεία αποχώρησης")
                    st.caption(
                        "Τα παρακάτω αποθηκεύονται μόνο όταν η κατάσταση είναι «Ανενεργός»."
                    )

                    term1, term2 = st.columns(2)

                    termination_date_value = term1.date_input(
                        "Ημερομηνία αποχώρησης",
                        value=parse_date(
                            selected_employee.get("termination_date"),
                            date.today(),
                        ),
                        format="DD/MM/YYYY",
                    )

                    termination_reasons = [
                        "Παραίτηση",
                        "Απόλυση",
                        "Λήξη σύμβασης",
                        "Συνταξιοδότηση",
                        "Άλλο",
                    ]

                    current_reason = selected_employee.get(
                        "termination_reason"
                    )

                    reason_index = (
                        termination_reasons.index(current_reason)
                        if current_reason in termination_reasons
                        else 0
                    )

                    termination_reason_value = term2.selectbox(
                        "Λόγος αποχώρησης",
                        termination_reasons,
                        index=reason_index,
                    )

                    save = st.form_submit_button(
                        "💾 Αποθήκευση αλλαγών"
                    )

                    if save:
                        if (
                            edit_status == "Ανενεργός"
                            and termination_date_value < edit_hire
                        ):
                            st.error(
                                "Η ημερομηνία αποχώρησης δεν μπορεί να είναι πριν από την ημερομηνία πρόσληψης."
                            )
                        else:
                            try:
                                update_employee(
                                    selected_employee["id"],
                                    edit_first.strip(),
                                    edit_last.strip(),
                                    edit_email.strip().lower() or None,
                                    edit_phone.strip(),
                                    edit_position.strip(),
                                    edit_department.strip(),
                                    edit_hire.strftime("%Y-%m-%d"),
                                    edit_status,
                                    (
                                        termination_date_value.strftime("%Y-%m-%d")
                                        if edit_status == "Ανενεργός"
                                        else None
                                    ),
                                    (
                                        termination_reason_value
                                        if edit_status == "Ανενεργός"
                                        else None
                                    ),
                                )

                                st.success(
                                    "✅ Τα στοιχεία ενημερώθηκαν."
                                )
                                st.rerun()

                            except Exception as e:
                                if (
                                    "UniqueViolation" in str(e)
                                    or "duplicate key" in str(e).lower()
                                ):
                                    st.error(
                                        "❌ Υπάρχει ήδη εργαζόμενος με αυτό το email."
                                    )
                                else:
                                    st.error(
                                        f"❌ Σφάλμα ενημέρωσης: {e}"
                                    )

            with tab2:
                if employee_leaves:
                    rows = [{
                        "Τύπος": l["leave_type"], "Από": l["start_date"], "Έως": l["end_date"],
                        "Αιτιολογία": l["reason"] or "-", "Κατάσταση": l["status"]
                    } for l in employee_leaves]
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("Δεν υπάρχουν άδειες.")

            with tab3:
                if employee_onboarding:
                    for item in employee_onboarding:
                        completed = sum(bool(item[k]) for k in ["contract", "documents", "email", "equipment", "system_access", "training", "manager_meeting"])
                        st.write(f"**Ημερομηνία έναρξης:** {item['start_date'] or '-'}")
                        st.progress(completed / 7)
                        st.write(f"**Ολοκλήρωση:** {completed}/7 ({completed / 7 * 100:.0f}%)")
                        st.write(f"📄 Σύμβαση: {'✅' if item['contract'] else '❌'}")
                        st.write(f"📁 Έγγραφα: {'✅' if item['documents'] else '❌'}")
                        st.write(f"📧 Email: {'✅' if item['email'] else '❌'}")
                        st.write(f"💻 Εξοπλισμός: {'✅' if item['equipment'] else '❌'}")
                        st.write(f"🔐 Πρόσβαση: {'✅' if item['system_access'] else '❌'}")
                        st.write(f"🎓 Εκπαίδευση: {'✅' if item['training'] else '❌'}")
                        st.write(f"🤝 Manager Meeting: {'✅' if item['manager_meeting'] else '❌'}")
                        st.divider()
                else:
                    st.info("Δεν υπάρχει onboarding.")

            with tab4:
                st.write(f"📅 Ημερομηνία πρόσληψης: {selected_employee['hire_date'] or '-'}")
                st.write(f"🏢 Τμήμα: {selected_employee['department'] or '-'}")
                st.write(f"💼 Θέση: {selected_employee['position'] or '-'}")
                st.write(f"📌 Κατάσταση: {selected_employee['status'] or '-'}")
                st.write(
                    f"📉 Ημερομηνία αποχώρησης: "
                    f"{format_date(selected_employee.get('termination_date'))}"
                )
                st.write(
                    f"📝 Λόγος αποχώρησης: "
                    f"{selected_employee.get('termination_reason') or '-'}"
                )
                st.write(f"🏖️ Αιτήματα άδειας: {len(employee_leaves)}")
                st.write(f"✅ Εγκεκριμένες άδειες: {approved}")
                st.write(f"⏳ Εκκρεμή αιτήματα: {pending}")
                st.write(f"🚀 Onboarding: {'Υπάρχει' if employee_onboarding else 'Δεν υπάρχει'}")

        st.divider()
        st.subheader("🗑️ Διαγραφή εργαζομένου")
        delete_options = {
            f'{e["first_name"]} {e["last_name"]} (ID: {e["id"]})': e["id"]
            for e in employees
        }
        selected_delete = st.selectbox("Επίλεξε εργαζόμενο", list(delete_options.keys()), key="delete_employee_selector")
        if st.button("🗑️ Διαγραφή εργαζομένου"):
            delete_employee(delete_options[selected_delete])
            st.success("✅ Ο εργαζόμενος διαγράφηκε.")
            st.rerun()
    else:
        st.info("Δεν υπάρχουν εργαζόμενοι.")


# ============================================================
# RECRUITMENT
# ============================================================

elif page == "📋 Recruitment":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("📋 Recruitment")
    st.caption("Διαχείριση υποψηφίων και pipeline προσλήψεων.")

    candidates = get_candidates()
    pipeline_statuses = [
        "Νέα αίτηση", "Σε αξιολόγηση", "Συνέντευξη",
        "Προσφορά", "Προσλήφθηκε", "Απορρίφθηκε"
    ]

    st.subheader("➕ Νέος υποψήφιος")
    with st.form("candidate_form"):
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("Όνομα")
            last_name = st.text_input("Επώνυμο")
            email = st.text_input("Email")
            phone = st.text_input("Τηλέφωνο")
        with c2:
            position = st.text_input("Θέση εργασίας")
            application_date = st.date_input("Ημερομηνία αίτησης", value=date.today(), format="DD/MM/YYYY")
            recruiter = st.text_input("👤 Recruiter")
            initial_status = st.selectbox("Κατάσταση", pipeline_statuses)
        submitted = st.form_submit_button("💾 Προσθήκη υποψηφίου")

        if submitted:
            if not first_name.strip() or not last_name.strip():
                st.error("Το Όνομα και το Επώνυμο είναι υποχρεωτικά.")
            else:
                add_candidate(
                    first_name.strip(), last_name.strip(), email.strip() or None,
                    phone.strip(), position.strip(), application_date.strftime("%Y-%m-%d"),
                    initial_status, None, None, None, recruiter.strip() or None
                )
                st.success("✅ Ο υποψήφιος προστέθηκε.")
                st.rerun()

    st.divider()
    st.subheader("🎯 Recruitment Pipeline")
    pipeline_counts = {status: 0 for status in pipeline_statuses}
    for candidate in candidates:
        if candidate.get("status") in pipeline_counts:
            pipeline_counts[candidate["status"]] += 1
    cols = st.columns(6)
    for i, status in enumerate(pipeline_statuses):
        with cols[i]:
            st.metric(status, pipeline_counts[status])

    st.divider()
    st.subheader("🔎 Αναζήτηση υποψηφίων")
    c1, c2 = st.columns(2)
    with c1:
        search_text = st.text_input("Όνομα, επώνυμο ή email", placeholder="Αναζήτηση...")
    with c2:
        status_filter = st.selectbox("📌 Κατάσταση", ["Όλες"] + pipeline_statuses)

    filtered_candidates = candidates
    if search_text.strip():
        q = search_text.strip().lower()
        filtered_candidates = [
            c for c in filtered_candidates
            if q in (c.get("first_name") or "").lower()
            or q in (c.get("last_name") or "").lower()
            or q in (c.get("email") or "").lower()
        ]
    if status_filter != "Όλες":
        filtered_candidates = [c for c in filtered_candidates if c.get("status") == status_filter]

    st.caption(f"Βρέθηκαν {len(filtered_candidates)} υποψήφιοι.")

    st.subheader("📊 Pipeline")
    visible_pipeline = ["Νέα αίτηση", "Σε αξιολόγηση", "Συνέντευξη", "Προσφορά", "Προσλήφθηκε"]
    columns = st.columns(len(visible_pipeline))
    for i, stage in enumerate(visible_pipeline):
        with columns[i]:
            st.markdown(f"### {stage}")
            stage_candidates = [c for c in filtered_candidates if c.get("status") == stage]
            if not stage_candidates:
                st.caption("Κανένας υποψήφιος")
            for candidate in stage_candidates:
                with st.container(border=True):
                    st.write(f"**{candidate['first_name']} {candidate['last_name']}**")
                    st.caption(candidate.get("position") or "Χωρίς θέση")
                    if candidate.get("email"):
                        st.write(f"📧 {candidate['email']}")
                    if candidate.get("rating"):
                        st.write(f"⭐ {candidate['rating']}/5")

    st.divider()
    st.subheader("⚙️ Διαχείριση υποψηφίου")

    if filtered_candidates:
        options = {
            f'{c["first_name"]} {c["last_name"]} (ID: {c["id"]})': c
            for c in filtered_candidates
        }
        selected_label = st.selectbox("Επίλεξε υποψήφιο", list(options.keys()), key="candidate_selector")
        candidate = options[selected_label]

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"📧 **Email:** {candidate.get('email') or '-'}")
            st.write(f"📞 **Τηλέφωνο:** {candidate.get('phone') or '-'}")
            st.write(f"💼 **Θέση:** {candidate.get('position') or '-'}")
        with c2:
            st.write(f"📅 **Αίτηση:** {candidate.get('application_date') or '-'}")
            st.write(f"👤 **Recruiter:** {candidate.get('recruiter') or '-'}")

        with st.form(f"candidate_management_{candidate['id']}"):
            new_status = st.selectbox(
                "🔄 Κατάσταση",
                pipeline_statuses,
                index=pipeline_statuses.index(candidate["status"]) if candidate["status"] in pipeline_statuses else 0,
            )
            interview_date = st.text_input(
                "📅 Ημερομηνία συνέντευξης",
                value=candidate.get("interview_date") or "",
                placeholder="π.χ. 10/09/2026 11:00",
            )
            rating = st.select_slider(
                "⭐ Βαθμολογία",
                options=[1, 2, 3, 4, 5],
                value=candidate.get("rating") if candidate.get("rating") in [1, 2, 3, 4, 5] else 3,
            )
            recruiter_edit = st.text_input("👤 Recruiter", value=candidate.get("recruiter") or "")
            notes = st.text_area("📝 Σημειώσεις HR", value=candidate.get("notes") or "", height=140)

            save_candidate = st.form_submit_button("💾 Αποθήκευση")
            if save_candidate:
                try:
                    update_candidate(
                        candidate["id"], new_status, user_email,
                        interview_date.strip() or None, rating,
                        notes.strip() or None, recruiter_edit.strip() or None
                    )
                    st.success("✅ Τα στοιχεία του υποψηφίου ενημερώθηκαν.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Σφάλμα ενημέρωσης: {e}")

        st.divider()
        st.subheader("📋 Ιστορικό υποψηφίου")
        history = get_candidate_history(candidate["id"])
        if history:
            history_rows = [{
                "Παλιά κατάσταση": h["old_status"] or "-",
                "Νέα κατάσταση": h["new_status"],
                "Αλλαγή από": h["changed_by"] or "-",
                "Ημερομηνία": str(h["changed_at"]),
            } for h in history]
            st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχει ιστορικό.")
    else:
        st.info("Δεν υπάρχουν υποψήφιοι με τα συγκεκριμένα φίλτρα.")

    st.divider()
    st.subheader("📋 Πλήρης λίστα υποψηφίων")
    if filtered_candidates:
        rows = [{
            "ID": c["id"],
            "Όνομα": c["first_name"],
            "Επώνυμο": c["last_name"],
            "Email": c["email"],
            "Θέση": c["position"],
            "Recruiter": c.get("recruiter"),
            "Συνέντευξη": c.get("interview_date"),
            "Βαθμολογία": c.get("rating"),
            "Κατάσταση": c["status"],
        } for c in filtered_candidates]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν υποψήφιοι.")


# ============================================================
# ONBOARDING
# ============================================================

elif page == "🚀 Onboarding":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("🚀 Employee Onboarding")
    st.caption("Checklist για την ένταξη νέων εργαζομένων.")

    employees = get_employees()
    if not employees:
        st.warning("Πρέπει πρώτα να προσθέσεις εργαζόμενο.")
    else:
        st.subheader("➕ Νέο Onboarding")
        employee_options = {
            f'{e["first_name"]} {e["last_name"]}': e["id"]
            for e in employees
        }
        with st.form("onboarding_form"):
            selected_employee = st.selectbox("Εργαζόμενος", list(employee_options.keys()))
            start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            submitted = st.form_submit_button("🚀 Δημιουργία Onboarding")
            if submitted:
                create_onboarding(employee_options[selected_employee], start_date.strftime("%Y-%m-%d"))
                st.success("✅ Το onboarding δημιουργήθηκε.")
                st.rerun()

        st.divider()
        st.subheader("📋 Onboarding Checklist")
        onboarding = get_onboarding()
        if onboarding:
            for item in onboarding:
                employee_name = f'{item["first_name"]} {item["last_name"]}'
                with st.expander(f"👤 {employee_name}"):
                    st.write(f"**Ημερομηνία έναρξης:** {item['start_date'] or '-'}")
                    contract = st.checkbox("📄 Σύμβαση", value=bool(item["contract"]), key=f"contract_{item['id']}")
                    documents = st.checkbox("📁 Έγγραφα", value=bool(item["documents"]), key=f"documents_{item['id']}")
                    email_setup = st.checkbox("📧 Email", value=bool(item["email"]), key=f"email_{item['id']}")
                    equipment = st.checkbox("💻 Εξοπλισμός", value=bool(item["equipment"]), key=f"equipment_{item['id']}")
                    system_access = st.checkbox("🔐 Πρόσβαση σε συστήματα", value=bool(item["system_access"]), key=f"system_{item['id']}")
                    training = st.checkbox("🎓 Εκπαίδευση", value=bool(item["training"]), key=f"training_{item['id']}")
                    manager_meeting = st.checkbox("🤝 Συνάντηση με Manager", value=bool(item["manager_meeting"]), key=f"manager_{item['id']}")
                    if st.button("💾 Αποθήκευση Checklist", key=f"save_onboarding_{item['id']}"):
                        update_onboarding(item["id"], int(contract), int(documents), int(email_setup), int(equipment), int(system_access), int(training), int(manager_meeting))
                        st.success("✅ Το checklist ενημερώθηκε.")
                        st.rerun()
        else:
            st.info("Δεν υπάρχουν onboarding διαδικασίες.")


# ============================================================
# LEAVES - HR
# ============================================================

elif page == "🏖️ Άδειες":

    if not IS_HR:
        st.error("⛔ Δεν έχεις δικαίωμα πρόσβασης.")
        st.stop()

    st.title("🏖️ Διαχείριση Αδειών")
    employees = get_employees()

    if not employees:
        st.warning("Πρέπει πρώτα να προσθέσεις εργαζόμενο.")
    else:
        st.subheader("➕ Νέα αίτηση άδειας")
        employee_options = {
            f'{e["first_name"]} {e["last_name"]}': e["id"]
            for e in employees
        }
        with st.form("leave_form"):
            selected_employee = st.selectbox("Εργαζόμενος", list(employee_options.keys()))
            leave_type = st.selectbox("Τύπος άδειας", ["Κανονική", "Αναρρωτική", "Άδεια άνευ αποδοχών", "Ειδική", "Άλλο"])
            start_date = st.date_input("Ημερομηνία έναρξης", value=date.today(), format="DD/MM/YYYY")
            end_date = st.date_input("Ημερομηνία λήξης", value=date.today(), format="DD/MM/YYYY")
            reason = st.text_area("Αιτιολογία")
            submitted = st.form_submit_button("📨 Υποβολή αίτησης")
            if submitted:
                if end_date < start_date:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν από την ημερομηνία έναρξης.")
                else:
                    add_leave(employee_options[selected_employee], leave_type, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), reason, "Εκκρεμεί")
                    st.success("✅ Η αίτηση άδειας καταχωρήθηκε.")
                    st.rerun()

        st.divider()
        st.subheader("📋 Αιτήσεις αδειών")
        leaves = get_leaves()
        if leaves:
            rows = [{
                "ID": l["id"],
                "Εργαζόμενος": f'{l["first_name"]} {l["last_name"]}',
                "Τύπος": l["leave_type"],
                "Από": l["start_date"],
                "Έως": l["end_date"],
                "Αιτιολογία": l["reason"] or "-",
                "Κατάσταση": l["status"],
            } for l in leaves]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("✅ HR Approval Center")
            pending_leaves = [l for l in leaves if l["status"] == "Εκκρεμεί"]
            if pending_leaves:
                for leave in pending_leaves:
                    with st.container(border=True):
                        st.write(f'**#{leave["id"]} — {leave["first_name"]} {leave["last_name"]}**')
                        st.write(f'Τύπος: {leave["leave_type"]}')
                        st.write(f'Από: {leave["start_date"]} Έως: {leave["end_date"]}')
                        st.write(f'Αιτιολογία: {leave["reason"] or "-"}')
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Έγκριση", key=f"approve_{leave['id']}"):
                                update_leave_status(leave["id"], "Εγκρίθηκε")
                                st.rerun()
                        with c2:
                            if st.button("❌ Απόρριψη", key=f"reject_{leave['id']}"):
                                update_leave_status(leave["id"], "Απορρίφθηκε")
                                st.rerun()
            else:
                st.success("✅ Δεν υπάρχουν εκκρεμή αιτήματα.")
        else:
            st.info("Δεν υπάρχουν αιτήσεις άδειας.")


# ============================================================
# AI ASSISTANT
# ============================================================

elif page == "🤖 AI Assistant":

    st.title("🤖 AI HR Assistant")
    st.caption("Ο έξυπνος βοηθός του HR.")

    if client is None:
        st.error("Δεν βρέθηκε το OPENAI_API_KEY.")
        st.info("Στο Streamlit Cloud πρόσθεσε το OPENAI_API_KEY στα Secrets.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("Γράψε την ερώτησή σου...")

        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Το AI σκέφτεται..."):
                    try:
                        response = client.responses.create(
                            model="gpt-5-mini",
                            instructions="""
Είσαι ένας επαγγελματικός AI HR Assistant.

Βοηθάς σε Recruitment, Employee Management, Onboarding,
HR Administration, HR KPIs, HR emails, Job descriptions,
Job advertisements και HR διαδικασίες.

Απαντάς στα ελληνικά εκτός αν ζητηθεί άλλη γλώσσα.
Οι απαντήσεις είναι επαγγελματικές, πρακτικές και σαφείς.
Δεν παρουσιάζεις νομική συμβουλή ως βεβαιότητα.
""",
                            input=question,
                        )
                        answer = response.output_text
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"Παρουσιάστηκε σφάλμα: {e}")

        if st.session_state.messages:
            st.divider()
            if st.button("🗑️ Καθαρισμός συνομιλίας"):
                st.session_state.messages = []
                st.rerun()
