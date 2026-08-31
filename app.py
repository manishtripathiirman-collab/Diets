import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Meal Planner & Nutrition Tracker", page_icon="🥗", layout="centered")

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select a meal time below to explore recipes, nutrition details, and health benefits.")

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

    # Identify core columns dynamically
    meal_type_col = next((c for c in df.columns if c.lower() in ["mealtype", "meal_type", "meal type", "meal"]), None)
    recipe_name_col = next((c for c in df.columns if c.lower() in ["recipename", "recipe_name", "recipe name", "recipe", "item", "dish"]), None)

    if not meal_type_col or not recipe_name_col:
        st.error("Could not find standard columns. Please ensure your sheet has 'Meal Type' and 'Recipe Name' column headers.")
        st.write("Current columns detected:", list(df.columns))
    else:
        # 1. Main Category: Filter unique meal types available in the sheet
        available_meal_types = df[meal_type_col].dropna().astype(str).unique().tolist()
        
        # Let users select from the categories found in the sheet
        meal_category = st.selectbox("Choose Meal Category:", available_meal_types)

        # Filter database by selected meal type
        filtered_df = df[df[meal_type_col].astype(str).str.strip().str.lower() == meal_category.lower()]

        if filtered_df.empty:
            st.info(f"No recipes found for **{meal_category}** yet.")
        else:
            st.markdown(f"### Select an option for {meal_category}")
            
            # 2. Recipe Option Selector
            recipe_list = filtered_df[recipe_name_col].dropna().unique().tolist()
            selected_recipe = st.selectbox(f"Available Options:", recipe_list)

            # Get the row details for the selected recipe
            recipe_row = filtered_df[filtered_df[recipe_name_col] == selected_recipe].iloc[0]

            st.divider()
            st.header(f"🍽️ {recipe_row[recipe_name_col]}")

            # 3. Dynamic Display for ALL Other Columns (Calories, Macros, Health Benefits, etc.)
            # Exclude Meal Type and Recipe Name from this loop since they are already used above
            exclude_cols = {meal_type_col.lower(), recipe_name_col.lower()}
            
            other_columns = [col for col in df.columns if col.lower() not in exclude_cols]

            for col in other_columns:
                val = recipe_row[col]
                if pd.notna(val) and str(val).strip() != "":
                    # Check if the column sounds like a numeric metric (Calories, Protein, etc.)
                    col_lower = col.lower()
                    if any(metric in col_lower for metric in ["calorie", "kcal", "protein", "carb", "fat", "gram", "g"]):
                        # Display metrics nicely in small info blocks
                        st.metric(label=col, value=str(val))
                    else:
                        # Display text-based columns (Ingredients & Instructions, Health Benefits, etc.) as sections
                        st.subheader(f"📌 {col}")
                        st.write(val)
                    st.markdown("")

except Exception as e:
    st.error(f"Error loading Google Sheet: {e}")
    st.info("Tip: Make sure your Google Sheet is shared with **'Anyone with the link can view'** so Streamlit can read it.")
