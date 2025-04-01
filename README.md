# Company Scraper

A Python script to scrape company information.

## Prerequisites

- Python 3.11
- pip (Python package installer)
- Google Maps API key

## Environment Setup

1. Create a `.env` file in the project root:
```bash
touch .env
```

2. Add the following environment variables to your `.env` file:
```env
GOOGLE_MAPS_API_KEY=your_maps_api_key_here
```

### Getting API Keys

1. **Google Maps API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Places API
     - Maps JavaScript API
   - Create credentials (API key)
   - Copy the API key to your `.env` file

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/abhishekkannan2509/company-scraper.git
cd company_scrapper
```

2. Create and activate a virtual environment:

For macOS/Linux:
```bash
python3.11 -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Git Setup

1. Initialize Git repository (if not already initialized):
```bash
git init
```

2. Add files to Git:
```bash
git add .
```

3. Make initial commit:
```bash
git commit -m "Initial commit"
```

4. Add remote repository (replace with your repository URL):
```bash
git remote add origin <repository-url>
```

5. Push to remote repository:
```bash
git push -u origin main
```

## Usage Examples

### Single Company Search

To search for a single company:

```bash
python main.py "Company Name" -e "Dubai" --output "company_data.json" --csv "company_summary.csv" --summary "company_summary.txt"
```

Example:
```bash
python main.py "Emirates Airlines" -e "Dubai" --output "emirates_data.json" --csv "emirates_summary.csv" --summary "emirates_summary.txt"
```

### Multiple Companies via CSV Input

1. Create a CSV file (e.g., `companies.csv`) with the following format:
```csv
company_name,emirate
Emirates Airlines,Dubai
Dubai Mall,Dubai
```

2. Run the script with the CSV file:
```bash
python main.py --input companies.csv --output "all_companies_data.json" --csv "all_companies_summary.csv" --summary "all_companies_summary.txt"
```

### Optional Arguments

- `--output`: Specify output JSON file for detailed company data
- `--csv`: Specify output CSV file for company summaries
- `--summary`: Specify output text file for formatted summaries
- `--domains`: List of domains to search for news (e.g., `--domains example.com example.org`)

## Deactivating the Virtual Environment

When you're done, you can deactivate the virtual environment:
```bash
deactivate
```