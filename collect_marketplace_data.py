import os
from dotenv import load_dotenv
import requests
import pandas as pd
import json  # Added for better error debugging
import time  # Added for sleep functionality

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv('API_KEY')
BASE_URL = "https://marketplace.api.healthcare.gov/api/v1"
def get_marketplace_all_data(zipcode, age, gender, income, year, drug_query, state="NC", sleep_time=0.2):
    # 1. Get county FIPS for ZIP code
    fips_resp = requests.get(
        f"{BASE_URL}/counties/by/zip/{zipcode}",
        params={"apikey": API_KEY}
    )
    fips_resp.raise_for_status()
    fips_data = fips_resp.json()
    countyfips = fips_data['counties'][0]['fips']

    # 2. Search for all plans
    search_payload = {
        "household": {
            "income": income,
            "people": [
                {
                    "age": age,
                    "aptc_eligible": True,
                    "gender": gender,
                    "uses_tobacco": False
                }
            ]
        },
        "market": "Individual",
        "place": {
            "countyfips": countyfips,
            "state": state,
            "zipcode": zipcode
        },
        "year": year
    }
    plans_resp = requests.post(
        f"{BASE_URL}/plans/search",
        params={"apikey": API_KEY},
        json=search_payload,
        headers={"Content-Type": "application/json"}
    )
    plans_resp.raise_for_status()
    plans_data = plans_resp.json()
    plans = plans_data.get('plans', [])

    # 3. Get drug RxCUI
    drug_auto_resp = requests.get(
        f"{BASE_URL}/drugs/autocomplete",
        params={"q": drug_query, "apikey": API_KEY}
    )
    drug_auto_resp.raise_for_status()
    drug_auto_data = drug_auto_resp.json()
    
    # Debug: Print the API response to understand its structure
    print("\nDrug Autocomplete API Response:")
    print(json.dumps(drug_auto_data, indent=2))
    
    if not drug_auto_data or not isinstance(drug_auto_data, list) or len(drug_auto_data) == 0:
        raise Exception(f"No drug found for query: {drug_query}")
        
    rxcui = drug_auto_data[0]['rxcui']  # Take the first match

    # 4. For each plan, get details and drug coverage
    all_plan_details = []
    for plan in plans:
        plan_id = plan['id']

        # Get plan details
        plan_details_resp = requests.get(
            f"{BASE_URL}/plans/{plan_id}",
            params={"year": year, "apikey": API_KEY}
        )
        plan_details_resp.raise_for_status()
        plan_details = plan_details_resp.json()

        # Check drug coverage
        drug_covered_resp = requests.get(
            f"{BASE_URL}/drugs/covered",
            params={
                "year": year,
                "drugs": rxcui,
                "planids": plan_id,
                "apikey": API_KEY
            }
        )
        drug_covered_resp.raise_for_status()
        drug_covered_data = drug_covered_resp.json()

        all_plan_details.append({
            "plan_summary": plan,
            "plan_details": plan_details,
            "drug_coverage": drug_covered_data
        })

        # To avoid hitting rate limits, sleep between requests
        time.sleep(sleep_time)

    return {
        "county_fips": countyfips,
        "plans_count": len(plans),
        "all_plans": all_plan_details
    }

    import csv
import os

def append_to_csv(data, filename="marketplace_data.csv"):
    # Flatten and select relevant fields for CSV
    for plan in data['all_plans']:
        row = {
            "county_fips": data['county_fips'],
            "plan_id": plan['plan_summary']['id'],
            "plan_name": plan['plan_summary']['name'],
            "drug_covered": plan['drug_coverage'].get('covered', False),
            # Add more fields as needed
        }
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)