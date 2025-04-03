''' With this script we can download sentinel images from the Copernicus API. '''

from datetime import date
import requests
import pandas as pd
import os
import zipfile
from typing import Union

class SentinelScraper:

    def __init__(self, username:str, password:str, data_collection:str) -> None:
        self.username = username
        self.password = password
        self.data_collection = data_collection
        self.set_accesstoken() # access token is always necessary so run on init

    def set_aoi_rectangle(self, lon_min:float, lat_min:float, lon_max:float, lat_max:float) -> None:
        ''' Set the area of interest to a rectangle defined by the minimum and maximum longitude and latitude '''
        self.aoi = f"POLYGON(({lon_min} {lat_min},{lon_max} {lat_min},{lon_max} {lat_max},{lon_min} {lat_max},{lon_min} {lat_min}))"
  
    def set_dates(self, start_date:Union[str,date], end_date:Union[str,date]) -> None:
        ''' Set the start and end date of the data to be downloaded. Dates should be in the format "YYYY-MM-DD" '''
        self.start_date = start_date
        self.end_date = end_date

    def set_accesstoken(self):
        ''' Set access token (to attribute), used to download data in the copernicus system - required to run download_image method '''
        data = {
            "client_id": "cdse-public",
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }
        try:
            r = requests.post(
                "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
                data=data
            )
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Keycloack token creation failed. Response from the server was: {r.json()}")
        self.access_token = r.json()["access_token"]

    def data_ids(self, name_contains:str) -> pd.Series:
        ''' Get the IDs of data (that contains the phrase `name_contains`) within the area and time of interest. 
        Returns a DF Series with the IDs that are used for the data download URL '''

        if not hasattr(self, "aoi") or not hasattr(self, "start_date") or not hasattr(self, "end_date"):
            raise ValueError("Please set the area of interest and the start and end date using the set_aoi_square and set_dates methods")

        json_ = requests.get(
            f"""https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq '{self.data_collection}' and 
                OData.CSC.Intersects(area=geography'SRID=4326;{self.aoi}') and
                contains(Name,'{name_contains}') and
                ContentDate/Start gt {self.start_date}T00:00:00.000Z and 
                ContentDate/Start lt {self.end_date}T00:00:00.000Z&$count=True&$top=100""" 
        ).json()
        query_returns = pd.DataFrame.from_dict(json_["value"])

        if len(query_returns) == 0:
            raise ValueError("No data found for the given parameters")
     
        im_ids = query_returns["Id"]
        return im_ids

    def download_image(self, id_im:str, data_dir:str, name_contains:str) -> None:
        ''' Downloads the image with the given id and saves it in the data_dir folder '''
        url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({id_im})/$value"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers, stream=True)

        if response.headers['Content-Type'] == 'application/zip': # these contain the data, the application/json ones are just metadata
            content_disposition = response.headers['content-disposition']
            if content_disposition.__contains__(name_contains):
                filename = content_disposition.split("=")[1] # because the strings are like "attachment; filename=..."
                with open(data_dir+ filename, "wb") as file:
                    print(f"Downloading {filename}...")
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)

    def unzip(self, data_dir):
        ''' Unzips all zip files in the data_dir folder '''
        for filename in os.listdir(data_dir):
            if filename.endswith(".zip"):
                path_to_zip_file = data_dir + filename
                directory_to_extract_to = data_dir
                with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
                    zip_ref.extractall(directory_to_extract_to)

def main():
    username = "email"
    password = "password"
    data_collection = "SENTINEL-1"
    name_contains = "SLC"
    scraper = SentinelScraper(username, password, data_collection)

    lon_min, lat_min, lon_max, lat_max = 119.76, -1.05, 119.96, -0.65
    start_date = date.fromisoformat('2018-09-10')
    end_date = date.fromisoformat('2018-09-22')
    scraper.set_aoi_rectangle(lon_min, lat_min, lon_max, lat_max)
    scraper.set_dates(start_date, end_date)
    ids = scraper.data_ids(name_contains)

    # THINGS YOU NEED TO DO TO MAKE THIS WORK FOR YOURSELF
    # 1. Create a Copernicus account and get the username and password
    # 2. Check which data product you want; you can edit the json request in data_ids to query for different data
    # the copernicus website should state how to query, e.g. particular name tags, dates, number of results in query, etc.

    print(f'Found {len(ids)} images')

    # for id in ids:
        # scraper.download_image(id, data_dir = "./data/")

    # BUG:
    # it can return different results for the query on subsequent runs
    # (it's not returning all possible results; should raise the limit of returns?)

if __name__ == "__main__":
    main()
