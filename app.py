import streamlit as st
import pandas as pd

st.title("🥗 Daily Meal Planner & Nutrition Tracker")
st.write("Select a meal category below to explore recipes, calories, and macronutrient breakdowns.")

# PUBLIC GOOGLE SHEET CSV LINK METHOD
# To make a Google Sheet readable publicly: Go to File > Share > Publish to web > Choose CSV format, then paste the link below:
@st.cache_data(ttl=600)
def load_data():
    # REPLACE this placeholder URL with your published Google Sheet CSV link
    sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/export?format=csv"
    df = pd.read_csv(sheet_url)
    return df

try:
    df = load_data()
    
    # 1. Main Selection: Breakfast, Lunch, or Dinner
    meal_category = st.radio("Choose Meal Time:", ["Breakfast", "Lunch", "Dinner"], horizontal=True)
    
    # Filter database based on selection
    filtered_df = df[df['MealType'].str.lower() == meal_category.lower()]
    
    if filtered_df.empty:
        st.info(f"No recipes found for {meal_category} yet. Add them to your Google Sheet!")
    else:
        st.markdown(iter_text := f"### Available {meal_category} Options")
        
        # 2. Select specific recipe option from dropdown or buttons
        recipe_list = filtered_df['RecipeName'].tolist()
        selected_recipe_name = st.selectbox(f"Select a {meal_category} recipe:", recipe_list)
        
        # Pull details for the selected recipe
        recipe_row = filtered_df[filtered_df['RecipeName'] == selected_recipe_name].iloc[0]
        
        st.divider()
        st.subheader(recipe_row['RecipeName'])
        
        # 3. Display Calories and Composition Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🔥 Calories", f"{recipe_row['Calories']} kcal")
        col2.metric("💪 Protein", f"{recipe_row['Protein (g)']} g")
        col3.metric("🌾 Carbs", f"{recipe_row['Carbs (g)']} g")
        col4.metric("🥑 Fats", f"{recipe_row['Fats (g)']} g")
        
        # 4. Show Ingredients and Recipe Steps
        st.markdown("#### 📝 Recipe & Ingredients")
        st.write(recipe_row['Ingredients & Instructions'])

except Exception as e:
    st.warning("Please connect your Google Sheet CSV link inside the code to load your live recipes.")
    with st.expander("See setup instructions"):
        st.write("1. Create a Google Sheet with columns: `MealType`, `RecipeName`, `Calories`, `Protein (g)`, `Carbs (g)`, `Fats (g)`, `Ingredients & Instructions`.")
        st.write("2. Publish the sheet to the web as a CSV (`File > Share > Publish to web > CSV`).")
        st.write("3. Paste the URL into the `sheet_url` variable in `app.py`.")
