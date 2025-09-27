import requests
import pandas as pd
import geopandas as gpd
import io

# Replace with your Census API key
API_KEY = "6a48aa97c7519117ef5ac343ba3fe50d60106932"

# --- 1) API Endpoint for ACS 5-Year Data Profile (2022), Table DP05 ---
# Variables to pull: NAME (geography name) and DP05_0073E (Hispanic or Latino (of any race), and DP05_0001E (Total Population))
acs_url = "https://api.census.gov/data/2022/acs/acs5/profile"
params = {
    "get": "NAME,DP05_0073E,DP05_0001E",
    "for": "tract:*",
    "in": "state:12 county:086",   # Miami-Dade County  
    "key": API_KEY
}
r = requests.get(acs_url, params=params)
r.raise_for_status()
data = r.json()
df = pd.DataFrame(data[1:], columns=data[0])
df["DP05_0073E"] = pd.to_numeric(df["DP05_0073E"], errors="coerce")
df["DP05_0001E"] = pd.to_numeric(df["DP05_0001E"], errors="coerce")
df["GEOID"] = df["state"] + df["county"] + df["tract"]

# --- Geometry: TIGERweb Census Tracts layer (GeoJSON) ---
# Layer 10 = Census Tracts; query Miami-Dade only
tiger_url = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/10/query"
    "?where=STATE%3D%2712%27+AND+COUNTY%3D%27086%27"
    "&outFields=STATE,COUNTY,TRACT,GEOID,NAME"
    "&returnGeometry=true&outSR=4326&f=geojson"
)

geo_resp = requests.get(tiger_url)
geo_resp.raise_for_status()
gdf = gpd.read_file(io.BytesIO(geo_resp.content))

# --- Join + calc ---
gdf = gdf.merge(df[["GEOID", "DP05_0073E", "DP05_0001E"]], on="GEOID", how="left")
gdf["hispanic_pct"] = (gdf["DP05_0073E"] / gdf["DP05_0001E"]) * 100

# Save as GeoParquet for future super-fast reads
gdf.to_parquet("miamidade_tracts_hispanic.parquet", index=False)
print(gdf[["GEOID","NAME","hispanic_pct"]].head())
