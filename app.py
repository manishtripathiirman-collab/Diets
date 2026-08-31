import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select a meal time below to explore recipes, nutrition details, and health benefits.")

# Direct CSV export URL for your Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1aTt0FZH5F-w0fx18tYkeWauSbJ1S4JjwvPfrVbQBbCU/export?format=csv&gid=0"

@st.cache_data(ttl=10)  # Refresh data every 10 seconds automatically
def load_meal_data():
    data = pd.read_csv(SHEET_CSV_URL)
    # Clean up column names to avoid whitespace/casing mismatches
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
        # Clean up the meal type column data
        df[meal_type_col] = df[meal_type_col].fillna("").astype(str).str.strip()
        
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
            selected_recipe = st.selectbox(f"Available Options:", recipe_list)

            # Get the row details for the selected recipe
            recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

            st.divider()
            st.header(f"🍽️ {recipe_row[recipe_name_col]}")

            # 3. Strictly categorize columns: Only calories and specific macros go into horizontal metrics
            exclude_cols = {meal_type_col.lower(), recipe_name_col.lower()}
            other_columns = [col for col in df.columns if col.lower() not in exclude_cols]

            metric_cols = []
            text_cols = []

            for col in other_columns:
                col_lower = col.lower()
                # Only treat exact macro/calorie headers as small metrics widgets
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

            # Render all other text columns (Ingredients, Health Benefits, etc.) as full-width sections below
            for col in text_cols:
                val = recipe_row[col]
                if pd.notna(val) and str(val).strip() != "":
                    st.subheader(f"📌 {col}")
                    st.write(val)
                    st.markdown("")

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
