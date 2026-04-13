import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
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

def create_label_html(label_text, label_config):
    """Create styled label HTML"""
    font_size = label_config.get("size", 12)
    font_weight = label_config.get("weight", "normal")
    text_color = label_config.get("color", "black")
    use_outline = label_config.get("useOutline", True)
    
    if use_outline:
        text_shadow = "-1px -1px 1px #fff, 1px -1px 1px #fff, -1px 1px 1px #fff, 1px 1px 1px #fff"
    else:
        text_shadow = "none"
    
    return f'''
        <div style="
            font-size: {font_size}px; 
            font-weight: {font_weight}; 
            color: {text_color};
            text-shadow: {text_shadow};
        ">
            {label_text}
        </div>
    '''

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
                symbolize_field = layer.get('symbolizefield', None)
                if symbolize_field and symbolize_field in gdf.columns:
                    unique_values = gdf[symbolize_field].unique()
                    color_palette = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta']
                    color_map = {val: color_palette[i % len(color_palette)] for i, val in enumerate(unique_values)}
                    style['fillColor'] = gdf[symbolize_field].map(color_map)
                
                # Create feature group
                fg = folium.FeatureGroup(name=layer['name'])
                
                # Add geometries based on type
                for idx, row in gdf.iterrows():
                    geom = row.geometry
                    if symbolize_field and symbolize_field in gdf.columns:
                        fillcolor = style['fillColor'].get(idx, 'blue')
                    else:
                        fillcolor = style.get('fillColor', 'blue')
                    
                    if geom.geom_type == 'Polygon':
                        folium.Polygon(
                            locations=[(lat, lon) for lon, lat in geom.exterior.coords],
                            color=style.get('color', 'blue'),
                            weight=style.get('weight', 2),
                            opacity=style.get('opacity', 0.7),
                            fillColor=fillcolor,
                            fillOpacity=style.get('fillOpacity', 0.5),
                            popup=f"{layer['name']} - {row.get(symbolize_field, idx)}"
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
                    
                    if layer.get('labelfield', None):
                        centroid = geom.centroid
                        folium.Marker(
                            location=(centroid.y, centroid.x),
                            icon=folium.DivIcon(create_label_html(str(row[layer['labelfield']]), layer.get('labelstyle', {})))
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
