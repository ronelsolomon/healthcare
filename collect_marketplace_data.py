import os
from dotenv import load_dotenv
import requests
import pandas as pd
import json  # Added for better error debugging
import time  # Added for sleep functionality
import csv
import sys

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not found in environment variables. Please set it in the .env file.")

BASE_URL = "https://marketplace.api.healthcare.gov/api/v1"

plan_columns = [
    'id', 'name', 'premium', 'premium_w_credit', 'ehb_premium', 'pediatric_ehb_premium',
    'aptc_eligible_premium', 'metal_level', 'type', 'state', 'benefits', 'deductibles',
    'tiered_deductibles', 'disease_mgmt_programs', 'has_national_network', 'market', 'max_age_child',
    'moops', 'tiered_moops', 'product_division', 'benefits_url', 'brochure_url', 'formulary_url',
    'network_url', 'issuer', 'hsa_eligible', 'insurance_market', 'specialist_referral_required',
    'oopc', 'tobacco_lookback', 'suppression_state', 'guaranteed_rate', 'simple_choice',
    'quality_rating', 'is_ineligible', 'rx_3mo_mail_order', 'covers_nonhyde_abortion', 'service_area_id'
]


def extract_plan_columns(plan, columns):
    """Extract only the specified columns from a plan dictionary."""
    return {col: plan.get(col) for col in columns}

def get_marketplace_all_data(zipcode, age, gender, income, year, drug_query, state="NC", sleep_time=0.2):
    """
    Fetch marketplace data for the given parameters
    """
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
    # print("PLANS:", plans)

    # 3. Get drug RxCUI
    drug_auto_resp = requests.get(
        f"{BASE_URL}/drugs/autocomplete",
        params={"q": drug_query, "apikey": API_KEY}
    )
    drug_auto_resp.raise_for_status()
    drug_auto_data = drug_auto_resp.json()
    
    
    
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
            "plan": plan,              
            "coverage": drug_covered_data   
        })

        time.sleep(sleep_time)
    # print(all_plan_details)
    return {
        "county_fips": countyfips,
        "plans_count": len(plans),
        "all_plans": all_plan_details
    }


def save_to_json(data, output_file="healthcare_plans.json"):
    """
    Save the marketplace data to a JSON file.
    
    Args:
        data (dict): The data to save
        output_file (str): Path to the output JSON file
    """
    try:
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved data to {output_file}")
        return output_file
    except Exception as e:
        print(f"Error saving to JSON: {str(e)}")
        return None

import os
import csv
import ast

def extract_json_to_csvs(json_file_path, output_dir="exported_csvs"):
    # Load JSON content (Python-style) safely
    with open(json_file_path, "r") as f:
        content = f.read()
        data = ast.literal_eval(content)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize data containers
    plans, benefits, cost_sharings = [], [], []
    deductibles, moops, issuers = [], [], []

    # Helper function to write CSVs
    def save_csv(data_list, filename):
        if not data_list:
            return
        keys = data_list[0].keys()
        with open(os.path.join(output_dir, filename), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data_list)

    # Parse all plans
    for plan_wrapper in data["all_plans"]:
        plan = plan_wrapper["plan"]
        issuer = plan.get("issuer", {})

        plans.append({
            "plan_id": plan.get("id"),
            "plan_name": plan.get("name"),
            "premium": plan.get("premium"),
            "metal_level": plan.get("metal_level"),
            "type": plan.get("type"),
            "state": plan.get("state"),
            "product_division": plan.get("product_division"),
            "insurance_market": plan.get("insurance_market"),
            "hsa_eligible": plan.get("hsa_eligible"),
            "has_national_network": plan.get("has_national_network"),
            "max_age_child": plan.get("max_age_child"),
        })

        issuers.append({
            "plan_id": plan.get("id"),
            "issuer_id": issuer.get("id"),
            "issuer_name": issuer.get("name"),
            "state": issuer.get("state"),
            "toll_free": issuer.get("toll_free"),
        })

        for benefit in plan.get("benefits", []):
            benefits.append({
                "plan_id": plan["id"],
                "benefit_name": benefit["name"],
                "covered": benefit.get("covered"),
                "has_limits": benefit.get("has_limits"),
                "limit_unit": benefit.get("limit_unit"),
                "limit_quantity": benefit.get("limit_quantity"),
            })

            for sharing in benefit.get("cost_sharings", []):
                cost_sharings.append({
                    "plan_id": plan["id"],
                    "benefit_name": benefit["name"],
                    "network_tier": sharing.get("network_tier"),
                    "copay_amount": sharing.get("copay_amount"),
                    "coinsurance_rate": sharing.get("coinsurance_rate"),
                    "display_string": sharing.get("display_string"),
                    "csr": sharing.get("csr"),
                })

        for deductible in plan.get("deductibles", []):
            deductibles.append({
                "plan_id": plan["id"],
                "type": deductible.get("type"),
                "amount": deductible.get("amount"),
                "network_tier": deductible.get("network_tier"),
                "family_cost": deductible.get("family_cost"),
            })

        for moop in plan.get("moops", []):
            moops.append({
                "plan_id": plan["id"],
                "type": moop.get("type"),
                "amount": moop.get("amount"),
                "network_tier": moop.get("network_tier"),
                "family_cost": moop.get("family_cost"),
            })

    # Save all extracted tables
    save_csv(plans, "plans.csv")
    save_csv(issuers, "issuers.csv")
    save_csv(benefits, "benefits.csv")
    save_csv(cost_sharings, "cost_sharings.csv")
    save_csv(deductibles, "deductibles.csv")
    save_csv(moops, "moops.csv")

    print(f"✅ Export complete. Files saved in: {output_dir}")

def main():
    """Main function to collect and store marketplace data"""
    try:
        # Collect data from the marketplace API
        print("Fetching marketplace data...")
        data = get_marketplace_all_data("27360", 27, "Female", 52000, 2019, "ibuprof")
        
        # Save raw JSON for reference
        json_file = "healthcare_plans.json"
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved raw data to {json_file}")
        
        # Save to SQLite database
        from db import save_marketplace_data, export_to_csv
        save_marketplace_data(data)
        
        # Export to CSV for easy access
        export_to_csv()
        print("Data collection and storage complete!")
        
        return True
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if "401" in str(e):
            print("Error: Invalid or missing API key. Please check your .env file.")
        elif "404" in str(e):
            print("Error: The requested resource was not found. Please check the API endpoint and parameters.")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--export-csv":
        # Just export existing database to CSV
        from db import export_to_csv
        export_to_csv()
    else:
        # Run full data collection
        success = main()
        sys.exit(0 if success else 1)