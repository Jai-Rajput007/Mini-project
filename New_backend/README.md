# Safex Vulnerability Scanner Backend

This is the backend for the Safex Web Vulnerability Scanner application.

## Setup

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. The application comes with pre-configured MongoDB credentials in the `.env.example` file. 
   Create a copy of this file to use these credentials:
   ```
   cp .env.example .env   # Linux/Mac
   Copy-Item .env.example .env  # Windows
   ```

## MongoDB Connection

The application uses a MongoDB Atlas cluster with the following pre-configured credentials:
- Username: jaisrajputdev
- Password: newpass1234
- Cluster: mycluster.7ay65.mongodb.net

You can test the MongoDB connection by running:
```
python test_connection.py
```

If you want to use your own MongoDB instance, update the connection string in your `.env` file.

## Running the Backend

### Correct Way to Start the Backend

Always use the `run.py` script from the project root to start the backend:

```bash
python run.py
```

This will:
- Start the FastAPI server on port 8000 (default)
- Connect to the MongoDB database
- Initialize all necessary services

### Important Notes

- Do NOT run `app/main.py` directly - always use `run.py`
- Make sure MongoDB is properly configured
- The API will be available at: http://localhost:8000
- API documentation is available at: http://localhost:8000/docs

## Testing the Backend

You can test the backend with the included test scripts:

```bash
# Test a basic scan
python test_minimal.py

# Full test of all endpoints
python test_api.py
```

## API Endpoints

The main API endpoints are:

- `/api/v1/scanner/start` - Start a new scan (POST)
- `/api/v1/scanner/{scan_id}` - Get scan status (GET)
- `/api/v1/scanner/{scan_id}/result` - Get scan results (GET)
- `/api/v1/reports/generate` - Generate a report (POST)
- `/api/v1/reports/{report_id}/export/{format}` - Export a report (GET)

See the API documentation for a complete list of endpoints.

## Troubleshooting

1. If you see database connection errors, run `python test_connection.py` to diagnose MongoDB connectivity issues
2. If scanners are timing out, try reducing the number of scanners you're using in a single scan
3. For more detailed logs, set the log level to "debug" in `run.py` 