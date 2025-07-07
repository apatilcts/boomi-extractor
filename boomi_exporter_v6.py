import requests
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# --- Configuration ---
# This script loads credentials from a .env file in the same directory.
# 1. Make sure you have the python-dotenv library installed: pip install python-dotenv
# 2. Create a file named .env and add your credentials like this:
#
# BOOMI_ACCOUNT_ID="your_boomi_account_id"
# BOOMI_USERNAME="your_boomi_username"
# BOOMI_API_TOKEN="your_boomi_api_token"
#

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
BOOMI_ACCOUNT_ID = os.getenv("BOOMI_ACCOUNT_ID")
BOOMI_USERNAME = os.getenv("BOOMI_USERNAME")
BOOMI_API_TOKEN = os.getenv("BOOMI_API_TOKEN")

# Base URL for the Boomi AtomSphere API - will be constructed after validation
BASE_URL = "" 

# Directory where the exported components will be saved
EXPORT_DIRECTORY = "boomi_export"

# --- Helper Functions ---

def make_api_request(endpoint, method='POST', payload=None):
    """
    Makes an authenticated request to the Boomi API using JSON.
    This is used for the initial query.
    
    Args:
        endpoint (str): The API endpoint to call (e.g., '/ComponentMetadata').
        method (str): The HTTP method to use ('GET' or 'POST').
        payload (dict): The request payload for POST requests.

    Returns:
        dict: The JSON response from the API, or None if the request fails.
    """
    url = BASE_URL + endpoint
    auth = (f"BOOMI_TOKEN.{BOOMI_USERNAME}", BOOMI_API_TOKEN)
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    try:
        if method.upper() == 'POST':
            response = requests.post(url, auth=auth, headers=headers, json=payload)
        elif method.upper() == 'GET':
            response = requests.get(url, auth=auth, headers=headers)
        else:
            print(f"Error: Unsupported HTTP method '{method}'")
            return None

        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
    
    return None

def get_all_components():
    """
    Queries the Boomi API to get metadata for all components.
    It handles pagination to retrieve all results.

    Returns:
        list: A list of all component metadata objects.
    """
    print("Fetching all component metadata...")
    all_components = []
    
    # FIX: Modified query to only fetch the LATEST version of each component.
    # This provides a cleaner export and helps avoid pagination issues.
    initial_payload = {
        "QueryFilter": {
            "expression": {
                "operator": "and",
                "nestedExpression": [
                    {
                        "argument": ["false"],
                        "operator": "EQUALS",
                        "property": "deleted"
                    },
                    {
                        "argument": ["true"],
                        "operator": "EQUALS",
                        "property": "currentVersion"
                    }
                ]
            }
        }
    }

    # Make the first request using the JSON helper
    response = make_api_request('/ComponentMetadata/query', method='POST', payload=initial_payload)

    if not response or 'result' not in response:
        print("Failed to fetch initial component metadata or no results found.")
        return []

    # Process the first page of results
    all_components.extend(response['result'])
    print(f"  ...retrieved {len(all_components)} components so far.")

    query_token = response.get('queryToken')

    # Loop to get subsequent pages using the queryToken
    while query_token:
        # For subsequent paged requests, the Boomi API expects a specific XML payload with a namespace.
        more_payload_xml = f'<QueryMoreRequest xmlns="http://api.platform.boomi.com/api/rest/v1/"><queryToken>{query_token}</queryToken></QueryMoreRequest>'
        
        url = BASE_URL + '/ComponentMetadata/query'
        auth = (f"BOOMI_TOKEN.{BOOMI_USERNAME}", BOOMI_API_TOKEN)
        # We send XML, but we still want a JSON response back.
        headers = {'Accept': 'application/json', 'Content-Type': 'application/xml'}
        
        try:
            response_obj = requests.post(url, auth=auth, headers=headers, data=more_payload_xml.encode('utf-8'))
            response_obj.raise_for_status()
            response = response_obj.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred during pagination: {http_err}")
            print(f"Response content: {response_obj.text}")
            response = None
            break # Exit loop on error
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during pagination: {req_err}")
            response = None
            break # Exit loop on error

        if not response or 'result' not in response:
            print("Failed to fetch subsequent page of component metadata.")
            break
        
        all_components.extend(response['result'])
        print(f"  ...retrieved {len(all_components)} components so far.")

        # Get the next token for the next iteration
        query_token = response.get('queryToken')
            
    print(f"Total components found: {len(all_components)}")
    return all_components

