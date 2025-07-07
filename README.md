# Boomi Component Export Tool

This Python script exports all components from your Dell Boomi AtomSphere account to local XML files, organized by folder structure.

## Prerequisites

- Python 3.6 or higher
- Boomi AtomSphere account with API access
- API Token generated from your Boomi account

## Installation

1. **Clone or download** this script to your local machine

2. **Install required dependencies**:
   ```bash
   pip install requests python-dotenv
   ```

3. **Create environment file** - Create a `.env` file in the same directory as the script:
   ```
   BOOMI_ACCOUNT_ID="your_boomi_account_id"
   BOOMI_USERNAME="your_boomi_username"
   BOOMI_API_TOKEN="your_boomi_api_token"
   ```

## Getting Your Boomi Credentials

### Account ID
- Log into your Boomi AtomSphere account
- The Account ID is visible in the URL: `https://platform.boomi.com/account/YOUR_ACCOUNT_ID`

### Username
- Your Boomi login username/email address

### API Token
1. In AtomSphere, go to **Manage** → **Account Information and Setup**
2. Click **API Token Management**
3. Generate a new API Token
4. Copy the token value (you won't be able to see it again)

## Usage

1. **Prepare your environment**:
   ```bash
   # Make sure you're in the script directory
   cd /path/to/boomi-export-script
   
   # Verify your .env file exists and has the correct credentials
   cat .env
   ```

2. **Run the script**:
   ```bash
   python boomi_export.py
   ```

3. **Monitor progress**:
   - The script will show progress as it fetches components
   - Components are saved to the `boomi_export` directory
   - Each component is saved as an XML file with format: `ComponentName_vVersion_ComponentID.xml`

## Output Structure

The script creates the following structure:
```
boomi_export/
├── FolderName1/
│   ├── Component1_v1.0_abc123.xml
│   └── Component2_v2.1_def456.xml
├── FolderName2/
│   └── Component3_v1.5_ghi789.xml
└── No Folder/
    └── UnorganizedComponent_v1.0_jkl012.xml
```

## What Gets Exported

- **All component types**: Processes, connections, connectors, maps, etc.
- **Latest versions only**: Only exports the current/published version of each component
- **XML definitions**: Complete component configuration in XML format
- **Folder organization**: Maintains your Boomi folder structure locally

## Troubleshooting

### Common Issues

**"Environment variables are missing"**
- Check that your `.env` file exists in the same directory as the script
- Verify all three variables are set: `BOOMI_ACCOUNT_ID`, `BOOMI_USERNAME`, `BOOMI_API_TOKEN`

**"HTTP error 401 Unauthorized"**
- Verify your API token is correct and hasn't expired
- Check that your username is correct
- Ensure your account has API access permissions

**"HTTP error 403 Forbidden"**
- Your account may not have sufficient permissions
- Contact your Boomi administrator to grant API access

**"Failed to fetch component metadata"**
- Check your internet connection
- Verify the account ID is correct
- Try running the script again (temporary network issues)


