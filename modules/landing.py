"""Public landing site (before login) and the in-app Home page for SmartETL AI."""

import streamlit as st

# ----------------------------------------------------------
# EDIT THESE DETAILS
# ----------------------------------------------------------
AUTHOR = {
    "name": "Venkatesh",
    "title": "Data Engineer | Python Developer",
    "bio": (
        "I build practical data tools that turn messy, inconsistent data "
        "into clean, trusted datasets. SmartETL AI was created to make "
        "ETL and data quality checks simple for everyone."
    ),
    "emails": ["Venkateshvkt96@gmail.com", "venkateshvkt10@gmail.com"],
    "github": "https://github.com/venkateshvkt10",
    "linkedin": "https://www.linkedin.com/in/venkateshvkt10/",
    "location": "Chennai, India",
    # Profile photo: uses your GitHub avatar. Replace with any image URL if you like.
    "photo": "https://github.com/venkateshvkt10.png",
}

APP_VERSION = "1.0"

NAV = ["🏠 Home", "ℹ️ About", "📖 User Guide", "👤 Author", "🔐 Login"]

FEATURES = [
    ("📤", "Smart File Upload",
     "Upload CSV, Excel (.xlsx/.xls) or JSON files up to 50 MB and preview them instantly."),
    ("🔍", "Automatic Data Profiling",
     "See rows, columns, duplicates, completeness and a full column-level profile in seconds."),
    ("🧹", "Data Cleaning",
     "Remove duplicates, trim whitespace and fill missing values with a single click."),
    ("✅", "Rule-Based Validation",
     "Check required, unique, email, phone, numeric and date columns. Bad rows are separated, not lost."),
    ("⚙️", "Complete ETL Pipeline",
     "Extract, transform and validate in one run, producing Valid and Rejected record sets."),
    ("🗄️", "Database Import",
     "Pull data straight from SQL Server, MySQL, PostgreSQL or SQLite using a table or a SQL query."),
    ("🤖", "AI Quality Reports",
     "Get a quality score, recommendations and an AI-written summary of your data health."),
    ("📊", "ETL Dashboard",
     "Track every run: records processed, valid vs rejected, and execution time trends."),
    ("🔐", "Secure Private Access",
     "Admin-managed user accounts with role-based access and session isolation."),
]

STEPS = [
    ("1", "Sign in", "Log in with the account created by your administrator."),
    ("2", "Upload or connect",
     "Upload a file, or import a table or query from a database."),
    ("3", "Profile & clean", "Review the data profile and choose cleaning options."),
    ("4", "Validate", "Pick the columns and rules to validate, then run the pipeline."),
    ("5", "Review & export",
     "Check valid and rejected records, the quality report, then download CSV or Excel."),
]

CSS = """
<style>
.hero{
  padding:3rem 2rem; border-radius:20px; text-align:center; margin:.5rem 0 1.5rem 0;
  background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 55%,#06b6d4 100%); color:#fff;
}
.hero h1{font-size:2.8rem; margin:0 0 .4rem 0; color:#fff;}
.hero p{font-size:1.15rem; max-width:760px; margin:.3rem auto; opacity:.95; color:#fff;}
.badge{
  display:inline-block; padding:.25rem .8rem; margin:.2rem; border-radius:999px;
  background:rgba(255,255,255,.2); font-size:.85rem; color:#fff;
}
.card{
  border:1px solid rgba(128,128,128,.3); border-radius:14px; padding:1.1rem 1.2rem;
  height:100%; background:rgba(128,128,128,.07); margin-bottom:.8rem;
}
.card h4{margin:.2rem 0 .4rem 0;}
.card p{margin:0; opacity:.85; font-size:.95rem;}
.icon{font-size:1.8rem;}
.step{
  border-left:4px solid #7c3aed; padding:.6rem 1rem; margin:.6rem 0;
  background:rgba(128,128,128,.07); border-radius:0 10px 10px 0;
}
.footer{text-align:center; opacity:.65; font-size:.85rem; margin-top:2.5rem; padding-top:1rem;
  border-top:1px solid rgba(128,128,128,.3);}
</style>
"""


def _go_to_login():
    st.session_state["public_nav"] = "🔐 Login"


def _cards(items, per_row=3):
    for i in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for col, (icon, title, text) in zip(cols, items[i:i + per_row]):
            col.markdown(
                f'<div class="card"><div class="icon">{icon}</div>'
                f'<h4>{title}</h4><p>{text}</p></div>',
                unsafe_allow_html=True,
            )


