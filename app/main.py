#pipenv install fastapi httpx
#pipenv shell
#uvicorn gsa_zip:app --reload
#http://127.0.0.1:8000/call_gsa_api?zip_code=92011&year=2024
#http://127.0.0.1:8000/call_gsa_api/calculate_perdiem?zip_code=92011&begin_date=2023-12-29&end_date=2024-01-02

from fastapi import FastAPI, Header
import httpx
from datetime import datetime
import asyncio  # Import the asyncio module

app = FastAPI()

X_API_KEY='imRuLjQ9Wvzte0ZsNWojJzGnnHdwlzMFR7TJZpXf' # your X API key
BASE_URL='https://api.gsa.gov/travel/perdiem/v2'

import json

MONTH_NUMBERS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def parse_and_display_rates(data):
    """
    Parses the provided JSON data containing rate information, displays it in a clean format,
    and returns the extracted data as a dictionary.

    Args:
        json_data (str): The JSON data as a string.

    Returns:
        dict: A dictionary containing the extracted rate information.
    """
    try:
        # Extract relevant fields
        rate_data = data['rates'][0]['rate'][0]
        extracted_data = {
            'city': rate_data['city'],
            'county': rate_data['county'],
            'state': data['rates'][0]['state'],
            'zip': rate_data['zip'],
            'year': data['rates'][0]['year'],
            'meals_rate': rate_data['meals'],
            'daily_hotel_rates_by_month': []
        }

        # Extract monthly rates with month numbers
        for month in rate_data['months']['month']:
            extracted_data['daily_hotel_rates_by_month'].append({
                'month_num': month['number'],
                'value': month['value']
            })

        # Display the extracted data
        print(f"Location: {extracted_data['city']}, {extracted_data['county']}, {extracted_data['state']} {extracted_data['zip']}")
        print(f"Year: {extracted_data['year']}")
        print(f"Meals Rate: ${extracted_data['meals_rate']:.2f}")

        print("\nDaily Hotels Rates by Each Month:")
        print("Month\tRate")
        print("----\t----")
        for month_rate in extracted_data['daily_hotel_rates_by_month']:
            print(f"{month_rate['month_num']}\t${month_rate['value']:.2f}")

        return extracted_data

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing JSON: {e}")
        return {}  # Return an empty dictionary in case of an error



@app.get("/")
async def root():
    current_time = datetime.now().strftime("%H:%M:%S")
    print("Root Run time is:", current_time)
    return {"message": "Welcome to the FAST API gsa_zip app"}
    
# @app.get("/items/{item_id}")
# async def read_user_item(item_id: str, needy: str | None = None):  # Make needy optional
    # item = {"item_id": item_id, "needy": needy}
    # return item
 
    
@app.get("/call_gsa_api")
async def call_gsa_api(zip_code:str, year:str):
    async with httpx.AsyncClient() as client:
        
        headers = {
            #"Authorization": "Bearer my_token",  # Example authorization header
            #"Content-Type": "application/json",  # Example content type header
            # Add more headers as needed
            "x-api-key": X_API_KEY
        }        
        
        ZIP=zip_code
        print("zip:", ZIP)
        YEAR=year
        print("year:", YEAR)
        url= BASE_URL+'/rates/zip/'+ZIP+'/year/'+YEAR
        print("url:", url)
        response = await client.get(url,headers=headers)
        # Process the response as needed
        if response.status_code == 200:
            json_data = response.json()  # Parse the JSON response
            # Assuming you have the JSON data in the 'json_data' variable (from the previous response)
            extracted_data = parse_and_display_rates(json_data)
            # print("\nExtracted JSON Data:")
            # print(json.dumps(result, indent=4))  # Pretty-print the extracted JSON
            return extracted_data
        else:
            return {"error": "Failed to fetch data"}
            
            
