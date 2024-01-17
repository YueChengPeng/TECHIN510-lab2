import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta

current_date = datetime.now() # get current date
formatted_date_csv = current_date.strftime("%-m_%-d_%Y")

links = []
url = "https://visitseattle.org/events/page/" # + page number, from 1 to 41

# loop pages
for i in range(1, 42):
    res = requests.get(url + str(i) + "/")
    soup = BeautifulSoup(res.text, "html.parser")
    selector = "div.search-result-preview > div > h3 > a"
    link = soup.select(selector)
    links.extend([x['href'] for x in link])

details = [["Name", "Date", "Location", "Type", "Region"]]

# scrape detailed pages
for link in links:
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.text, "html.parser")

        data_item = [] # store data for one detailed page
        # extract names
        name_selector = "div.medium-6.columns.event-top > h1"
        name = soup.select(name_selector)
        data_item.append(name[0].contents[0].strip())
        # extract dates
        date_selector = "div.medium-6.columns.event-top > h4 > span:nth-child(1)"
        date = soup.select(date_selector)
        data_item.append(date[0].contents[0].strip())
        # extract locations
        location_selector = "div.medium-6.columns.event-top > h4 > span:nth-child(2)"
        location = soup.select(location_selector)
        data_item.append(location[0].contents[0].strip())
        # extract types
        type_selector = "div.medium-6.columns.event-top > a:nth-child(3)"
        type = soup.select(type_selector)
        data_item.append(type[0].contents[0].strip())
        # extract regions
        region_selector = "div.medium-6.columns.event-top > a:nth-child(4)"
        region = soup.select(region_selector)
        data_item.append(region[0].contents[0].strip())

        details.append(data_item) # append data for one detailed page to the list
        # time.sleep(1)  # sleep 1 second to avoid being blocked by the server
    except Exception as ex:
        print('Exception:')
        print(ex)

with open('events'+formatted_date_csv+'.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(details)

coordinate_data =[] # stores latitude and longitude
location_cannotfind = [] # stores locations that cannot be found

# scrape coordinates
for i in range(1, len(details)):
    cord_base_url = "https://nominatim.openstreetmap.org/search.php"
    try: # first try to find the location with the location name
        # search parameters
        query_params = {
            "q": details[i][2] + ", Seattle",
            "format": "jsonv2"
        }
        # specify headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Referer': 'https://nominatim.openstreetmap.org/ui/search.html'
        }
        res_cord = requests.get(cord_base_url, params=query_params, headers=headers)
        res_dict = res_cord.json()
        coordinate_data.append([res_dict[0]['lat'], res_dict[0]['lon']])
    except:
        try: # then try to find location with region name
            # search parameters
            query_params = {
                "q": details[i][4] + ", Seattle",
                "format": "jsonv2"
            }
            # specify headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Referer': 'https://nominatim.openstreetmap.org/ui/search.html'
            }
            res_cord = requests.get(cord_base_url, params=query_params, headers=headers)
            res_dict = res_cord.json()
            coordinate_data.append([res_dict[0]['lat'], res_dict[0]['lon']])
        except: # if still cannot find the location, redirect the location name
            try: 
                print(details[i][4])
                # redirect region names from experience
                region_redirect = {
                    "Queen Anne / Seattle Center": "Seattle Center",
                    "Bellevue / Eastside": "Bellevue Way NE",
                    "Fremont / Ballard": {"Ballard Farmers Market": " 5345 Ballard Ave NW", "Fremont Farmers Market": "3401 Evanston Ave N"}
                }
                if details[i][4] in region_redirect.keys(): # if the region name is in the redirect list
                    if details[i][4] == "Fremont / Ballard": # if the region name is a dict
                        if details[i][2] in region_redirect[details[i][4]].keys(): # if the location name is in the redirect list
                            query_params = {
                                "q": region_redirect[details[i][4]][details[i][2]] + ", Seattle",
                                "format": "jsonv2"
                            }
                    else:
                        query_params = {
                            "q": region_redirect[details[i][4]] + ", Seattle",
                            "format": "jsonv2"
                        }
                    print(query_params)
                # specify headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                    'Referer': 'https://nominatim.openstreetmap.org/ui/search.html'
                }
                res_cord = requests.get(cord_base_url, params=query_params, headers=headers)
                res_dict = res_cord.json()
                coordinate_data.append([res_dict[0]['lat'], res_dict[0]['lon']])
            except:
                # coordinate_data.append([])
                location_cannotfind.append([details[i][2], details[i][4]])

# save the coordinate data to a csv file
with open('locations'+formatted_date_csv+'.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(coordinate_data)

# forecastable_date = ["1/17/2024", "1/18/2024", "1/19/2024", "1/20/2024", "1/21/2024", "1/22/2024", "1/23/2024"] # the max date can be forecasted is '1/23/2024'
forecastable_raw_date = [current_date + timedelta(days=i) for i in range(7)] # get the next 7 days
forecastable_date = [date.strftime("%-m/%-d/%Y") for date in forecastable_raw_date] # convert the date format e.g. '01/17/2024' to '1/17/2024'
weather_base_url = "https://api.weather.gov/points/"
weather_data = [["Name", "Date", "Location", "Type", "Region", "Weather"]]

for i in range(0, len(details)):
    if details[i][1] in forecastable_date: # filter out the events within 7 days
        try:
            res_weather = requests.get(weather_base_url + str(coordinate_data[i][0]) + "," + str(coordinate_data[i][1]))
            res_dict = res_weather.json()

            res_weather_detail = requests.get(res_dict['properties']['forecast']) # use the forecast property to get the weather data
            res_dict = res_weather_detail.json()

            # convert the date format e.g. '1/17/2024' to '2024-01-17'
            parts = details[i][1].split('/') 
            formatted_date = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            
            for period in res_dict["properties"]["periods"]:
                # we are interested in the weather data of the day time of that day
                if period["startTime"].startswith(formatted_date) and period["endTime"].startswith(formatted_date):
                    weather_data.append(details[i] + [period["detailedForecast"]]) # there are many attributes in the weather data, we are only interested in the detailedForecast
                    break
        except Exception as ex:
            print('Exception:')
            print(ex)

# save the coordinate data to a csv file
with open('weather'+formatted_date_csv+'.csv', 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(weather_data)