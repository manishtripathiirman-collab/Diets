import streamlit as st
import pandas as pd
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

# Custom CSS with Flexbox layout and explicit metric box alignment fixes
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
    
    div[data-testid="column"] div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    div[data-testid="column"] div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        width: 25% !important;
    }

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

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1aTt0FZH5F-w0fx18tYkeWauSbJ1S4JjwvPfrVbQBbCU/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def load_meal_data():
    data = pd.read_csv(SHEET_CSV_URL)
    data.columns = [c.strip() for c in data.columns]
    return data

# --- GLOBAL USER DB & STATE INITIALIZATION ---
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "manish": {"password": "password123", "email": "manishtripathi.irman@gmail.com"},
        "priya": {"password": "password123", "email": "priyadarshini.tripathi@gmail.com"}
    }

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- AUTHENTICATION & REGISTRATION SCREEN ---
if not st.session_state.authenticated:
    st.markdown("""
        <div class="watermark-banner">
            <h1>🔐 Member Access</h1>
            <p>Login with your credentials or create a new user profile</p>
        </div>
    """, unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Create Account"])
    
    with tab_login:
        with st.form("login_form"):
            user_input = st.text_input("User ID", key="login_user")
            pass_input = st.text_input("Password", type="password", key="login_pass")
            remember_me = st.checkbox("Remember My Password (Save Session)")
            submit_login = st.form_submit_button("Login", use_container_width=True)
            
            if submit_login:
                db = st.session_state.users_db
                if user_input in db and db[user_input]["password"] == pass_input:
                    st.session_state.authenticated = True
                    st.session_state.username = user_input
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid User ID or Password.")
                    
    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("Choose User ID", key="reg_user")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            new_email = st.text_input("Default Report Email ID", key="reg_email", placeholder="yourname@gmail.com")
            submit_reg = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit_reg:
                cleaned_user = new_user.strip().lower()
                if not cleaned_user or not new_pass or not new_email:
                    st.warning("Please fill in all fields.")
                elif cleaned_user in st.session_state.users_db:
                    st.error("User ID already exists. Choose a different one.")
                else:
                    st.session_state.users_db[cleaned_user] = {
                        "password": new_pass,
                        "email": new_email.strip()
                    }
                    st.success("Account created successfully! Please switch to the Login tab.")
    st.stop()

# --- MAIN APP (Post-Authentication) ---
st.markdown("""
    <div class="watermark-banner">
        <h1>🥗 Daily Meal Planner & Nutrition Tracker</h1>
        <p>Track composition, portions, goals, favorites, and custom email reports</p>
    </div>
""", unsafe_allow_html=True)

user_key = st.session_state.username
current_user_data = st.session_state.users_db[user_key]

# Logout & Profile Settings in Sidebar
with st.sidebar:
    st.write(f"Logged in as: **{user_key}**")
    
    with st.expander("⚙️ Profile & Email Settings"):
        updated_email = st.text_input("Report Recipient Email", value=current_user_data["email"], key=f"setting_email_{user_key}")
        if st.button("Update Email", use_container_width=True):
            st.session_state.users_db[user_key]["email"] = updated_email
            st.success("Email updated!")
            time.sleep(1)
            st.rerun()
            
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()
    st.divider()

try:
    df = load_meal_data()

    meal_type_col = next((c for c in df.columns if c.lower() in ["mealtype", "meal_type", "meal type", "meal"]), None)
    recipe_name_col = next((c for c in df.columns if c.lower() in ["recipename", "recipe_name", "recipe name", "recipe", "item", "dish"]), None)

    if not meal_type_col or not recipe_name_col:
        st.error("Could not find standard columns. Please ensure your sheet has 'Meal Type' and 'Recipe Name' column headers.")
    else:
        df[meal_type_col] = df[meal_type_col].fillna("").astype(str).str.strip()
        
        # User-specific session state variables initialization
        if f'logged_meals_{user_key}' not in st.session_state:
            st.session_state[f'logged_meals_{user_key}'] = []
        if f'favorites_{user_key}' not in st.session_state:
            st.session_state[f'favorites_{user_key}'] = []
        if f'confirm_delete_idx_{user_key}' not in st.session_state:
            st.session_state[f'confirm_delete_idx_{user_key}'] = None
        if f'confirm_clear_all_{user_key}' not in st.session_state:
            st.session_state[f'confirm_clear_all_{user_key}'] = False

        # --- SIDEBAR GOALS & QUICK-ADD ---
        with st.sidebar:
            st.header("🎯 Daily Targets")
            target_calories = st.number_input("Calorie Goal (kcal)", value=2000, step=50, key=f"t_cal_{user_key}")
            target_protein = st.number_input("Protein Goal (g)", value=130.0, step=5.0, key=f"t_pro_{user_key}")
            target_carbs = st.number_input("Carbs Goal (g)", value=200.0, step=5.0, key=f"t_carb_{user_key}")
            target_fats = st.number_input("Fats Goal (g)", value=60.0, step=5.0, key=f"t_fat_{user_key}")
            
            st.divider()
            st.markdown("### ⭐ Quick-Add Favorites")
            user_favorites = st.session_state[f'favorites_{user_key}']
            if not user_favorites:
                st.info("No favorites added yet. Click '⭐ Add to Favorites' on any recipe card below.")
            else:
                for fav in user_favorites:
                    col_fav_name, col_fav_btn = st.columns([2, 1])
                    col_fav_name.write(f"**{fav['recipe']}**")
                    if col_fav_btn.button("Log", key=f"fav_log_{user_key}_{fav['recipe']}"):
                        fav_row = df[df[recipe_name_col] == fav['recipe']]
                        if not fav_row.empty:
                            r_data = fav_row.iloc[0]
                            parsed_metrics = {}
                            for col in df.columns:
                                if col.lower() in ["calories", "calorie", "kcal", "protein (g)", "protein", "carbs (g)", "carbs", "fats (g)", "fats"]:
                                    val = r_data[col]
                                    if pd.notna(val) and str(val).strip() != "":
                                        try:
                                            parsed_metrics[col] = float(str(val).replace("g", "").strip())
                                        except:
                                            pass
                            st.session_state[f'logged_meals_{user_key}'].append({
                                "date": date.today(),
                                "category": r_data[meal_type_col],
                                "recipe": r_data[recipe_name_col],
                                "metrics": parsed_metrics
                            })
                            st.success(f"Logged {fav['recipe']}!")
                            time.sleep(1)
                            st.rerun()

        # 1. Horizontal radio buttons for standard meal categories
        meal_category = st.radio(
            "Choose Meal Category:",
            ["Breakfast", "Lunch", "Dinner"],
            horizontal=True,
            key=f"meal_cat_{user_key}"
        )

        filtered_df = df[df[meal_type_col].str.lower().str.contains(meal_category.lower(), na=False)]

        if filtered_df.empty:
            st.info(f"No recipes found for **{meal_category}** yet. Check your Google Sheet column values.")
        else:
            recipe_list = filtered_df[recipe_name_col].dropna().unique().tolist()
            
            st.markdown(f"### Select an option for {meal_category}")
            search_query = st.text_input("🔍 Search recipe by keyword", placeholder="e.g. paneer, egg, oats...", key=f"search_{user_key}_{meal_category}")
            
            if search_query:
                recipe_list = [r for r in recipe_list if search_query.lower() in r.lower()]
                if not recipe_list:
                    st.warning(f"No recipes match '{search_query}'.")
            
            if recipe_list:
                selected_recipe = st.selectbox("Available Options:", recipe_list, key=f"select_{user_key}_{meal_category}")
                recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

                st.divider()
                
                col_title, col_fav_toggle = st.columns([3, 1])
                col_title.markdown(f"### 🍽️ {recipe_row[recipe_name_col]}")
                
                is_fav = any(f['recipe'] == recipe_row[recipe_name_col] for f in st.session_state[f'favorites_{user_key}'])
                fav_label = "⭐ Favorited" if is_fav else "☆ Add Favorite"
                if col_fav_toggle.button(fav_label, key=f"fav_toggle_{user_key}_{selected_recipe}", use_container_width=True):
                    if is_fav:
                        st.session_state[f'favorites_{user_key}'] = [f for f in st.session_state[f'favorites_{user_key}'] if f['recipe'] != recipe_row[recipe_name_col]]
                    else:
                        st.session_state[f'favorites_{user_key}'].append({"recipe": recipe_row[recipe_name_col], "category": meal_category})
                    st.rerun()

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

                st.markdown("**🍽️ Portion Multiplier**")
                portion_choice = st.radio(
                    "Portion Multiplier Choice:",
                    ["1x", "1.5x", "2x"],
                    horizontal=True,
                    key=f"portion_radio_{user_key}_{selected_recipe}",
                    label_visibility="collapsed"
                )
                
                portion_multiplier = 1.0
                if portion_choice == "1.5x":
                    portion_multiplier = 1.5
                elif portion_choice == "2x":
                    portion_multiplier = 2.0

                if metric_cols:
                    cols = st.columns(len(metric_cols))
                    scaled_metrics_dict = {}
                    for i, col in enumerate(metric_cols):
                        val = recipe_row[col]
                        if pd.notna(val) and str(val).strip() != "":
                            try:
                                clean_val = float(str(val).replace("g", "").strip()) * portion_multiplier
                                unit_suffix = "g" if "g" in str(val).lower() or col.lower() in ["protein", "carbs", "fats", "protein (g)", "carbs (g)", "fats (g)"] else ""
                                formatted_val = f"{clean_val:.1f}{unit_suffix}" if unit_suffix else f"{clean_val:.0f}"
                                cols[i].metric(label=f"{col} ({portion_choice})", value=formatted_val)
                                scaled_metrics_dict[col] = clean_val
                            except:
                                cols[i].metric(label=col, value=str(val))
                                scaled_metrics_dict[col] = val
                    st.markdown("")

                log_date = st.date_input("Meal Date", value=date.today(), key=f"date_{user_key}_{selected_recipe}")

                if st.button("➕ Add to Food Log", type="primary", use_container_width=True):
                    if log_date > date.today():
                        st.error("Abe Pagle Time Travel kar raha kya?")
                    else:
                        meal_data_to_log = {
                            "date": log_date,
                            "category": meal_category,
                            "recipe": f"{recipe_row[recipe_name_col]} ({portion_choice})" if portion_choice != "1x" else recipe_row[recipe_name_col],
                            "metrics": scaled_metrics_dict
                        }
                        st.session_state[f'logged_meals_{user_key}'].append(meal_data_to_log)
                        
                        temp_alert = st.success(f"✅ Added **{recipe_row[recipe_name_col]}** ({portion_choice}) for {log_date} to your tracker!")
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
        
        user_logs = st.session_state[f'logged_meals_{user_key}']
        if not user_logs:
            st.info("No meals logged yet. Add meals above to start tracking.")
        else:
            st.markdown("#### 🔍 Select Date Range for Summary")
            col_d1, col_d2 = st.columns(2)
            range_start = col_d1.date_input("From Date", value=date.today(), key=f"summary_start_{user_key}")
            range_end = col_d2.date_input("To Date", value=date.today(), key=f"summary_end_{user_key}")

            range_filtered_logs = [m for m in user_logs if range_start <= m['date'] <= range_end]

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

            # Daily Macro Goal Progress Bars
            today_logs = [m for m in user_logs if m['date'] == date.today()]
            t_calories, t_protein, t_carbs, t_fats = 0.0, 0.0, 0.0, 0.0
            for m in today_logs:
                for m_key, m_val in m['metrics'].items():
                    try:
                        v = float(str(m_val).replace("g", "").strip())
                        kl = m_key.lower()
                        if "calorie" in kl or "kcal" in kl: t_calories += v
                        elif "protein" in kl: t_protein += v
                        elif "carb" in kl: t_carbs += v
                        elif "fat" in kl: t_fats += v
                    except:
                        pass

            st.markdown("#### 🎯 Today's Goal Progress")
            st.markdown(f"**Calories:** {t_calories:.0f} / {target_calories} kcal")
            st.progress(min(t_calories / target_calories, 1.0) if target_calories > 0 else 0.0)
            
            st.markdown(f"**Protein:** {t_protein:.1f} / {target_protein}g")
            st.progress(min(t_protein / target_protein, 1.0) if target_protein > 0 else 0.0)
            
            st.markdown(f"**Carbs:** {t_carbs:.1f} / {target_carbs}g")
            st.progress(min(t_carbs / target_carbs, 1.0) if target_carbs > 0 else 0.0)
            
            st.markdown(f"**Fats:** {t_fats:.1f} / {target_fats}g")
            st.progress(min(t_fats / target_fats, 1.0) if target_fats > 0 else 0.0)
            st.markdown("")

            df_export = pd.DataFrame([{
                "Date": m['date'],
                "Category": m['category'],
                "Recipe": m['recipe'],
                **{k: v for k, v in m['metrics'].items()}
            } for m in user_logs])
            
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Complete Log as CSV",
                data=csv_data,
                file_name=f"nutrition_log_{user_key}_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown("")

            # --- MANAGE LOGGED ITEMS WITH DELETE CONFIRMATION ---
            st.markdown("#### 📝 All Logged Meals")
            for idx, meal in enumerate(user_logs):
                col_item_info, col_item_btn = st.columns([3, 1])
                with col_item_info:
                    st.markdown(f"**{idx+1}. {meal['recipe']}** *({meal['category']})* <br><small>📅 {meal['date']}</small>", unsafe_allow_html=True)
                with col_item_btn:
                    if st.button("🗑️ Delete", key=f"del_btn_{user_key}_{idx}", use_container_width=True):
                        st.session_state[f'confirm_delete_idx_{user_key}'] = idx

                if st.session_state[f'confirm_delete_idx_{user_key}'] == idx:
                    st.warning(f"Are you sure you want to delete **{meal['recipe']}** ({meal['date']})?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("Yes, Delete", key=f"yes_del_{user_key}_{idx}", use_container_width=True):
                        st.session_state[f'logged_meals_{user_key}'].pop(idx)
                        st.session_state[f'confirm_delete_idx_{user_key}'] = None
                        st.rerun()
                    if c_no.button("Cancel", key=f"no_del_{user_key}_{idx}", use_container_width=True):
                        st.session_state[f'confirm_delete_idx_{user_key}'] = None
                        st.rerun()
                st.markdown("---")

            # --- EMAIL REPORT SECTION WITH CUSTOM RECIPIENT OPTION ---
            st.subheader("📧 Email Range Summary Report")
            with st.form(f"email_form_{user_key}"):
                default_email = st.session_state.users_db[user_key]["email"]
                recipient_email = st.text_input("Send Report To (Email Address)", value=default_email, key=f"recipient_{user_key}")
                st.write(f"Report Period: **{range_start} to {range_end}**")
                
                submit_email = st.form_submit_button("Send Summary to Email", use_container_width=True)
                
                if submit_email:
                    if not range_filtered_logs:
                        st.warning("No logged meals found within the selected date range to email.")
                    elif not recipient_email or "@" not in recipient_email:
                        st.error("Please enter a valid email address.")
                    else:
                        report_lines = [f"- {m['date']} | {m['category']}: {m['recipe']}" for m in range_filtered_logs]
                        email_body = f"""Hello {user_key.capitalize()},\n\nHere is your nutrition summary report from {range_start} to {range_end}:\n\nLogged Meals:\n""" + "\n".join(report_lines) + f"""\n\nTotals for Range:\n- Calories: {rc_calories:.0f} kcal\n- Protein: {rc_protein:.1f} g\n- Carbs: {rc_carbs:.1f} g\n- Fats: {rc_fats:.1f} g\n\nBest regards,\nYour Meal Planner App"""

                        try:
                            if "smtp" in st.secrets:
                                smtp_user = st.secrets["smtp"]["user"]
                                smtp_pass = st.secrets["smtp"]["password"]
                                smtp_server = st.secrets["smtp"]["server"]
                                smtp_port = st.secrets["smtp"]["port"]

                                msg = MIMEMultipart()
                                msg['From'] = smtp_user
                                msg['To'] = recipient_email
                                msg['Subject'] = f"Nutrition Range Report ({range_start} to {range_end})"
                                msg.attach(MIMEText(email_body, 'plain'))

                                server = smtplib.SMTP(smtp_server, smtp_port)
                                server.starttls()
                                server.login(smtp_user, smtp_pass)
                                server.sendmail(smtp_user, recipient_email, msg.as_string())
                                server.quit()
                                st.success(f"Report successfully sent to {recipient_email}!")
                            else:
                                st.success(f"Report compiled successfully for {recipient_email} ({range_start} to {range_end})!")
                                with st.expander("View Email Content Preview"):
                                    st.text(email_body)
                                st.info("Note: Configure your SMTP credentials in Streamlit Secrets to enable direct emailing.")
                        except Exception as mail_err:
                            st.error(f"Failed to send email: {mail_err}")

            if not st.session_state[f'confirm_clear_all_{user_key}']:
                if st.button("Clear Entire Log", use_container_width=True, key=f"clear_all_{user_key}"):
                    st.session_state[f'confirm_clear_all_{user_key}'] = True
                    st.rerun()
            else:
                st.warning("Are you sure you want to clear your entire log?")
                cc_yes, cc_no = st.columns(2)
                if cc_yes.button("Yes, Clear All", use_container_width=True, key=f"yes_clear_{user_key}"):
                    st.session_state[f'logged_meals_{user_key}'] = []
                    st.session_state[f'confirm_clear_all_{user_key}'] = False
                    st.rerun()
                if cc_no.button("Cancel", use_container_width=True, key=f"no_clear_{user_key}"):
                    st.session_state[f'confirm_clear_all_{user_key}'] = False
                    st.rerun()

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
