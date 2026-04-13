import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import json
from utils.layer_manager import LayerManager

# Page configuration
st.set_page_config(
    page_title="GIS Dashboard",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ White Oak Bayou Feasibility Study Dashboard")

# Load configuration
layer_manager = LayerManager('config/layers.json')
map_config = layer_manager.get_map_config()

# Create columns for layout
col1, col2 = st.columns([3, 1])

# ============================================================
# MAIN MAP (Left Column)
# ============================================================
with col1:
    # Initialize map
    m = folium.Map(
        location=[map_config['center_lat'], map_config['center_lon']],
        zoom_start=map_config['zoom'],
        tiles="OpenStreetMap"
    )
    
    # Store layer data in session state for downloads
    if 'layer_data' not in st.session_state:
        st.session_state.layer_data = {}
    
    # Add layers to map
    visible_layers = layer_manager.get_visible_layers()
    for layer in visible_layers:
        try:
            gdf = layer_manager.load_layer_data(layer['id'])
            
            if gdf is not None:
                if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                    gdf = gdf.to_crs(epsg=4326)
                # Store for later download
                st.session_state.layer_data[layer['id']] = gdf                
                
                style = layer.get('style', {})
                
                # Create feature group
                fg = folium.FeatureGroup(name=layer['name'])
                
                # Add geometries based on type
                for idx, row in gdf.iterrows():
                    geom = row.geometry
                    
                    if geom.geom_type == 'Polygon':
                        folium.Polygon(
                            locations=[(lat, lon) for lon, lat in geom.exterior.coords],
                            color=style.get('color', 'blue'),
                            weight=style.get('weight', 2),
                            opacity=style.get('opacity', 0.7),
                            fillColor=style.get('fillColor', 'lightblue'),
                            fillOpacity=style.get('fillOpacity', 0.5),
                            popup=f"{layer['name']} - {row.get('name', idx)}"
                        ).add_to(fg)
                    
                    elif geom.geom_type == 'LineString':
                        coords = [(lat, lon) for lon, lat in geom.coords]
                        folium.PolyLine(
                            locations=coords,
                            color=style.get('color', 'blue'),
                            weight=style.get('weight', 2),
                            opacity=style.get('opacity', 0.7),
                            popup=f"{layer['name']} - {row.get('name', idx)}"
                        ).add_to(fg)
                    
                    elif geom.geom_type == 'Point':
                        folium.CircleMarker(
                            location=(geom.y, geom.x),
                            radius=5,
                            color=style.get('color', 'blue'),
                            weight=style.get('weight', 2),
                            opacity=style.get('opacity', 0.7),
                            popup=f"{layer['name']} - {row.get('name', idx)}"
                        ).add_to(fg)
                
                fg.add_to(m)
        
        except Exception as e:
            st.error(f"Error loading layer {layer['name']}: {str(e)}")
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Display map
    st_folium(m, width=1400, height=600)

# ============================================================
# CONTROLS (Right Column)
# ============================================================
with col2:
    st.subheader("📋 Layer Controls")
    
    # Layer visibility toggles
    st.write("**Visible Layers:**")
    visible_layers = layer_manager.get_visible_layers()
    for layer in visible_layers:
        st.checkbox(layer['name'], value=True, disabled=True, key=f"check_{layer['id']}")
    
    st.divider()
    
    # Download section
    st.write("**📥 Download Layers:**")
    
    downloadable_layers = layer_manager.get_downloadable_layers()
    
    for layer in downloadable_layers:
        st.write(f"**{layer['name']}**")
        
        col_format1, col_format2 = st.columns(2)
        
        with col_format1:
            if st.button(f"📄 GeoJSON", key=f"geojson_{layer['id']}", use_container_width=True):
                if layer['id'] in st.session_state.layer_data:
                    gdf = st.session_state.layer_data[layer['id']]
                    geojson_str = gdf.to_json()
                    st.download_button(
                        label=f"Download {layer['name']} (GeoJSON)",
                        data=geojson_str,
                        file_name=f"{layer['id']}.geojson",
                        mime="application/json"
                    )
        
        with col_format2:
            if st.button(f"📊 CSV", key=f"csv_{layer['id']}", use_container_width=True):
                if layer['id'] in st.session_state.layer_data:
                    gdf = st.session_state.layer_data[layer['id']]
                    csv_data = gdf.drop(columns=['geometry']).to_csv(index=False)
                    st.download_button(
                        label=f"Download {layer['name']} (CSV)",
                        data=csv_data,
                        file_name=f"{layer['id']}.csv",
                        mime="text/csv"
                    )
        
        st.divider()

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.markdown("""
    **About:** This is an interactive GIS dashboard built with Streamlit.
    - 🗺️ Pan and zoom the map
    - 👆 Click features for information
    - 📥 Download layers in multiple formats
    - ⚙️ Configure layers in `config/layers.json`
""")
