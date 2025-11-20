import requests
import pandas as pd
import json

recipes_id=pd.read_csv('config/all_recipes.csv')
idrow=recipes_id['id'].tolist() #Database id collums from all recipes
AllYieldData = []

def get_all_recipes():
    all_recipes = []
   
    for i in enumerate(idrow):
        params = {
            "id": str(idrow[i]),
            "language": "en"
        }

    
        # Make request
        base_url = 'https://questlog.gg/blue-protocol/api/trpc/database.getRecipe'
        r = requests.get(base_url, params={'input': json.dumps(params)})
        data = r.json()
        


        # Process data
        Recipesinfo = data['result']['data']['recipeInputItems']
        input_items_flat = []
        for item_group in Recipesinfo:
            for item_data in item_group:
                input_items_flat.append({
                    'input_id': item_data['item']['id'],
                    'item_name': item_data['item']['name'],
                    'amount': item_data['amount'],
                    'isVariable': item_data['isVariable'],
                    'grade': item_data['item']['grade'],
                    'mainCategory': item_data['item']['mainCategory'],
                    'subCategory': item_data['item']['subCategory']
                })

        recipe_data = data['result']['data']  
        final_input = [{
            'id': recipe_data['id'],
            'name': recipe_data['name'],
            'icon': recipe_data['icon'],
            'grade': recipe_data['grade'],
            'dbType': recipe_data['dbType'],
            'mainCategory': recipe_data['mainCategory'],
            'description': recipe_data['description'],
            'FocusCost': recipe_data['cost']['amount'],
            'input_data': input_items_flat
        }]
        all_recipes.extend(final_input)

'''
# Get ALL recipes
print("Downloading all recipes...")
all_recipes = get_all_recipes("")
df = pd.DataFrame(all_recipes)

print(f"Total recipes: {len(df)}")
df.to_csv('all_collectable.csv', index=False)
print("Saved all recipes to all_collectable.csv")
'''