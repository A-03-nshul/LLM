# main.py
import json
import re
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn

# --- 1. Application Setup ---
app = FastAPI(
    title="DataWise LLM Analytics",
    description="API to query sales data using natural language.",
    version="1.0.0"
)

# --- 2. CORS Configuration ---
# Enable Cross-Origin Resource Sharing for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Data Loading ---
# Load the dataset into a pandas DataFrame when the application starts.
# This is efficient as the data is loaded only once.
try:
    with open('q-fastapi-llm-query.json', 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    # Convert sales to numeric and date to datetime objects for proper querying
    df['sales'] = pd.to_numeric(df['sales'])
    df['date'] = pd.to_datetime(df['date'])
except FileNotFoundError:
    print("Error: 'q-fastapi-llm-query.json' not found. Please place it in the same directory.")
    df = pd.DataFrame() # Create an empty DataFrame to avoid crashing the app

# --- 4. Question Analysis Logic ---
def answer_question(question: str):
    """
    Parses a natural language question, queries the DataFrame, and returns the answer.
    """
    # Pattern 1: Total sales of [Product] in [City]?
    match = re.search(r"What is the total sales of (\w+) in (\w+)\?", question, re.IGNORECASE)
    if match:
        product, city = match.groups()
        result = df[(df['product'] == product) & (df['city'] == city)]['sales'].sum()
        return int(result)

    # Pattern 2: How many sales reps are there in [Region]?
    match = re.search(r"How many sales reps are there in ([\w\s]+)\?", question, re.IGNORECASE)
    if match:
        region = match.groups()[0]
        # Get the number of unique sales reps in the specified region
        result = df[df['region'] == region]['rep'].nunique()
        return int(result)

    # Pattern 3: Average sales for [Product] in [Region]?
    match = re.search(r"What is the average sales for (\w+) in ([\w\s]+)\?", question, re.IGNORECASE)
    if match:
        product, region = match.groups()
        result = df[(df['product'] == product) & (df['region'] == region)]['sales'].mean()
        return round(result, 2) if not pd.isna(result) else 0

    # Pattern 4: On what date did [Rep Name] make the highest sale in [City]?
    match = re.search(r"On what date did ([\w\s.'-]+) make the highest sale in ([\w\s]+)\?", question, re.IGNORECASE)
    if match:
        rep, city = match.groups()
        # Filter by rep and city, then find the row with the maximum sales
        subset = df[(df['rep'] == rep) & (df['city'] == city)]
        if not subset.empty:
            highest_sale_row = subset.loc[subset['sales'].idxmax()]
            return highest_sale_row['date'].strftime('%Y-%m-%d')
        else:
            return "No sales data found for this rep in this city."

    return "Sorry, I can't answer that question."

# --- 5. API Endpoint Definition ---
@app.get("/query")
async def handle_query(request: Request, response: Response, q: str):
    """
    Accepts a natural language query via the 'q' parameter,
    analyzes it, and returns the answer from the sales dataset.
    """
    email_address = "22f3003185@ds.study.iitm.ac.in"
    
    # Add the custom X-Email header to the response
    response.headers["X-Email"] = email_address
    
    if df.empty:
        return {"answer": "Error: Dataset not loaded.", "email": email_address}
        
    answer = answer_question(q)
    
    # The error message suggests the email must also be in the JSON body.
    return {"answer": answer, "email": email_address}

# --- 6. Running the Application ---
# To run this app:
# 1. Save the code as `main.py`.
# 2. Place the `q-fastapi-llm-query.json` file in the same directory.
# 3. Create a `requirements.txt` file with:
#    fastapi
#    uvicorn
#    pandas
#    python-multipart
# 4. Run `uvicorn main:app --reload` in your terminal.
# 5. The API will be live at http://127.0.0.1:8000

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
