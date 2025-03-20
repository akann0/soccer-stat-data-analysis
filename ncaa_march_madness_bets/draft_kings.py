# %%
from curl_cffi import CurlHttpVersion
from curl_cffi import requests
import json, csv
import httpx
from bs4 import BeautifulSoup
import csv
from playwright.sync_api import sync_playwright

draftkings_nfl_api_url = "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/88808?format=json"
draftkings_nfl_site_url = "https://sportsbook/https:.draftkings.com/leagues/football/nfl"
draftkings_cbb_api_url = "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/92483?format=json"
draftkings_nba_api_url = "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/42648?format=json"
draftkings_mlb_api_url = "https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/84240?format=json"

# HTTP_VERSION_1_1 = CurlHttpVersion.HTTP_VERSION_1_1

# %%
# Code to help find the api - do not run
def find_access_code_in_server():
    response = requests.get(draftkings_nfl_site_url, headers={"User-Agent": "Mozilla/5.0"})
    if ("88808" in response.text):
        print("Found the event group id on the site")
        index_found = response.text.find("88808")
        print(response.text[index_found-500:index_found+500])
    else:
        print("Did not find the event group id on the site")
        print(response.text)

# %%
# Generalized function to get data from DraftKings API
def get_dk_data(sport):
    api_urls = {
        "cbb": draftkings_cbb_api_url,
        "nba": draftkings_nba_api_url,
        "mlb": draftkings_mlb_api_url,
    }

    if sport not in api_urls:
        print(f"Sport {sport} not supported")
        return

    def get_json(url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Start headless browser
            page = browser.new_page()

            # Navigate directly to the API endpoint
            page.goto(url)

            # Get the content of the page as JSON (it might be an API response directly)
            response = page.content()  # Get page content as string (may not work for pure APIs)

            # In case it's a JSON response, parse it
            ans = None
            try:
                ans = page.evaluate("() => JSON.parse(document.body.innerText)")
                 # Print the JSON data
            except Exception as e:
                print("Error parsing JSON:", e)

            browser.close()
            return ans
        

            
    

    def get_json_in_chunks(url):
        response = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"}, http_version=CurlHttpVersion.V1_1)
        for chunk in response.iter_content(chunk_size=1024):
            print(chunk)

    
    json = get_json(api_urls[sport])

    category_urls = {}
    cat_names = {}
    for event in json['eventGroup']['offerCategories']:
        category_urls[event['offerCategoryId']] = f"https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/{json['eventGroup']['eventGroupId']}/categories/{event['offerCategoryId']}?format=json"
        cat_names[event['offerCategoryId']] = event['name']

    csv_data = []

    # NEW PLAN: Get a list of all subcategories, then get the data for each subcategory
    subcategories = list()
    offers = list()
    for cat_id in category_urls:
        print(f"Getting data at website {category_urls[cat_id]}", cat_names[cat_id])
        jason = get_json(category_urls[cat_id])
        for category in jason['eventGroup']['offerCategories']:
            if 'offerSubcategoryDescriptors' in category.keys(): 
                if category['offerSubcategoryDescriptors'] is not None: #i'm not entirely sure if these two checks are necessary, but alas
                    for subcat in category['offerSubcategoryDescriptors']:
                        if "offerSubcategory" not in subcat.keys():
                            subcategories.append({
                                "subcatId": subcat['subcategoryId'],
                                "catId": cat_id
                            })
                        else:
                            for offer in subcat['offerSubcategory']['offers']:
                                offers.append({
                                    "offer": offer,
                                    "category": category['name'],
                                    "subcat": subcat['name']
                                })



    for subcat in subcategories:
        print(f"Getting data for ", subcat)
        jason = get_json(f"https://sportsbook.draftkings.com//sites/US-SB/api/v5/eventgroups/{json['eventGroup']['eventGroupId']}/categories/{subcat['catId']}/subcategories/{subcat['subcatId']}?format=json")
        for category in jason['eventGroup']['offerCategories']:
            if 'offerSubcategoryDescriptors' in category.keys(): 
                if category['offerSubcategoryDescriptors'] is not None: #i'm not entirely sure if these two checks are necessary, but alas
                    for subcat in category['offerSubcategoryDescriptors']:
                        if "offerSubcategory" not in subcat.keys():
                            continue
                        for offer in subcat['offerSubcategory']['offers']:
                            offers.append({
                                "offer": offer,
                                "category": category['name'],
                                "subcat": subcat['name']
                                })
                
                
                
    for offer in offers:
        for i in offer["offer"]:
            for outcome in i['outcomes']:
                dict = outcome
                dict['category'] = offer['category']
                dict['subcategory'] = offer['subcat']
                if 'label' in i.keys():
                    dict['prop_label'] = i['label']

                
                csv_data.append(fill_unlabeled_keys(dict, csv_data)) #some key values are not addressed by DK

    # turn the data in csv_data into a csv file
    with open(f'draftkings_{sport}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        headers = csv_data[0].keys()
        writer.writerow(headers)
        for row in csv_data:
            writer.writerow([row.get(key, "None Specified") for key in headers])

def fill_unlabeled_keys(dic, csv_data):
    if (len(csv_data) == 0):
        return dic

    if (dic.keys() == csv_data[0].keys()):
        return dic
    
    for key in csv_data[0].keys():
        if key not in dic.keys():
            # print(f"Adding key {key} to dict")
            dic[key] = "None Specified"

    return dic



# %%
get_dk_data("cbb")