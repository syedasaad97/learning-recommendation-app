from fastapi import FastAPI, status
import openai
import re
import os
from dotenv import load_dotenv
import json
from googleapiclient.discovery import build
from duckduckgo_search import DDGS
import requests

load_dotenv()

app = FastAPI()
# Retrieve the API key
OPENAI_API_KEY = os.getenv("OPENI_API_KEY")

# Check if the API key is loaded
if not OPENAI_API_KEY:
    raise ValueError("⚠️ OpenAI API key not found! Make sure you have a .env file.")

# Set API key for OpenAI
openai.api_key = OPENAI_API_KEY
g_api_key = os.getenv('GOOGLE_API_KEY')
g_cse_id = os.getenv('CSE_ID')


@app.get("/")
async def root():
    return {"message": "Hello World"}


# @app.get("/suggest/gpt", status_code=status.HTTP_200_OK)
# async def root(query:str = '',level:str=''):
#     articles = []
#     response=openai.chat.completions.create(
#                 model= 'gpt-4o-mini',
#                 messages= [
#                     {'role': 'system', 'content': """act as an AI assistant and Recommend me best articles and videos tutorial on basis of some user queries.
#                         Provide the response in JSON format like below:[{"rank": 1,
#                         "title": "Article Title",
#                         "source": "Source Name",
#                         "type": "Article or Tutorial",
#                         "link": "URL" }]"""},
#                     {'role': 'user', 'content': f'Want to {query} and I have {level} level of Financial knowledge and I can dedicate 5 hours per day'}],
#                     n=1
#     )
#     json_string = response.choices[0].message.content
#     # Define the regular expression pattern to match code block markers
#     pattern = r'```[a-zA-Z]*\n([\s\S]*?)\n```'

#     # # Use re.sub() to replace the pattern with the captured group (the content inside the code block)
#     cleaned_text = re.sub(pattern, r'\1', json_string)
#     print(cleaned_text)
#     try:
#      articles = json.loads(cleaned_text)
#     # # 'articles' is now a list of dictionaries
#     except json.JSONDecodeError as e:
#      print(f"Failed to decode JSON: {e}")


#     # print(response.choices[0].message.content)


#     return articles


# @app.get("/suggest/ddgs", status_code=status.HTTP_200_OK)
# async def root(purpose:str = '',level:str=''):
#     articles = []

#     prompt = f"Recommend me best articles and videos tutorial on {purpose} for {level} level"
#     articles = search_articles_ddgs(prompt)

#     for article in articles:
#         print(article)

#     gpt_prompt = f""" Act as an AI assistant.
#     Here are some search results for the query:  {purpose} and output results are
#     {articles}
#     You just want to rank these results by relevancy of user query and valid link.



#     Please:
#     1. **Rank them** by relevance.
#     2. Filter out invalid link

#     Ensure the response is strictly in JSON format without any additional text and also add type like(article/blog/video
#     """
#     print(gpt_prompt)
#     response = chatgpt_completion(gpt_prompt)
#     print(response)
#     json_string = response.choices[0].message.content
#     return json_string


# @app.get("/suggest/ddgs", status_code=status.HTTP_200_OK)
# async def root(purpose:str = '',level:str=''):
#     try:
#         # Generate search query
#         search_query = f"Recommend me best articles and video tutorials on {purpose} for {level} level"
#         articles = search_articles_ddgs(search_query)
#         # print(articles)
#         if not articles:
#             return {"error": "No articles found"}
        
#         # GPT prompt for ranking and filtering
#         gpt_prompt = f'''
#         Act as an AI assistant.
#         Here are some search results for the query: "{purpose}" and the output results are:
#         {json.dumps(articles)}
#         Your task is to:
#         1. **Rank them** by relevance.
#         2. **Filter out invalid links**.
#         3. Also categorize the response type by articles or blogs or videos
        
#         Ensure the response is **strictly in JSON format** and follows this structure:

#         ```
#         [
#             {{"title": "", "link": "", "type": "article/blogs/video"}}
#         ]
#         '''
#         print(gpt_prompt)
#         response = chatgpt_completion(gpt_prompt)
        
#         # Parse the JSON response
#         json_string = response.choices[0].message.content
#         json_string = json_string.strip("```json").strip("```").strip("\n")

#         json_response = json.loads(json_string)
        
#         return json_response
    
#     except Exception as e:
#         print(str(e))
#         return {"error": str(e)}

@app.get("/suggest/google", status_code=status.HTTP_200_OK)
async def googleSearch(purpose:str = '',level:str=''):
    articles = []
    # api_key = 'AIzaSyCaO1CXfAKRW5zneMPPIle9X3cb8lNED3g'
    # cse_id = '850d1bd60d83d4823'
    google_response = []
    prompt = f"Best articles on {purpose} for {level} level -reddit -quora"
    articles = google_search(prompt,g_api_key,g_cse_id)

    google_response.append(articles)

    prompt_video = f"Videos or Courses on {purpose} for {level} level site:youtube.com OR site:coursera.org OR site:udemy.com OR site:edx.org"
    videos_response = google_search(prompt_video,g_api_key,g_cse_id)
    if videos_response:
        google_response.extend(videos_response)
    
    # print(google_response)
    if not google_response:
        return {"error": "No resources found"}
    
    
    gpt_prompt = f'''
        Act as an AI assistant.
        Here are some search results for the query: "{purpose}" and the output results are:
        {json.dumps(google_response)}
        Your task is to:
        1. **Rank them** by relevance.
        2. Filter out irrelevant results
        3. Also categorize the response type by articles or blogs or videos
        
        Ensure the response is **strictly in JSON format** and follows this structure:

        ```
        [
            {{"title": "", "link": "", "type": "articles/video/course", "author": ""}}
        ]
        '''
    response = chatgpt_completion(gpt_prompt)
    json_string = response.choices[0].message.content
    json_string = json_string.strip("```json").strip("```").strip("\n")

    json_response = json.loads(json_string)
    # json_string = response.choices[0].message.content
    return json_response



def google_search(query, api_key, cse_id, **kwargs):
    service = build(
        "customsearch", "v1", developerKey=api_key
    )

    res = (
        service.cse()
        .list(
            q=query,
            cx="850d1bd60d83d4823",
        )
        .execute()
    )
    articles = []
    # print(res.get('items', []))
    for item in res.get('items', []):
        if(is_valid_url(item['link'])):
            articles.append(f"{item['title']} - {item['link']}")

    return articles


def chatgpt_completion(prompt):
    try:
        response = openai.chat.completions.create(
            model='gpt-4o',  # Correct model name
            messages=[
                {"role": "system", "content": "You are an AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            n=1
        )
        return response
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")  # Debugging
        return None


def is_valid_url(url):
    try:
        response = requests.head(url, timeout=3)
        return response.status_code in [200, 301, 302] 
    except requests.RequestException:
        return False
    
def search_articles_ddgs(query, max_results=5):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=max_results)

    articles = []
    for item in results:
        articles.append(f"{item['title']} - {item['href']}")

    return articles