## Sentinel Data Downloader

Downloads Sentinel data (of any Sentinel mission) based on user-set query parameters, from the Copernicus Data Space Ecosystem (CDSE, migrated to as of June 2023).
E.g., download all Sentinel-2 data over the lat [0.0, 10.0] lon [0.0, 10.0] region, with cloud cover < 0.5.
See the dataspace documentation for help on how to query the CDSE catalogue: https://documentation.dataspace.copernicus.eu/notebook-samples/geo/odata_basics.html

To make this work:
1. Create a Copernicus account and get the username and password; set it in the script.
2. Check which data product you want; you can edit the json request in `data_ids` to query for different data the copernicus website should state how to query, e.g. particular name tags, dates, number of results in query, etc.
