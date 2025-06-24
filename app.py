import requests
import pandas as pd

def fetch_healthcare_data(dataset_id, limit=10):
    """
    Fetch data from Data.Healthcare.gov API
    
    Args:
        dataset_id (str): The ID of the dataset to fetch
        limit (int): Number of records to return (default: 10)
        
    Returns:
        pandas.DataFrame: A DataFrame containing the requested data
    """
    base_url = "https://data.medicaid.gov/api/1/metastore/schemas/dataset/items"
    
    try:
        # First, get the dataset information
        response = requests.get(f"{base_url}?identifier={dataset_id}")
        response.raise_for_status()
        dataset_info = response.json()
        
        # Extract the distribution URL
        distribution_url = None
        for distribution in dataset_info.get('distribution', []):
            if distribution.get('format', '').lower() == 'csv':
                distribution_url = distribution.get('downloadURL')
                break
        
        if not distribution_url:
            raise ValueError("No CSV distribution found for this dataset")
        
        # Download and read the CSV data
        data = pd.read_csv(distribution_url, nrows=limit)
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Example dataset ID (you can find these on data.medicaid.gov)
    # This is an example ID - replace with the actual dataset ID you want to query
    dataset_id = "72a84d9e-3daf-4e9e-9f62-8f7bde2abc7a"  # Example ID
    
    # Fetch data
    healthcare_data = fetch_healthcare_data(dataset_id, limit=5)
    
    if healthcare_data is not None:
        print("Successfully fetched healthcare data:")
        print(healthcare_data.head())
    else:
        print("Failed to fetch healthcare data")