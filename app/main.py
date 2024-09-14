#pipenv install fastapi httpx
#pipenv shell
# uvicorn nyt_movies:app --reload
# http://127.0.0.1:8000/call-external-api?begin_date=20240905&end_date=20240913

from fastapi import FastAPI
import httpx
from datetime import datetime

app = FastAPI()

API_KEY='uedPipKsm7yUoLxd1GEha30oBnpUtXza' # your API key
BEGIN_DATE='20240905'
END_DATE='20240911'
FQ='section_name%3AMovies AND type_of_material%3AReview' # keyword
F1='document_type%2Cabstract%2Cweb_url%2Cheadline%2Ckeywords%2Cbyline'
EXTRA_FILTERS='sort=newest&page=0'
BASE_URL='https://api.nytimes.com/svc/search/v2/articlesearch.json'


def extract_article_info(data):
    """
    Extracts relevant information from the API response data, handling multiple articles.

    Args:
        data (dict): The JSON data returned from the API call.

    Returns:
        list: A list of dictionaries, each containing the extracted information for one article.
    """
    current_time = datetime.now().strftime("%H:%M:%S")
    print("extract_article_info Run time is:", current_time)
    
    articles_info = []

    for article in data["response"]["docs"]:
        abstract = article.get("abstract")  # Use .get() to handle missing keys
        web_url = article.get("web_url")
       
        #headlines = article.get("headlines", [])
        grouped_headlines = {
            "headline": article["headline"].get("main"),
            "print_headline": article["headline"].get("print_headline")
        }
        
        keywords = article.get("keywords", [])
        grouped_keywords = {
            "subject": [kw["value"] for kw in keywords if kw["name"] == "subject"],
            #"creative_works":[kw["value"] for kw in keywords if kw["name"] == "creative_works"],
            "creative_work": next((kw["value"] for kw in keywords if kw["name"] == "creative_works"), None),  # Extract first or None
            "persons": [kw["value"] for kw in keywords if kw["name"] == "persons"]
        }
        author_name = article["byline"].get("original", "").replace("By ", "")

        articles_info.append({
            "abstract": abstract,
            "web_url": web_url,
            "headlines": grouped_headlines,
            "keywords": grouped_keywords,
            "author_name": author_name,
        })
    return articles_info

@app.get("/")
async def root():
    current_time = datetime.now().strftime("%H:%M:%S")
    print("Root Run time is:", current_time)
    return {"message": "Welcome to the FAST API"}
    
# @app.get("/items/{item_id}")
# async def read_user_item(item_id: str, needy: str | None = None):  # Make needy optional
    # item = {"item_id": item_id, "needy": needy}
    # return item
 
    
@app.get("/call-external-api")
async def call_external_api(begin_date:str, end_date:str):
    async with httpx.AsyncClient() as client:
        BEGIN_DATE=begin_date
        print("begin_date:", BEGIN_DATE)
        END_DATE=end_date
        print("end_date:", END_DATE)
        url= BASE_URL+'?begin_date='+BEGIN_DATE+'&end_date='+END_DATE+'&f1='+F1+'&fq='+FQ+'&'+EXTRA_FILTERS+'&api-key='+API_KEY
        print("url:", url)
        response = await client.get(url)
        # Process the response as needed
        if response.status_code == 200:
            data = response.json()  # Parse the JSON response
            extracted_info = extract_article_info(data)
            return extracted_info
        else:
            return {"error": "Failed to fetch data"}