@app.get("/call_gsa_api/calculate_perdiem")
async def call_gsa_api(zip_code:str, begin_date:str, end_date:str):
    async with httpx.AsyncClient() as client:
        
        headers = {
            #"Authorization": "Bearer my_token",  # Example authorization header
            #"Content-Type": "application/json",  # Example content type header
            # Add more headers as needed
            "x-api-key": X_API_KEY
        }        
        
        ZIP = zip_code
        print("zip:", ZIP)
       
        # Extract date components
        begin_YYYY, begin_MM, begin_day = begin_date.split("-")
        print("begin_YYYY:", begin_YYYY, "begin_MM:", begin_MM, "begin_DD:", begin_day)
        
        end_YYYY, end_MM, end_day = end_date.split("-")
        print("end_YYYY:", end_YYYY, "end_MM:", end_MM, "end_DD:", end_day)

        # Calculate number of days
        begin_num_of_days = (datetime(year=int(begin_YYYY), month=12, day=31) - 
                             datetime(year=int(begin_YYYY), month=int(begin_MM), day=int(begin_day))).days + 1
        print("begin_num_of_days:", begin_num_of_days)
        end_num_of_days = (datetime(year=int(end_YYYY), month=int(end_MM), day=int(end_day)) - 
                           datetime(year=int(end_YYYY), month=1, day=1)).days + 1
        print("end_num_of_days:", end_num_of_days)

        # Make API calls for both years if necessary
        if begin_YYYY == end_YYYY:
            url = BASE_URL + '/rates/zip/' + ZIP + '/year/' + begin_YYYY
            responses = [await client.get(url, headers=headers)]
        else:
            url_begin_year = BASE_URL + '/rates/zip/' + ZIP + '/year/' + begin_YYYY
            url_end_year = BASE_URL + '/rates/zip/' + ZIP + '/year/' + end_YYYY
            responses = await asyncio.gather(
                client.get(url_begin_year, headers=headers),
                client.get(url_end_year, headers=headers)
            )
            
        # Process responses and combine data
        extracted_data = {}
        for response in responses:
            if response.status_code == 200:
                json_data = response.json()
                year_data = parse_and_display_rates(json_data)
                extracted_data.update(year_data) 
            else:
                return {"error": "Failed to fetch data for one or both years"}
        
        begin_month_num  = int(begin_MM)  # Convert begin_MM to an integer
        print("begin_month_num:", begin_month_num)
        end_month_num = int(end_MM)
        print("end_month_num:", end_month_num)
        
        # Calculate and add rate breakdowns (using daily_hotel_rates_by_month)
        extracted_data['begin_YYYY'] = begin_YYYY
        extracted_data['begin_MM'] = begin_MM
        extracted_data['begin_num_of_days']= begin_num_of_days
        
        extracted_data['begin_daily_hotel_rate'] = extracted_data['daily_hotel_rates_by_month'][begin_month_num - 1]['value']
        extracted_data['begin_total_hotel'] = begin_num_of_days * extracted_data['begin_daily_hotel_rate']
        extracted_data['begin_daily_meals_rate'] = extracted_data['meals_rate'] 
        extracted_data['begin_total_meals'] = begin_num_of_days * extracted_data['begin_daily_meals_rate']
        
        extracted_data['end_YYYY'] = end_YYYY
        extracted_data['end_MM'] = end_MM
        extracted_data['end_num_of_days']= end_num_of_days
        
        extracted_data['end_daily_hotel_rate'] = extracted_data['daily_hotel_rates_by_month'][end_month_num - 1]['value']
        extracted_data['end_total_hotel'] = end_num_of_days * extracted_data['end_daily_hotel_rate']
        extracted_data['end_daily_meals_rate'] = extracted_data['meals_rate']
        extracted_data['end_total_meals'] = end_num_of_days * extracted_data['end_daily_meals_rate']
        
        extracted_data['total_hotel'] = extracted_data['begin_total_hotel'] + extracted_data['end_total_hotel']
        extracted_data['total_meals'] = extracted_data['end_total_meals'] + extracted_data['end_total_meals']
        extracted_data['total_perdiem'] =  extracted_data['total_hotel'] + extracted_data['total_meals']
        
        return extracted_data