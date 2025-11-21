import requests
import pandas as pd
import json
import time

recipes_id = pd.read_csv('config/all_recipes.csv')
idrow = recipes_id['id'].tolist()

def get_all_recipes():
    all_recipes = []

    for i, row in enumerate(idrow, start=1):
        params = {"id": str(row), "language": "en"}

        base_url = 'https://questlog.gg/blue-protocol/api/trpc/database.getRecipe'
        try:
            r = requests.get(base_url, params={'input': json.dumps(params)}, timeout=10)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError) as e:
            print(f"Request/JSON error for id {row} (index {i}): {e}")
            time.sleep(1)
            continue

        recipe_data = data.get('result', {}).get('data')
        if not recipe_data:
            print(f"No recipe data for id {row} (index {i})")
            time.sleep(1)
            continue

        # Process INPUT data
        Recipesinfoinput = recipe_data.get('recipeInputItems', [])
        input_items_flat = []
        for item_group in Recipesinfoinput:
            for item_data in item_group:
                item = item_data.get('item', {})
                input_items_flat.append({
                    'input_id': item.get('id'),
                    'item_name': item.get('name'),
                    'amount': item_data.get('amount'),
                    'isVariable': item_data.get('isVariable', False),
                    'grade': item.get('grade'),
                    'mainCategory': item.get('mainCategory'),
                    'subCategory': item.get('subCategory')
                })

        # Process OUTPUT data
        RecipesInfoOutput = recipe_data.get('recipeOutputItems', [])
        output_items_flat = []
        for output_item in RecipesInfoOutput:
            item = output_item.get('item', {})
            output_items_flat.append({
                'output_id': item.get('id'),
                'item_name': item.get('name'),
                'rate': output_item.get('rate'),
                'isVariable': output_item.get('isVariable', False),
                'grade': item.get('grade'),
                'maxAmount': item.get('maxAmount'),
                'minAmount': item.get('minAmount'),
                'mainCategory': item.get('mainCategory'),
                'subCategory': item.get('subCategory'),
                'amount': output_item.get('amount')
            })

        final_input = {
            'id': recipe_data.get('id'),
            'name': recipe_data.get('name'),
            'icon': recipe_data.get('icon'),
            'grade': recipe_data.get('grade'),
            'dbType': recipe_data.get('dbType'),
            'mainCategory': recipe_data.get('mainCategory'),
            'description': recipe_data.get('description'),
            'FocusCost': recipe_data.get('cost', {}).get('amount'),
            'input_data': input_items_flat,
            'output_data': output_items_flat
        }

        all_recipes.append(final_input)
        print(f"Processed recipe {i}/{len(idrow)}: {final_input['name']} (ID: {final_input['id']})")
        time.sleep(1)
        
    return all_recipes


if __name__ == '__main__':
    print("Downloading all recipes...")
    all_recipes = get_all_recipes()
    df = pd.DataFrame(all_recipes)
    print(f"Total recipes: {len(df)}")
    df.to_json('RecipesData.json', orient='records', indent=2)
    print("Saved to RecipesData.json")