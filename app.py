import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select a meal time below to explore recipes, calorie intake, and macronutrient composition.")

# Direct CSV export URL for your Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1aTt0FZH5F-w0fx18tYkeWauSbJ1S4JjwvPfrVbQBbCU/export?format=csv&gid=0"

@st.cache_data(ttl=60)  # Refresh data every 60 seconds automatically
def load_meal_data():
    data = pd.read_csv(SHEET_CSV_URL)
    # Clean up column names to avoid whitespace/casing mismatches
    data.columns = [c.strip() for c in data.columns]
    return data

try:
    df = load_meal_data()

    # Match MealType column dynamically (case-insensitive)
    meal_type_col = next((c for c in df.columns if c.lower() in ["mealtype", "meal_type", "meal type", "meal"]), None)
    recipe_name_col = next((c for c in df.columns if c.lower() in ["recipename", "recipe_name", "recipe name", "recipe", "item", "dish"]), None)

    if not meal_type_col or not recipe_name_col:
        st.error("Could not find standard columns. Please ensure your sheet has 'MealType' and 'RecipeName' column headers.")
        st.write("Current columns detected:", list(df.columns))
    else:
        # 1. Main Category: Breakfast, Lunch, Dinner
        meal_category = st.radio(
            "Choose Meal Time:",
            ["Breakfast", "Lunch", "Dinner"],
            horizontal=True
        )

        # Filter database by selected meal type
        filtered_df = df[df[meal_type_col].astype(str).str.strip().str.lower() == meal_category.lower()]

        if filtered_df.empty:
            st.info(f"No recipes found for **{meal_category}** yet. Add rows in your Google Sheet under MealType '{meal_category}'!")
        else:
            st.markdown(f"### Select an option for {meal_category}")
            
            # 2. Recipe Option Selector
            recipe_list = filtered_df[recipe_name_col].dropna().unique().tolist()
            selected_recipe = st.selectbox(f"Available {meal_category} Options:", recipe_list)

            # Get the row details for the selected recipe
            recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

            st.divider()
            st.header(f"🍽️ {recipe_row[recipe_name_col]}")

            # 3. Dynamic Nutrition & Calorie Metrics
            cal_col = next((c for c in df.columns if "calorie" in c.lower() or "kcal" in c.lower()), None)
            protein_col = next((c for c in df.columns if "protein" in c.lower()), None)
            carbs_col = next((c for c in df.columns if "carb" in c.lower()), None)
            fat_col = next((c for c in df.columns if "fat" in c.lower()), None)

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            if cal_col:
                m_col1.metric("🔥 Calories", f"{recipe_row[cal_col]} kcal")
            if protein_col:
                m_col2.metric("💪 Protein", f"{recipe_row[protein_col]} g")
            if carbs_col:
                m_col3.metric("🌾 Carbs", f"{recipe_row[carbs_col]} g")
            if fat_col:
                m_col4.metric("🥑 Fats", f"{recipe_row[fat_col]} g")

            st.divider()

            # 4. Recipe, Ingredients & Instructions
            desc_col = next((c for c in df.columns if any(k in c.lower() for k in ["recipe", "ingredient", "instruction", "detail", "method", "composition"]) and c != recipe_name_col), None)
            
            st.subheader("📝 Recipe Details & Instructions")
            if desc_col and pd.notna(recipe_row[desc_col]):
                st.write(recipe_row[desc_col])
            else:
                st.write("No recipe description entered for this item in the sheet.")

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
