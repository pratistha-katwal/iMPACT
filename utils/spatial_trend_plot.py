import geopandas as gpd
import plotly.graph_objects as go
import numpy as np

# Load the shapefile outside the function (only once)
shapefile_path = 'Shapefile/Nepal_bnd_WGS84.shp'
nepal_shape = gpd.read_file(shapefile_path)

def spatial_trend_plot(dataset,a):
    fig_spatial_trend = go.Figure()

    fig_spatial_trend.add_trace(go.Heatmap(
        x=dataset.lon.values,
        y=dataset.lat.values,
        z=dataset.values,
        colorscale='RdBu',
        colorbar=dict(title=f'Slope (mm/{a})'),
        hovertemplate="Lat: %{y:.2f}<br>Lon: %{x:.2f}<br>Trend: %{z:.2f} mm/" + str(a),
        name='Mann-Kendall Trend Slope (mm/yr)'
    ))

    # Get min and max of coordinates
    x = dataset.lon.values
    y = dataset.lat.values
    
    x_tickvals = np.linspace(min(x), max(x), 5)
    y_tickvals = np.linspace(min(y), max(y), 5)

    x_ticktext = [f"{abs(val):.1f}°{'E' if val >= 0 else 'W'}" for val in x_tickvals]
    y_ticktext = [f"{abs(val):.1f}°{'N' if val >= 0 else 'S'}" for val in y_tickvals]

    # Add Nepal shapefile outline
    try:
        # Convert to GeoJSON
        nepal_geojson = nepal_shape.__geo_interface__
        
        for feature in nepal_geojson['features']:
            coords = feature['geometry']['coordinates']
            
            if feature['geometry']['type'] == 'MultiPolygon':
                for polygon in coords:
                    for ring in polygon:
                        lon, lat = zip(*ring)
                        fig_spatial_trend.add_trace(go.Scatter(
                            x=lon,
                            y=lat,
                            mode='lines',
                            line=dict(color='black', width=2),
                            hoverinfo='skip',
                            showlegend=False
                        ))
            else:  # Polygon
                for ring in coords:
                    lon, lat = zip(*ring)
                    fig_spatial_trend.add_trace(go.Scatter(
                        x=lon,
                        y=lat,
                        mode='lines',
                        line=dict(color='black', width=2),
                        hoverinfo='skip',
                        showlegend=False
                    ))
    except Exception as e:
        print(f"Could not add shapefile: {e}")


    fig_spatial_trend.update_layout(
        title=dict(text='Spatial Distribution of Statistically Significant Precipitation Trends (p <= 0.05) <br>  Derived from Mann-Kendall Test',
                   xanchor='center',
                   x=0.5,
                   font=dict(size=18, family="Arial Black", color='MidnightBlue')),
        xaxis=dict(
            title='Longitude',
            tickvals=x_tickvals,
            ticktext=x_ticktext,
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor='lightgrey'
        ),
        yaxis=dict(
            title='Latitude',
            tickvals=y_tickvals,
            ticktext=y_ticktext,
            tickfont=dict(size=12),
            showgrid=True,
            gridcolor='lightgrey'
        ),
        plot_bgcolor='rgba(240,248,255, 0.4)',
        width=1250,
        height=700
    )

    return fig_spatial_trend