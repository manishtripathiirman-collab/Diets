import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

# Custom CSS with Flexbox layout to guarantee 4 clean, side-by-side metric boxes on mobile without overflowing
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 700px;
    }
    .watermark-banner {
        position: relative;
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url("https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=1000&q=80");
        background-size: cover;
        background-position: center;
        padding: 24px 16px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .watermark-banner h1 {
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .watermark-banner p {
        font-size: 11px;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Robust Flexbox fix for 4 side-by-side columns on mobile */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 25% !important;
    }

    /* Compact metric box styling for mobile screens */
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 4px 6px !important;
        border-radius: 8px;
        text-align: left;
    }
    div[data-testid="stMetric"] label {
        font-size: 10px !important;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 13px !important;
        font-weight: 600;
        text-align: right !important;
    }
    </style>
""", unsafe_allow_html=True)

# Compact Watermark Banner Header
st.markdown("""
    <div class="watermark-banner">
        <h1>🥗 Daily Meal Planner & Nutrition Tracker</h1>
        <p>Track composition, dates, and email range summaries to manishtripathi.irman@gmail.com</p>
    </div>
""", unsafe_allow_html=True)

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
        
        # Initialize session state variables
        if 'logged_meals' not in st.session_state:
            st.session_state.logged_meals = []
        if 'confirm_delete_idx' not in st.session_state:
            st.session_state.confirm_delete_idx = None
        if 'confirm_clear_all' not in st.session_state:
            st.session_state.confirm_clear_all = False

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
            st.markdown(f"### 🍽️ {recipe_row[recipe_name_col]}")

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

            # Render numeric metrics strictly side-by-side in 4 columns
            if metric_cols:
                cols = st.columns(len(metric_cols))
                for i, col in enumerate(metric_cols):
                    val = recipe_row[col]
                    if pd.notna(val) and str(val).strip() != "":
                        cols[i].metric(label=col, value=str(val))
                st.markdown("")

            log_date = st.date_input("Meal Date", value=date.today(), key=f"date_{selected_recipe}")

            if st.button("➕ Add to Food Log", type="primary", use_container_width=True):
                if log_date > date.today():
                    st.error("Abe Pagle Time Travel kar raha kya?")
                else:
                    meal_data_to_log = {
                        "date": log_date,
                        "category": meal_category,
                        "recipe": recipe_row[recipe_name_col],
                        "metrics": {col: recipe_row[col] for col in metric_cols}
                    }
                    st.session_state.logged_meals.append(meal_data_to_log)
                    
                    temp_alert = st.success(f"✅ Added **{recipe_row[recipe_name_col]}** for {log_date} to your tracker!")
                    time.sleep(2)
                    temp_alert.empty()
                    st.rerun()

            st.divider()

            for col in text_cols:
                val = recipe_row[col]
                if pd.notna(val) and str(val).strip() != "":
                    st.markdown(f"**📌 {col}**")
                    st.write(val)
                    st.markdown("")

        # --- NUTRITION TRACKER & DATE RANGE SUMMARY SECTION ---
        st.markdown("---")
        st.header("📊 Nutrition Log & Date Range Tracker")
        
        if not st.session_state.logged_meals:
            st.info("No meals logged yet. Add meals above to start tracking.")
        else:
            st.markdown("#### 🔍 Select Date Range for Summary")
            col_d1, col_d2 = st.columns(2)
            range_start = col_d1.date_input("From Date", value=date.today(), key="summary_start")
            range_end = col_d2.date_input("To Date", value=date.today(), key="summary_end")

            range_filtered_logs = [m for m in st.session_state.logged_meals if range_start <= m['date'] <= range_end]

            rc_calories, rc_protein, rc_carbs, rc_fats = 0.0, 0.0, 0.0, 0.0
            for m in range_filtered_logs:
                for m_key, m_val in m['metrics'].items():
                    try:
                        v = float(str(m_val).replace("g", "").strip())
                        kl = m_key.lower()
                        if "calorie" in kl or "kcal" in kl: rc_calories += v
                        elif "protein" in kl: rc_protein += v
                        elif "carb" in kl: rc_carbs += v
                        elif "fat" in kl: rc_fats += v
                    except:
                        pass

            st.markdown(f"**Summary from {range_start} to {range_end}** ({len(range_filtered_logs)} items logged):")
            sum_cols = st.columns(4)
            sum_cols[0].metric("🔥 Calories", f"{rc_calories:.0f}")
            sum_cols[1].metric("💪 Protein", f"{rc_protein:.1f}g")
            sum_cols[2].metric("🌾 Carbs", f"{rc_carbs:.1f}g")
            sum_cols[3].metric("🥑 Fats", f"{rc_fats:.1f}g")
            st.markdown("")

            # --- MANAGE LOGGED ITEMS WITH DELETE CONFIRMATION PROMPT ---
            st.markdown("#### 📝 All Logged Meals")
            for idx, meal in enumerate(st.session_state.logged_meals):
                col_item_info, col_item_btn = st.columns([3, 1])
                with col_item_info:
                    st.markdown(f"**{idx+1}. {meal['recipe']}** *({meal['category']})* <br><small>📅 {meal['date']}</small>", unsafe_allow_html=True)
                with col_item_btn:
                    if st.button("🗑️ Delete", key=f"del_btn_{idx}", use_container_width=True):
                        st.session_state.confirm_delete_idx = idx

                if st.session_state.confirm_delete_idx == idx:
                    st.warning(f"Are you sure you want to delete **{meal['recipe']}** ({meal['date']})?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("Yes, Delete", key=f"yes_del_{idx}", use_container_width=True):
                        st.session_state.logged_meals.pop(idx)
                        st.session_state.confirm_delete_idx = None
                        st.rerun()
                    if c_no.button("Cancel", key=f"no_del_{idx}", use_container_width=True):
                        st.session_state.confirm_delete_idx = None
                        st.rerun()
                st.markdown("---")

            # --- EMAIL REPORT SECTION ---
            st.subheader("📧 Email Range Summary Report")
            with st.form("email_form"):
                st.write(f"Send summary report (**{range_start} to {range_end}**) to **manishtripathi.irman@gmail.com**:")
                
                submit_email = st.form_submit_button("Send Summary to Email", use_container_width=True)
                
                if submit_email:
                    if not range_filtered_logs:
                        st.warning("No logged meals found within the selected date range to email.")
                    else:
                        report_lines = [f"- {m['date']} | {m['category']}: {m['recipe']}" for m in range_filtered_logs]
                        email_body = f"""Hello Manish,\n\nHere is your nutrition summary report from {range_start} to {range_end}:\n\nLogged Meals:\n""" + "\n".join(report_lines) + f"""\n\nTotals for Range:\n- Calories: {rc_calories:.0f} kcal\n- Protein: {rc_protein:.1f} g\n- Carbs: {rc_carbs:.1f} g\n- Fats: {rc_fats:.1f} g\n\nBest regards,\nYour Meal Planner App"""

                        try:
                            if "smtp" in st.secrets:
                                smtp_user = st.secrets["smtp"]["user"]
                                smtp_pass = st.secrets["smtp"]["password"]
                                smtp_server = st.secrets["smtp"]["server"]
                                smtp_port = st.secrets["smtp"]["port"]

                                msg = MIMEMultipart()
                                msg['From'] = smtp_user
                                msg['To'] = "manishtripathi.irman@gmail.com"
                                msg['Subject'] = f"Nutrition Range Report ({range_start} to {range_end})"
                                msg.attach(MIMEText(email_body, 'plain'))

                                server = smtplib.SMTP(smtp_server, smtp_port)
                                server.starttls()
                                server.login(smtp_user, smtp_pass)
                                server.sendmail(smtp_user, "manishtripathi.irman@gmail.com", msg.as_string())
                                server.quit()
                                st.success("Report successfully sent to manishtripathi.irman@gmail.com!")
                            else:
                                st.success(f"Report compiled successfully for manishtripathi.irman@gmail.com ({range_start} to {range_end})!")
                                with st.expander("View Email Content Preview"):
                                    st.text(email_body)
                                st.info("Note: To enable direct auto-sending via SMTP, configure your email credentials under Streamlit app Secrets.")
                        except Exception as mail_err:
                            st.error(f"Failed to send email: {mail_err}")

            if not st.session_state.confirm_clear_all:
                if st.button("Clear Entire Log", use_container_width=True):
                    st.session_state.confirm_clear_all = True
                    st.rerun()
            else:
                st.warning("Are you sure you want to clear your entire log?")
                cc_yes, cc_no = st.columns(2)
                if cc_yes.button("Yes, Clear All", use_container_width=True):
                    st.session_state.logged_meals = []
                    st.session_state.confirm_clear_all = False
                    st.rerun()
                if cc_no.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_all = False
                    st.rerun()

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
