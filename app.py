import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

# Custom CSS to strictly enforce horizontal 4-column layout on mobile devices
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="column"] {
        float: left !important;
        width: 23% !important;
        flex: 1 1 23% !important;
        min-width: 0px !important;
        margin-right: 2% !important;
    }
    div[data-testid="column"]:last-child {
        margin-right: 0 !important;
    }
    .row-widget.stHorizontal {
        display: flex !important;
        flex-direction: row !important;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 4px 2px;
        border-radius: 6px;
        text-align: center;
    }
    div[data-testid="stMetric"] label {
        font-size: 10px !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select your meals below, track your daily nutrition, and email reports to `manishtripathi.irman@gmail.com`.")

# Direct CSV export URL for your Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1aTt0FZH5F-w0fx18tYkeWauSbJ1S4JjwvPfrVbQBbCU/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def load_meal_data():
    data = pd.read_csv(SHEET_CSV_URL)
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df = load_meal_data()

    meal_type_col = next((c for c in df.columns if c.lower() in ["mealtype", "meal_type", "meal type", "meal"]), None)
    recipe_name_col = next((c for c in df.columns if c.lower() in ["recipename", "recipe_name", "recipe name", "recipe", "item", "dish"]), None)

    if not meal_type_col or not recipe_name_col:
        st.error("Could not find standard columns. Please ensure your sheet has 'Meal Type' and 'Recipe Name' column headers.")
    else:
        df[meal_type_col] = df[meal_type_col].fillna("").astype(str).str.strip()
        
        # Initialize session state for tracking logged meals with timestamps
        if 'logged_meals' not in st.session_state:
            st.session_state.logged_meals = []

        # 1. Horizontal radio buttons for standard meal categories
        meal_category = st.radio(
            "Choose Meal Category:",
            ["Breakfast", "Lunch", "Dinner"],
            horizontal=True
        )

        filtered_df = df[df[meal_type_col].str.lower().str.contains(meal_category.lower(), na=False)]

        if filtered_df.empty:
            st.info(f"No recipes found for **{meal_category}** yet. Check your Google Sheet column values.")
        else:
            st.markdown(f"### Select an option for {meal_category}")
            
            recipe_list = filtered_df[recipe_name_col].dropna().unique().tolist()
            selected_recipe = st.selectbox(f"Available Options:", recipe_list, key=f"select_{meal_category}")

            recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

            st.divider()
            st.header(f"🍽️ {recipe_row[recipe_name_col]}")

            exclude_cols = {meal_type_col.lower(), recipe_name_col.lower()}
            other_columns = [col for col in df.columns if col.lower() not in exclude_cols]

            metric_cols = []
            text_cols = []

            for col in other_columns:
                col_lower = col.lower()
                if col_lower in ["calories", "calorie", "kcal", "protein (g)", "protein", "carbs (g)", "carbs", "fats (g)", "fats"]:
                    metric_cols.append(col)
                else:
                    text_cols.append(col)

            if metric_cols:
                cols = st.columns(len(metric_cols))
                for i, col in enumerate(metric_cols):
                    val = recipe_row[col]
                    if pd.notna(val) and str(val).strip() != "":
                        cols[i].metric(label=col, value=str(val))
                st.markdown("<div style='clear: both;'></div>", unsafe_allow_html=True)
                st.markdown("")

            if st.button("➕ Add to Today's Food Log", type="primary", use_container_width=True):
                meal_data_to_log = {
                    "date": date.today(),
                    "category": meal_category,
                    "recipe": recipe_row[recipe_name_col],
                    "metrics": {col: recipe_row[col] for col in metric_cols}
                }
                st.session_state.logged_meals.append(meal_data_to_log)
                st.success(f"Added **{recipe_row[recipe_name_col]}** to your daily tracker!")

            st.divider()

            for col in text_cols:
                val = recipe_row[col]
                if pd.notna(val) and str(val).strip() != "":
                    st.subheader(f"📌 {col}")
                    st.write(val)
                    st.markdown("")

        # --- TODAY'S INTAKE TRACKER SECTION ---
        st.markdown("---")
        st.header("📊 Today's Intake Tracker")
        st.caption(f"Date: {datetime.now().strftime('%d %b %Y')}")
        
        if not st.session_state.logged_meals:
            st.info("No meals logged yet today. Click 'Add to Today's Food Log' on any recipe above.")
        else:
            total_calories = 0.0
            total_protein = 0.0
            total_carbs = 0.0
            total_fats = 0.0

            for idx, meal in enumerate(st.session_state.logged_meals):
                col_item_info, col_item_btn = st.columns([3, 1])
                with col_item_info:
                    st.markdown(f"**{idx+1}. {meal['recipe']}** *({meal['category']})* - {meal['date']}")
                with col_item_btn:
                    if st.button("❌ Remove", key=f"remove_{idx}", use_container_width=True):
                        st.session_state.logged_meals.pop(idx)
                        st.rerun()
                
                for m_key, m_val in meal['metrics'].items():
                    try:
                        val_num = float(str(m_val).replace("g", "").strip())
                        m_lower = m_key.lower()
                        if "calorie" in m_lower or "kcal" in m_lower:
                            total_calories += val_num
                        elif "protein" in m_lower:
                            total_protein += val_num
                        elif "carb" in m_lower:
                            total_carbs += val_num
                        elif "fat" in m_lower:
                            total_fats += val_num
                    except:
                        pass
                st.markdown("---")

            st.subheader("🎯 Total Nutrition Summary")
            
            sum_cols = st.columns(4)
            sum_cols[0].metric("🔥 Calories", f"{total_calories:.0f}")
            sum_cols[1].metric("💪 Protein", f"{total_protein:.1f}g")
            sum_cols[2].metric("🌾 Carbs", f"{total_carbs:.1f}g")
            sum_cols[3].metric("🥑 Fats", f"{total_fats:.1f}g")
            st.markdown("<div style='clear: both;'></div>", unsafe_allow_html=True)
            st.markdown("")

            # --- EMAIL REPORT SECTION WITH DATE RANGE ---
            st.subheader("📧 Email Nutrition Report")
            with st.form("email_form"):
                st.write("Select date range to include in the summary report sent to **manishtripathi.irman@gmail.com**:")
                
                col_d1, col_d2 = st.columns(2)
                start_date = col_d1.date_input("Start Date", value=date.today())
                end_date = col_d2.date_input("End Date", value=date.today())
                
                submit_email = st.form_submit_button("Send Summary to Email", use_container_width=True)
                
                if submit_email:
                    # Filter logged meals by selected date range
                    filtered_logs = [m for m in st.session_state.logged_meals if start_date <= m['date'] <= end_date]
                    
                    if not filtered_logs:
                        st.warning("No logged meals found within the selected date range.")
                    else:
                        # Calculate totals for the date range
                        r_calories, r_protein, r_carbs, r_fats = 0.0, 0.0, 0.0, 0.0
                        report_lines = []
                        
                        for m in filtered_logs:
                            report_lines.append(f"- {m['date']} | {m['category']}: {m['recipe']}")
                            for m_key, m_val in m['metrics'].items():
                                try:
                                    v = float(str(m_val).replace("g", "").strip())
                                    kl = m_key.lower()
                                    if "calorie" in kl or "kcal" in kl: r_calories += v
                                    elif "protein" in kl: r_protein += v
                                    elif "carb" in kl: r_carbs += v
                                    elif "fat" in kl: r_fats += v
                                except:
                                    pass

                        email_body = f"""Hello Manish,\n\nHere is your nutrition summary report from {start_date} to {end_date}:\n\nLogged Meals:\n""" + "\n".join(report_lines) + f"""\n\nTotals:\n- Calories: {r_calories:.0f} kcal\n- Protein: {r_protein:.1f} g\n- Carbs: {r_carbs:.1f} g\n- Fats: {r_fats:.1f} g\n\nBest regards,\nYour Meal Planner App"""

                        # Attempt to send email via Streamlit Secrets SMTP configuration or notify setup
                        try:
                            # Check if SMTP secrets exist, otherwise display ready-to-copy format / simulation
                            if "smtp" in st.secrets:
                                smtp_user = st.secrets["smtp"]["user"]
                                smtp_pass = st.secrets["smtp"]["password"]
                                smtp_server = st.secrets["smtp"]["server"]
                                smtp_port = st.secrets["smtp"]["port"]

                                msg = MIMEMultipart()
                                msg['From'] = smtp_user
                                msg['To'] = "manishtripathi.irman@gmail.com"
                                msg['Subject'] = f"Nutrition Summary Report ({start_date} to {end_date})"
                                msg.attach(MIMEText(email_body, 'plain'))

                                server = smtplib.SMTP(smtp_server, smtp_port)
                                server.starttls()
                                server.login(smtp_user, smtp_pass)
                                server.sendmail(smtp_user, "manishtripathi.irman@gmail.com", msg.as_string())
                                server.quit()
                                st.success("Report successfully sent to manishtripathi.irman@gmail.com!")
                            else:
                                # Fallback display if SMTP credentials are not yet added to Streamlit secrets
                                st.success(f"Report compiled successfully for manishtripathi.irman@gmail.com ({start_date} to {end_date})!")
                                with st.expander("View Email Content Preview"):
                                    st.text(email_body)
                                st.info("Note: To enable direct auto-sending via SMTP, configure your email credentials under Streamlit app Secrets.")
                        except Exception as mail_err:
                            st.error(f"Failed to send email: {mail_err}")

            if st.button("Clear Entire Log", use_container_width=True):
                st.session_state.logged_meals = []
                st.rerun()

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
