import streamlit as st
import pandas as pd
import requests
from PIL import Image

LOCATE_URL = "https://locate.measurementlab.net/v2/siteinfo/registrations?exp=ndt"


logo = Image.open('./content/mlab-logo-black.png')
page_title = "M-Lab Platform Status"
st.set_page_config(layout="wide",
                    page_title = page_title,
                    page_icon = logo)
st.image(logo, width=200)
st.title(page_title)



@st.cache_data(ttl=300)
def get_servers():
	r = requests.get(LOCATE_URL)
	servers_raw = r.json()

	servers_formatted = dict()
	for rs in servers_raw:
		if servers_raw[rs]["Health"] is not None:
			servers_formatted[rs] = {k:v for k,v in servers_raw[rs]["Registration"].items() if k != "Services"}
			servers_formatted[rs]["Prometheus"] = 0 if servers_raw[rs]["Prometheus"] is None else servers_raw[rs]["Prometheus"]["Health"]


	df_cols = ['ContinentCode', 'CountryCode', 'Metro', 'City', 'Latitude', 'Longitude', 'Project', 'Site', 'Type', 'Uplink', 'Probability', 'Prometheus', 'Hostname']
	df = pd.DataFrame.from_dict(servers_formatted, orient="index").reset_index()[df_cols]
	return df




def show_metrics(df):
	cols = st.columns(5)
	cols[0].metric("Total servers", len(df))
	cols[1].metric("Physical servers", len(df[df["Type"]=="physical"]))
	cols[2].metric("Virtual servers", len(df[df["Type"]=="virtual"]))
	cols[3].metric("OTI servers", len(df[df["Project"]=="mlab-oti"]))
	cols[4].metric("Autojoin servers", len(df[df["Project"]=="mlab-autojoin"]))


	cols = st.columns(5)
	cols[0].metric("Number of continents", len(df["ContinentCode"].unique()))
	cols[1].metric("Number of countries", len(df["CountryCode"].unique()))
	cols[2].metric("Number of cities", len(df["City"].unique()))
	cols[3].metric("Number of metros", len(df["Metro"].unique()))

	cols = st.columns(5)
	cols[0].metric("Number of Prometheus", len(df[df["Prometheus"]==True]))


df = get_servers()

filtered_df = df.copy()
filter_cols = ['ContinentCode', 'CountryCode', 'City', 'Project', 'Type', 'Uplink', 'Probability']

h = st.expander(label="Filter servers", expanded=True)
for fc in filter_cols:
	unique_values = sorted(filtered_df[fc].unique())
	selected_values = h.multiselect(label=fc, options=unique_values, default=unique_values)
	filtered_df = filtered_df[filtered_df[fc].isin(selected_values)]

st.dataframe(filtered_df, hide_index=True)

show_metrics(filtered_df)

map_df = filtered_df.copy()
city_sizes = filtered_df["City"].value_counts().to_dict()
map_df["size"] = map_df["City"].map(lambda x: city_sizes.get(x))
st.map(map_df.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'}), size="size", zoom=1)

