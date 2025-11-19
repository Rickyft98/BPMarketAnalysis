import requests
import pandas as pd
import json

def get_all_recipes(main_category=""):
    all_recipes = []
    page = 1
    
    while True:
        params = {
            "language": "en",
            "page": page,
            "mainCategory": main_category,
            "subCategory": "",
            "facets": {}
        }
        
        base_url = 'https://questlog.gg/blue-protocol/api/trpc/database.getRecipes'
        r = requests.get(base_url, params={'input': json.dumps(params)})
        data = r.json()
        
        recipes = data['result']['data']['pageData']
        
        if not recipes:  # No more recipes
            break
            
        all_recipes.extend(recipes)
        print(f"Page {page}: {len(recipes)} recipes")
        
        # Check if we've reached the last page
        current_page = data['result']['data']['currentPage']
        total_pages = data['result']['data']['pageCount']
        
        if current_page >= total_pages:
            break
            
        page += 1
    
    return all_recipes

# Get ALL recipes
print("Downloading all recipes...")
all_recipes = get_all_recipes("culinary")
df = pd.DataFrame(all_recipes)

print(f"Total recipes: {len(df)}")
df.to_csv('all_recipes.csv', index=False)
print("Saved all recipes to all_recipes.csv")