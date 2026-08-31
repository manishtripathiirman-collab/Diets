import streamlit as st
import pandas as pd
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="wide")

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select your meals below, view their composition and health benefits, and track your daily intake live in the sidebar.")

# Direct CSV export URL for your Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1aTt0FZH5F-w0fx18tYkeWauSbJ1S4JjwvPfrVbQBbCU/export?format=csv&gid=0"

@st.cache_data(ttl=10)  # Refresh data every 10 seconds automatically
def load_meal_data():
    data = pd.read_csv(SHEET_CSV_URL)
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df = load_meal_data()

    # Identify core columns dynamically
    meal_type_col = next((c for c in df.columns if c.lower() in ["mealtype", "meal_type", "meal type", "meal"]), None)
    recipe_name_col = next((c for c in df.columns if c.lower() in ["recipename", "recipe_name", "recipe name", "recipe", "item", "dish"]), None)

    if not meal_type_col or not recipe_name_col:
        st.error("Could not find standard columns. Please ensure your sheet has 'Meal Type' and 'Recipe Name' column headers.")
        st.write("Current columns detected:", list(df.columns))
    else:
        df[meal_type_col] = df[meal_type_col].fillna("").astype(str).str.strip()
        
        # Initialize session state for tracking daily logged meals
        if 'logged_meals' not in st.session_state:
            st.session_state.logged_meals = []

        # Layout Split: Main app on the left, Daily Log Sidebar on the right
        main_col, sidebar_col = st.columns([2.2, 1])

        with main_col:
            # 1. Horizontal radio buttons for standard meal categories
            meal_category = st.radio(
                "Choose Meal Category:",
                ["Breakfast", "Lunch", "Dinner"],
                horizontal=True
            )

            # Filter database using flexible contains check
            filtered_df = df[df[meal_type_col].str.lower().str.contains(meal_category.lower(), na=False)]

            if filtered_df.empty:
                st.info(f"No recipes found for **{meal_category}** yet. Check your Google Sheet column values.")
            else:
                st.markdown(f"### Select an option for {meal_category}")
                
                # 2. Recipe Option Selector
                recipe_list = filtered_df[recipe_name_col].dropna().unique().tolist()
                selected_recipe = st.selectbox(f"Available Options:", recipe_list, key=f"select_{meal_category}")

                # Get the row details for the selected recipe
                recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

                st.divider()
                st.header(f"🍽️ {recipe_row[recipe_name_col]}")

                # 3. Categorize columns into Metrics vs Long Text Details
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

                # Render numeric metrics horizontally using st.columns
                if metric_cols:
                    cols = st.columns(len(metric_cols))
                    for i, col in enumerate(metric_cols):
                        val = recipe_row[col]
                        if pd.notna(val) and str(val).strip() != "":
                            cols[i].metric(label=col, value=str(val))
                    st.divider()

                # Button to log this meal to daily tracker
                if st.button("➕ Add to Today's Food Log", type="primary"):
                    # Extract metric values safely for calculation
                    meal_data_to_log = {
                        "category": meal_category,
                        "recipe": recipe_row[recipe_name_col],
                        "metrics": {col: recipe_row[col] for col in metric_cols}
                    }
                    st.session_state.logged_meals.append(meal_data_to_log)
                    st.success(f"Added **{recipe_row[recipe_name_col]}** to your daily tracker!")

                # Render all text columns (Ingredients, Health Benefits, etc.) as full-width sections below
                for col in text_cols:
                    val = recipe_row[col]
                    if pd.notna(val) and str(val).strip() != "":
                        st.subheader(f"📌 {col}")
                        st.write(val)
                        st.markdown("")

        with sidebar_col:
            st.subheader("📊 Today's Intake Tracker")
            st.write(f"Date: {datetime.now().strftime('%d %b %Y')}")
            
            if not st.session_state.logged_meals:
                st.info("No meals logged yet today. Click 'Add to Today's Food Log' on any recipe.")
            else:
                total_calories = 0.0
                total_protein = 0.0
                total_carbs = 0.0
                total_fats = 0.0

                st.write("---")
                for idx, meal in enumerate(st.session_state.logged_meals):
                    st.markdown(f"**{idx+1}. {meal['recipe']}** *({meal['category']})*")
                    
                    # Try aggregating metrics dynamically
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
                    
                    if st.button("❌ Remove", key=f"remove_{idx}"):
                        st.session_state.logged_meals.pop(idx)
                        st.rerun()
                    st.markdown("---")

                st.subheader("🎯 Total Nutrition Summary")
                m_col1, m_col2 = st.columns(2)
                m_col1.metric("🔥 Calories", f"{total_calories:.0f} kcal")
                m_col2.metric("💪 Protein", f"{total_protein:.1f} g")
                
                m_col3, m_col4 = st.columns(2)
                m_col3.metric("🌾 Carbs", f"{total_carbs:.1f} g")
                m_col4.metric("🥑 Fats", f"{total_fats:.1f} g")

                if st.button("Clear Entire Log"):
                    st.session_state.logged_meals = []
                    st.rerun()

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
