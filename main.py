import os
import streamlit as st
from mistralai import Mistral
from datetime import datetime
import json
import pandas as pd
from collections import defaultdict
from env import api_key

client = Mistral(api_key=api_key)

# Enhanced categories with dietary tags and cooking difficulty
INGREDIENT_CATEGORIES = {
    "Vegetables": {
        "items": ["Tomato", "Onion", "Garlic", "Spinach", "Potato", "Carrot", "Bell Pepper", "Mushroom"],
        "tags": ["vegan", "vegetarian", "healthy"]
    },
    "Proteins": {
        "items": ["Eggs", "Chicken", "Tofu", "Beef", "Fish", "Lentils"],
        "tags": ["high-protein"]
    },
    "Dairy": {
        "items": ["Milk", "Cheese", "Yogurt", "Butter"],
        "tags": ["vegetarian"]
    },
    "Pantry": {
        "items": ["Rice", "Pasta", "Flour", "Oil", "Salt", "Pepper"],
        "tags": ["staples"]
    },
    "Herbs": {
        "items": ["Basil", "Oregano", "Thyme", "Cilantro", "Parsley"],
        "tags": ["flavor-enhancer"]
    }
}

# Enhanced ingredient relationships with flavor profiles and cooking methods
INGREDIENT_PROFILES = {
    "Tomato": {
        "pairs_with": ["Basil", "Garlic", "Onion", "Cheese"],
        "flavor_profile": ["acidic", "sweet"],
        "cooking_methods": ["raw", "roasted", "sautéed"]
    },
    "Chicken": {
        "pairs_with": ["Garlic", "Onion", "Bell Pepper", "Thyme"],
        "flavor_profile": ["savory"],
        "cooking_methods": ["grilled", "baked", "pan-fried"]
    }
    # Add more profiles as needed
}