def get_component_definition(component_id):
    """
    Fetches the XML definition of a single component.

    Args:
        component_id (str): The ID of the component to fetch.

    Returns:
        str: The component's XML definition, or None on failure.
    """
    if not component_id:
        print("  -> ERROR: Attempted to fetch a component with a null or empty ID.")
        return None
        
    endpoint = f"/Component/{component_id}"
    url = BASE_URL + endpoint
    auth = (f"BOOMI_TOKEN.{BOOMI_USERNAME}", BOOMI_API_TOKEN)
    headers = {'Accept': 'application/xml'} # Request XML for the definition

    try:
        response = requests.get(url, auth=auth, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching component {component_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred while fetching component {component_id}: {req_err}")
        
    return None

def sanitize_name(name):
    """Removes invalid characters from a string to make it a valid folder or filename."""
    # Replace invalid characters with an underscore
    return "".join(c if c.isalnum() or c in (' ', '.', '_', '-') else '_' for c in name).rstrip()

# --- Main Execution ---

def main():
    """
    Main function to run the export process.
    """
    global BASE_URL
    # Basic validation for environment variables
    if not all([BOOMI_ACCOUNT_ID, BOOMI_USERNAME, BOOMI_API_TOKEN]):
        print("Error: One or more environment variables are missing.")
        print("Please create a .env file with BOOMI_ACCOUNT_ID, BOOMI_USERNAME, and BOOMI_API_TOKEN.")
        return

    # Construct the BASE_URL now that we have the account ID
    BASE_URL = f"https://api.boomi.com/api/rest/v1/{BOOMI_ACCOUNT_ID}"

    # Create the main export directory if it doesn't exist
    if not os.path.exists(EXPORT_DIRECTORY):
        os.makedirs(EXPORT_DIRECTORY)
        print(f"Created export directory: {EXPORT_DIRECTORY}")

    # 1. Get the list of all components
    components = get_all_components()
    if not components:
        print("No components to export. Exiting.")
        return

    # 2. Iterate through each component, get its definition, and save it
    print("\nStarting component export process...")
    for i, comp_meta in enumerate(components):
        component_id = comp_meta.get('componentId')
        component_name = comp_meta.get('name', 'Unnamed Component')
        version = comp_meta.get('version') 

        # Add a check for missing ID to make the script more robust
        if not component_id:
            print(f"\n({i+1}/{len(components)}) SKIPPING: Component '{component_name}' is missing an ID. Full metadata: {comp_meta}")
            continue

        component_type = comp_meta.get('type')
        folder_name = comp_meta.get('folderName', 'No Folder')
        
        print(f"\n({i+1}/{len(components)}) Exporting: '{component_name}' v{version} (ID: {component_id})")
        print(f"  Type: {component_type}, Folder: {folder_name}")

        # Sanitize the folder name to prevent errors on creation
        sanitized_folder = sanitize_name(folder_name)
        local_folder_path = os.path.join(EXPORT_DIRECTORY, sanitized_folder.replace('/', os.sep))
        if not os.path.exists(local_folder_path):
            try:
                os.makedirs(local_folder_path)
            except OSError as e:
                print(f"  -> ERROR: Could not create directory {local_folder_path}. Reason: {e}")
                continue # Skip to the next component

        # Get the component's XML definition
        component_xml = get_component_definition(component_id)

        if component_xml:
            # Save the XML to a file
            sanitized_name = sanitize_name(component_name)
            # Include version in the filename to make it unique
            file_name = f"{sanitized_name}_v{version}_{component_id}.xml"
            file_path = os.path.join(local_folder_path, file_name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(component_xml)
                print(f"  -> Successfully saved to: {file_path}")
            except IOError as e:
                print(f"  -> ERROR: Could not write to file {file_path}. Reason: {e}")
        else:
            print(f"  -> ERROR: Failed to retrieve definition for component {component_id}.")

    print("\nExport process complete!")


if __name__ == "__main__":
    main()
