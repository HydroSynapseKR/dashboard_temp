import json
import geopandas as gpd
import pandas as pd
from pathlib import Path

class LayerManager:
    """Manages loading and managing GIS layers from config"""
    
    def __init__(self, config_path='config/layers.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def get_map_config(self):
        """Get map configuration (center, zoom)"""
        return self.config.get('map', {})
    
    def get_layers(self):
        """Get all layer definitions"""
        return self.config.get('layers', [])
    
    def load_layer_data(self, layer_id):
        """Load actual GIS data for a layer"""
        layers = self.get_layers()
        layer = next((l for l in layers if l['id'] == layer_id), None)
        
        if not layer:
            return None
        
        source = layer['source']
        
        # Load GeoJSON
        if layer['type'] == 'geojson':
            gdf = gpd.read_file(source)
            return gdf
        
        # Load shapefile (future)
        elif layer['type'] == 'shapefile':
            gdf = gpd.read_file(source)
            return gdf
        
        return None
    
    def get_visible_layers(self):
        """Get only visible layers"""
        return [l for l in self.get_layers() if l.get('visible', True)]
    
    def get_downloadable_layers(self):
        """Get only downloadable layers"""
        return [l for l in self.get_layers() if l.get('downloadable', True)]