class RecipeManager:
    def __init__(self):
        self.load_history()
        
    def load_history(self):
        """Load or initialize recipe history"""
        if 'recipe_history.json' in os.listdir('.'):
            with open('recipe_history.json', 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
            
    def save_history(self):
        """Save recipe history"""
        with open('recipe_history.json', 'w') as f:
            json.dump(self.history, f)
            
    def add_recipe(self, recipe_data):
        """Add recipe to history with metadata"""
        recipe_entry = {
            'recipe': recipe_data,
            'timestamp': datetime.now().isoformat(),
            'ingredients': st.session_state.selected_ingredients,
            'likes': 0,
            'dietary_tags': self.get_dietary_tags()
        }
        self.history.append(recipe_entry)
        self.save_history()
        
    def get_dietary_tags(self):
        """Analyze ingredients for dietary tags"""
        all_tags = set()
        for ingredient in st.session_state.selected_ingredients:
            for category in INGREDIENT_CATEGORIES.values():
                if ingredient in category['items']:
                    all_tags.update(category['tags'])
        return list(all_tags)
    
    def get_cooking_methods(self):
        """Suggest cooking methods based on ingredients"""
        methods = set()
        for ingredient in st.session_state.selected_ingredients:
            if ingredient in INGREDIENT_PROFILES:
                methods.update(INGREDIENT_PROFILES[ingredient]['cooking_methods'])
        return list(methods)

def get_recipe(ingredients, cooking_method=None, difficulty=None):
    """Enhanced recipe generation with cooking method and difficulty preferences"""
    prompt = f"""
    Create a detailed recipe using these ingredients: {', '.join(ingredients)}.
    {'Use this cooking method: ' + cooking_method if cooking_method else ''}
    {'Target difficulty level: ' + difficulty if difficulty else ''}
    
    Include:
    - Creative recipe name
    - Preparation time
    - Cooking time
    - Difficulty level
    - Calorie estimate
    - Detailed step-by-step instructions
    - Pro tips and variations
    - Plating suggestions
    - Wine pairing (if appropriate)
    - Storage instructions
    
    Use metric measurements and casual cooking style.
    """
    
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def analyze_nutrition(ingredients):
    """Estimate nutritional content of recipe"""
    # This would ideally use a nutrition API - for now using placeholder data
    nutrition_data = {
        'calories': sum([len(ingredient) * 10 for ingredient in ingredients]),  # Placeholder calculation
        'protein': len([i for i in ingredients if i in INGREDIENT_CATEGORIES['Proteins']['items']]) * 15,
        'carbs': len([i for i in ingredients if i in INGREDIENT_CATEGORIES['Pantry']['items']]) * 20
    }
    return nutrition_data

def main():
    st.set_page_config(page_title="Advanced Recipe Generator", layout="wide")
    
    # Initialize session state and recipe manager
    if 'selected_ingredients' not in st.session_state:
        st.session_state.selected_ingredients = []
    if 'available_ingredients' not in st.session_state:
        st.session_state.available_ingredients = {k: v['items'] for k, v in INGREDIENT_CATEGORIES.items()}
    
    recipe_manager = RecipeManager()

    # Sidebar with enhanced controls
    with st.sidebar:
        st.header("🧑‍🍳 Advanced Recipe Generator")
        
        # Difficulty preference
        difficulty = st.select_slider(
            "Preferred Difficulty",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate"
        )
        
        # Dietary preferences
        dietary_prefs = st.multiselect(
            "Dietary Preferences",
            ["Vegetarian", "Vegan", "High-Protein", "Low-Carb"]
        )
        
        st.subheader("Select Your Ingredients")
        
        # Smart ingredient filtering
        for category, items in st.session_state.available_ingredients.items():
            selected = st.multiselect(
                f"{category}:",
                items,
                key=f"category_{category}"
            )
            
            for item in selected:
                if item not in st.session_state.selected_ingredients:
                    st.session_state.selected_ingredients.append(item)
                    # Update available ingredients based on profiles
                    if item in INGREDIENT_PROFILES:
                        suggested_pairs = INGREDIENT_PROFILES[item]['pairs_with']
                        st.info(f"💡 Suggested pairings for {item}: {', '.join(suggested_pairs)}")

    # Main content area with three columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader("Recipe Setup")
        if st.session_state.selected_ingredients:
            st.write("Selected Ingredients:")
            for ingredient in st.session_state.selected_ingredients:
                st.markdown(f"- {ingredient}")
            
            # Cooking method suggestion
            cooking_methods = recipe_manager.get_cooking_methods()
            if cooking_methods:
                method = st.selectbox("Suggested Cooking Method:", cooking_methods)
            
            if st.button("Generate Recipe 🍳"):
                with st.spinner("Creating your culinary masterpiece..."):
                    recipe = get_recipe(
                        st.session_state.selected_ingredients,
                        cooking_method=method if cooking_methods else None,
                        difficulty=difficulty
                    )
                    nutrition = analyze_nutrition(st.session_state.selected_ingredients)
                    st.session_state.recipe = recipe
                    st.session_state.nutrition = nutrition
                    recipe_manager.add_recipe(recipe)
                    st.rerun()
        else:
            st.info("Select ingredients to begin your culinary journey!")

    with col2:
        if 'recipe' in st.session_state:
            st.subheader("Your Custom Recipe")
            st.markdown(st.session_state.recipe)
            
            # Interactive features
            col_act1, col_act2, col_act3 = st.columns(3)
            with col_act1:
                st.download_button(
                    "Download Recipe 📥",
                    st.session_state.recipe,
                    "generated_recipe.md",
                    "text/markdown"
                )
            with col_act2:
                if st.button("👍 Like"):
                    recipe_manager.history[-1]['likes'] += 1
                    recipe_manager.save_history()
            with col_act3:
                st.button("Share Recipe 🔗")

    with col3:
        if 'recipe' in st.session_state:
            st.subheader("Recipe Analytics")
            
            # Nutrition information
            st.write("Estimated Nutrition:")
            nutrition = st.session_state.nutrition
            st.metric("Calories", f"{nutrition['calories']} kcal")
            st.metric("Protein", f"{nutrition['protein']}g")
            st.metric("Carbs", f"{nutrition['carbs']}g")
            
            # Recipe history analytics
            st.write("Popular Combinations:")
            if recipe_manager.history:
                combinations = defaultdict(int)
                for entry in recipe_manager.history:
                    for i1 in entry['ingredients']:
                        for i2 in entry['ingredients']:
                            if i1 < i2:
                                combinations[(i1, i2)] += 1
                
                top_combos = sorted(combinations.items(), key=lambda x: x[1], reverse=True)[:3]
                for (i1, i2), count in top_combos:
                    st.write(f"• {i1} + {i2} ({count} times)")

if __name__ == "__main__":
    main()