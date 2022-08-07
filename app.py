import geopandas as gpd
from shapely.errors import WKTReadingError
import streamlit as st
import streamlit_folium

from stsa.stsa import TopsSplitAnalyzer
from stsa.utils import gdf_from_wkt

st.set_page_config(layout="wide")

st.title('S1-TOPS Split Analyzer (STSA)')

st.markdown("""
Simple web app implementation of STSA. If you have issues or suggestions please raise them in the
 [Github repo](https://github.com/pbrotoisworo/s1-tops-split-analyzer). This project is open-source and licensed under
 the [Apache-2.0 License](https://github.com/pbrotoisworo/s1-tops-split-analyzer/blob/main/LICENSE).

This web app extracts burst and subswath data from Sentinel-1 SLC data and visualizes on a webmap. The data itself can
be downloaded as GeoJSON format for viewing in GIS software. To be able to access the API please use your Copernicus
Scihub account. If you don't have one you can make one [here](https://scihub.copernicus.eu/).

This web app allows you to add one geometry overlay. You can create or format data into WKT strings using 
[geojson.io](https://geojson.io). Create or load your geometry then save it as WKT. Then load the WKT from the text 
file into the text box.
""")

with st.form(key='api'):
    scene = st.text_input(
        label='Sentinel-1 SLC scene ID'
    )
    wkt_aoi = st.text_input(
        label='WKT of geometry overlay (optional)'
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        username = st.text_input(
            label='Scihub Username'
        )
    with col2:
        password = st.text_input(
            label='Scihub Password',
            type='password'
        )
    with col3:
        pass
    load_button = st.form_submit_button(label='Load data')

if load_button:
    
    # Check WKT input before connecting to API
    if wkt_aoi:
        try:
            geom_overlay = gdf_from_wkt(wkt_aoi)
        except WKTReadingError:
            st.error('Error: Failed to parse WKT string for geometry overlay.')
            st.stop()
    else:
        geom_overlay = None

    s1 = TopsSplitAnalyzer(streamlit_mode=True, verbose=False)
    with st.spinner('Connecting to API...'):
        s1.load_api(
            username=username,
            password=password,
            scene_id=scene,
            download_folder=''
        )
    if s1.api_product_is_online is False:
        st.error(f'Error: Scene is offline')
        st.stop()

    download = st.empty()

    if wkt_aoi:
        df_intersect = gpd.GeoDataFrame(
            s1.intersecting_bursts(geom_overlay), columns=['subswath', 'burst']
        )
        if len(df_intersect) > 0:
            st.text('Geometry overlay intersects with the following bursts:')
            st.dataframe(df_intersect)
        else:
            st.text('No overlap found with the geometry overlay.')
    else:
        geom_overlay = None
    streamlit_folium.folium_static(s1.visualize_webmap(geom_overlay), width=1200, height=800)

    filename = f'{scene}.geojson'
    download.download_button('Download GeoJSON', data=s1.df.to_json(), file_name=filename)
