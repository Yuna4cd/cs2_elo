import requests

# Leetify Public CS API： https://api-public-docs.cs-prod.leetify.com/?ref=leetify.com#/player/get_v3_profile
# Leetify API Developer Guidelines: https://leetify.com/blog/leetify-api-developer-guidelines/

# sample: {'aim': 40.5165, 'positioning': 42.074, 'utility': 62.318, 'clutch': 0.0816, 'opening': -0.0197, 'ct_leetify': -0.0312, 't_leetify': -0.028}

LEETIFY_API_KEY="dummy1234"

def fetch_leetify_rating_by_leetify_id(leetify_id) -> dict:

    url = "https://api-public.cs-prod.leetify.com/v3/profile"

    params = {
        "id": leetify_id,
    }

    headers = {
        "accept": "application/json",
        "_leetify_key": LEETIFY_API_KEY,
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    # Raise an error for bad responses
    response.raise_for_status()
    
    data = response.json()

    if "rating" not in data:
        raise ValueError("Invalid response structure: 'rating' key not found")

    return data["rating"]

if __name__ == "__main__":
    leetify_id="76561198410951348"
    ratings = fetch_leetify_rating_by_leetify_id(leetify_id)

    print(ratings)
