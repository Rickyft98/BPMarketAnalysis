import requests
import pandas as pd
import json

# Define parameters
params = {
    "language": "en",
    "page": 2,
    "mainCategory": "",  # Change this
}

base_url = 'https://questlog.gg/blue-protocol/api/trpc/database.getCollectables'

# requests will encode it automatically
r = requests.get(base_url, params={'input': json.dumps(params)})
data = r.json()
recipes = data['result']['data']['pageData']

df = pd.DataFrame(recipes)
# Save to JSON file
df.to_json('DBrecipes.json', orient='records', indent=2)

print("Saved to recipes.json")