def _footer():
    st.markdown(
        f'<div class="footer">SmartETL AI v{APP_VERSION} · Built with Python, '
        f'Streamlit and Pandas · © {AUTHOR["name"]}</div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------
# PUBLIC PAGES
# ----------------------------------------------------------
def _home():
    st.markdown(
        """
        <div class="hero">
          <h1>🧹 SmartETL AI</h1>
          <p><b>Intelligent ETL and Data Quality Platform</b></p>
          <p>Upload your data, profile it, clean it, validate it and export trusted
          datasets, with AI-powered quality reports, all in one place.</p>
          <div style="margin-top:1rem">
            <span class="badge">CSV · Excel · JSON</span>
            <span class="badge">SQL Database Import</span>
            <span class="badge">AI Reports</span>
            <span class="badge">Secure Login</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, c, _ = st.columns([1, 1, 1])
    c.button("🔐 Login to Get Started", type="primary",
             use_container_width=True, on_click=_go_to_login,
             key="hero_login_btn")

    st.write("")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("File Formats", "3")
    m2.metric("Databases", "4")
    m3.metric("Validation Rules", "6+")
    m4.metric("Max File Size", "50 MB")

    st.subheader("✨ What you can do")
    _cards(FEATURES)

    st.subheader("🚀 How it works")
    for n, title, text in STEPS:
        st.markdown(
            f'<div class="step"><b>Step {n}: {title}</b><br>{text}</div>',
            unsafe_allow_html=True,
        )
    _footer()


def _about():
    st.header("ℹ️ About SmartETL AI")
    st.write(
        "SmartETL AI is a Python-based platform that helps teams prepare "
        "reliable data. Raw files and database tables often contain duplicates, "
        "missing values, invalid emails or phone numbers and inconsistent "
        "formats. SmartETL AI finds these problems, fixes what it safely can, "
        "and separates the rest into a clear rejected-records report."
    )

    a, b = st.columns(2)
    with a:
        st.subheader("🎯 Problem it solves")
        st.write(
            "- Manual data cleaning is slow and error-prone\n"
            "- Bad records silently reach reports and databases\n"
            "- There is no history of what was processed\n"
            "- Non-technical users need a simple interface"
        )
    with b:
        st.subheader("💡 Benefits")
        st.write(
            "- Faster, repeatable data preparation\n"
            "- Clear valid vs rejected record separation\n"
            "- Quality score with actionable recommendations\n"
            "- Complete run history and performance dashboard"
        )

    st.subheader("🧰 Technology stack")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Language", "Python")
    t2.metric("Framework", "Streamlit")
    t3.metric("Data Processing", "Pandas")
    t4.metric("AI Reports", "Google Gemini")

    st.subheader("🔒 Security")
    st.write(
        "- Private access: accounts are created only by the administrator\n"
        "- Passwords are never stored in plain text\n"
        "- Each user's session data and run history are kept separate\n"
        "- Database credentials are used only for the current session and are not saved"
    )
    _footer()


def _guide():
    st.header("📖 User Guide")
    st.caption("Everything you need to get started in a few minutes.")

    st.subheader("Quick start")
    for n, title, text in STEPS:
        st.markdown(
            f'<div class="step"><b>Step {n}: {title}</b><br>{text}</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Application pages")
    with st.expander("🏠 Home", expanded=False):
        st.write("Overview of the platform and quick shortcuts.")
    with st.expander("🧼 Data Preparation"):
        st.write(
            "Upload a file, view its profile (rows, columns, duplicates, "
            "completeness), apply cleaning options and run validation rules."
        )
    with st.expander("⚙️ Complete ETL Pipeline"):
        st.write(
            "Run extract, transform and validate in one step. Download Valid "
            "records, Rejected records, or a full Excel ETL report."
        )
    with st.expander("🗄️ Database Import"):
        st.write(
            "Choose SQL Server, MySQL, PostgreSQL or SQLite, connect, then "
            "import a table or run a read-only SELECT query. Use a read-only "
            "database account where possible."
        )
    with st.expander("📊 ETL Dashboard"):
        st.write(
            "View total runs, valid vs rejected records, execution time "
            "and download your history as CSV."
        )
    with st.expander("👥 User Management (admin only)"):
        st.write("Create users and activate or deactivate accounts.")

    st.subheader("Supported inputs")
    st.write(
        "- **Files:** CSV, XLSX, XLS, JSON (up to 50 MB)\n"
        "- **Databases:** SQL Server, MySQL, PostgreSQL, SQLite"
    )

    st.subheader("Validation rules")
    st.write(
        "- **Required columns:** must not be empty\n"
        "- **Unique columns:** no duplicate keys\n"
        "- **Email / Phone:** must match a valid format\n"
        "- **Numeric / Date:** must be convertible to the right type"
    )

    st.subheader("Tips and FAQ")
    with st.expander("I forgot my password or don't have an account"):
        st.write("Contact the administrator. Accounts are created by admin only.")
    with st.expander("My file is rejected"):
        st.write(
            "Check the size (max 50 MB), the format (CSV, Excel, JSON) and "
            "that column names are not duplicated."
        )
    with st.expander("Why are some rows in Rejected Records?"):
        st.write(
            "They failed one or more validation rules. Download the rejected "
            "file, fix the values and run the pipeline again."
        )
    with st.expander("Is my data saved?"):
        st.write(
            "Uploaded data and results stay in your session and are cleared "
            "when you log out. Only run statistics are kept in your history."
        )
    _footer()


def _author():
    st.header("👤 About the Author")
    left, right = st.columns([1, 2])
    initials = "".join(w[0] for w in AUTHOR["name"].split()[:2]).upper()
    with left:
        st.markdown(
            f'<div style="width:170px;height:170px;border-radius:50%;margin:auto;'
            f'overflow:hidden;position:relative;display:flex;align-items:center;'
            f'justify-content:center;font-size:3rem;font-weight:700;color:#fff;'
            f'background:linear-gradient(135deg,#4f46e5,#06b6d4);'
            f'border:4px solid rgba(124,58,237,.6);">{initials}'
            f'<img src="{AUTHOR["photo"]}" alt="{AUTHOR["name"]}" '
            f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;" '
            f'onerror="this.style.display=\'none\'"></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.subheader(AUTHOR["name"])
        st.caption(AUTHOR["title"])
        st.write(AUTHOR["bio"])
        st.write(f"📍 {AUTHOR['location']}")

    st.subheader("Get in touch")
    for email in AUTHOR["emails"]:
        st.markdown(f"📧 [{email}](mailto:{email})")
    c1, c2 = st.columns(2)
    c1.link_button("💻 GitHub", AUTHOR["github"], use_container_width=True)
    c2.link_button("🔗 LinkedIn", AUTHOR["linkedin"], use_container_width=True)

    st.subheader("Project info")
    p1, p2 = st.columns(2)
    p1.metric("Version", APP_VERSION)
    p2.metric("Status", "Active development")
    _footer()


def _login(authenticate_user):
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("## 🔐 Sign in to SmartETL AI")
        st.caption(
            "Private access. Contact the administrator if you need an account.")

        with st.form("smartetl_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login", type="primary", use_container_width=True
            )

        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state["authenticated_user"] = user
                st.rerun()
            else:
                st.error(
                    "Invalid username or password, or the account is inactive.")

        st.info("Don't have an account? Ask the administrator to create one for you.")
    _footer()


def render_public_site(authenticate_user):
    """Landing site shown to visitors who are not signed in."""
    st.markdown(CSS, unsafe_allow_html=True)

    if "public_nav" not in st.session_state:
        st.session_state["public_nav"] = NAV[0]

    st.radio(
        "Menu", NAV, key="public_nav",
        horizontal=True, label_visibility="collapsed",
    )
    st.divider()

    page = st.session_state["public_nav"]
    if page == NAV[0]:
        _home()
    elif page == NAV[1]:
        _about()
    elif page == NAV[2]:
        _guide()
    elif page == NAV[3]:
        _author()
    else:
        _login(authenticate_user)


# ----------------------------------------------------------
# IN-APP HOME (after login)
# ----------------------------------------------------------
def render_home_page(current_user):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="hero" style="padding:2rem">
          <h1 style="font-size:2.2rem">Welcome back, {current_user['username']} 👋</h1>
          <p>Prepare, validate and export trusted data with SmartETL AI.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("⚡ Quick actions")
    _cards([
        ("🧼", "Data Preparation", "Upload, profile, clean and validate a file."),
        ("⚙️", "Complete ETL Pipeline", "Run the full pipeline and export results."),
        ("🗄️", "Database Import", "Import from a SQL database table or query."),
    ])
    st.caption("Choose a page from the sidebar to begin.")

    st.subheader("✨ Platform features")
    _cards(FEATURES)

    st.subheader("🚀 How to use")
    for n, title, text in STEPS[1:]:
        st.markdown(
            f'<div class="step"><b>Step {int(n) - 1}: {title}</b><br>{text}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("👤 About the author"):
        st.write(f"**{AUTHOR['name']}** · {AUTHOR['title']}")
        st.write(AUTHOR["bio"])
        st.write("📧 " + "  |  ".join(AUTHOR["emails"]))
        st.write(
            f"[GitHub]({AUTHOR['github']})  |  [LinkedIn]({AUTHOR['linkedin']})")
    _footer()
