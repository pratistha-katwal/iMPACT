import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pymannkendall as mk
import xarray as xr
import geopandas as gpd
import rioxarray as rio
from shapely.geometry import mapping
from datetime import date, datetime
import calendar
import pandas as pd
import numpy as np
from utils.spatial_plot import plot_precipitation_distribution
from utils.temporal_plot import plot_precipitation_trend
from climate_indices import indices, compute
from Analysis.spi_calculation import calculate_spi_with_ufunc
from load_dataset import load_main_dataset, load_hydrological_year_dataset
from plotly.subplots import make_subplots
from Analysis.spatial_trend import calculate_spatial_trend
from utils.spatial_trend_plot import spatial_trend_plot
from functools import lru_cache
import warnings
import CHIRPS_PREPROCESSING

import os


# MERGED_FILE_PATH = "Dataset/chirps_data/chirps_nepal_merged.nc"

# # 1. Download dataset if not present
# if not os.path.exists(MERGED_FILE_PATH):
#     print("Merged dataset not found, downloading data...")
#     CHIRPS_PREPROCESSING.download_chirps()
# else:
#     print("Merged dataset found, skipping download.")


# Load data with caching
@lru_cache(maxsize=None)
def load_cached_data():
    print("Loading datasets...")
    (shp, daily_dataset, monthly_dataset, yearly_dataset, 
     dataframe, min_year, max_year, min_date, max_date) = load_main_dataset()
    (seasonal_shp, seasonal_daily_dataset, seasonal_monthly_dataset, 
     seasonal_yearly_dataset, seasonal_dataframe, seasonal_min_year, 
     seasonal_max_year, seasonal_min_date, seasonal_max_date) = load_hydrological_year_dataset()
    
    return {
        'shp': shp,
        'daily_dataset': daily_dataset,
        'monthly_dataset': monthly_dataset,
        'yearly_dataset': yearly_dataset,
        'dataframe': dataframe,
        'min_year': min_year,
        'max_year': max_year,
        'min_date': min_date,
        'max_date': max_date,
        'seasonal_shp': seasonal_shp,
        'seasonal_daily_dataset': seasonal_daily_dataset,
        'seasonal_monthly_dataset': seasonal_monthly_dataset,
        'seasonal_yearly_dataset': seasonal_yearly_dataset,
        'seasonal_dataframe': seasonal_dataframe,
        'seasonal_min_year': seasonal_min_year,
        'seasonal_max_year': seasonal_max_year,
        'seasonal_min_date': seasonal_min_date,
        'seasonal_max_date': seasonal_max_date
    }

# Get data at startup
data = load_cached_data()

min_year = data['min_year']
max_year = data['max_year']
min_date = data['min_date']
max_date = data['max_date']



# Suppress warnings to improve console performance
warnings.filterwarnings('ignore')

# Define seasons (constant)
seasons = {
    'Winter': [12, 1, 2],
    'Pre-Monsoon': [3, 4, 5],
    'Monsoon': [6, 7, 8, 9],
    'Post-Monsoon': [10, 11]
}

# SPI classification (constant)
SPI_CLASSES = [
    [-float('inf'), -2.0, "Exceptional Drought"],
    [-2.0, -1.5, "Extreme Drought"],
    [-1.5, -1.0, "Severe Drought"],
    [-1.0, -0.5, "Moderate Drought"],
    [-0.5, 0.5, "Near Normal"],
    [0.5, 1.0, "Moderately Wet"],
    [1.0, 1.5, "Very Wet"],
    [1.5, 2.0, "Extremely Wet"],
    [2.0, float('inf'), "Exceptionally Wet"]
]

# Initialize the Dash app with optimized settings
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.LUX,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap"
    ],
    title="iMPACT | Climate Analytics",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "application-name", "content": "iMPACT Platform"},
        {"name": "description", "content": "Integrated Monitoring and Predictive Platform for Adaptation to Climate Threats"},
        {"rel": "icon", "href": "assets/favicon.png", "type": "image/png"}
    ],
    suppress_callback_exceptions=True  # Moved here from config
)

server = app.server



# Enhanced custom CSS styles
CUSTOM_STYLES = {
    "sidebar": {
        "background": "#f8f9fa",
        "padding": "0",
        "border-right": "1px solid #dee2e6",
        "height": "100vh",
        "text-transform": "none",
        "box-shadow": "2px 0 10px rgba(0,0,0,0.03)"
    },
    "card": {
        "border-radius": "12px",
        "box-shadow": "0 4px 20px rgba(0, 0, 0, 0.08)",
        "margin-bottom": "24px",
        "border": "none",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease"
    },
    "card_hover": {
        "transform": "translateY(-5px)",
        "box-shadow": "0 8px 25px rgba(0, 0, 0, 0.12)"
    },
    "title": {
        "color": "#2c3e50",
        "font-weight": "700",
        "margin-bottom": "24px",
        "font-family": "'Open Sans', sans-serif",
        "font-size": "2rem"
    },
    "subtitle": {
        "color": "#234464",
        "font-weight": "600",
        "margin-bottom": "20px",
        "font-family": "'Open Sans', sans-serif",
        "font-size": "1.5rem",
        "text-transform": "uppercase",
        "letter-spacing": "1px"
    },
    "control-label": {
        "font-weight": "600",
        "margin-bottom": "8px",
        "color": "#495057",
        "font-family": "'Open Sans', sans-serif",
        "font-size": "1rem"
    },
    "info-box": {
        "background": "#e8f4fd",
        "border-left": "1px solid #3498db",
        "padding": "10px",
        "margin-bottom": "2px",
        "border-radius": "8px",
        "font-family": "'Open Sans', sans-serif",
        "font-size": "1rem",
        "text-transform": "none",
    },
    "nav-link": {
        "font-size": "1rem",
        "padding": "0.75rem 1.5rem",
        "border-radius": "0.5rem",
        "transition": "all 0.3s ease",
        "color": "#495057",
        "font-weight": "500",
        "margin-bottom": "4px"
    },
    "nav-link-active": {
        "background": "#3498db",
        "color": "white",
        "font-weight": "600"
    },
    "content": {
        "padding": "2rem 2.5rem",
        "background": "#fdfdfd"
    },
    "stat-card": {
        "text-align": "center",
        "padding": "1.5rem",
        "border-radius": "10px",
        "background": "white",
        "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.05)"
    },
    "stat-value": {
        "font-size": "2rem",
        "font-weight": "700",
        "color": "#2c3e50"
    },
    "stat-label": {
        "font-size": "0.9rem",
        "color": "#7f8c8d",
        "text-transform": "uppercase",
        "letter-spacing": "1px"
    },
    "section": {
        "background": "white",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "20px",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
    } ,
    "featureCard": {
        "background": "#f8f9fa",
        "padding": "20px",
        "borderRadius": "8px",
        "marginBottom": "15px",
        "borderLeft": "4px solid #3498db",
        "height": "100%"
    },
    "section": {
        "background": "white",
        "borderRadius": "8px",
        "padding": "20px",
        "marginBottom": "20px",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
    },
    "header": {
        "background": "linear-gradient(135deg, #1a5276, #2980b9)",
        "color": "white",
        "padding": "20px 30px",
        "borderRadius": "8px",
        "marginBottom": "20px",
        "textAlign": "center",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
    },
    "sectionTitle": {
        "color": "#2c3e50",
        "borderBottom": "2px solid #3498db",
        "paddingBottom": "10px",
        "marginBottom": "20px",
        "fontWeight": "700"
    },
    "card": {  # Added this missing style
        "background": "#ffffff",
        "borderRadius": "8px",
        "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
        "marginBottom": "20px",
        "transition": "transform 0.2s ease"
    },

    "warning": {
        "background": "#fff3cd",
        "borderLeft": "5px solid #f39c12",
        "padding": "15px",
        "margin": "15px 0",
        "borderRadius": "4px"
    },
    "container": {
        "maxWidth": "1200px",
        "margin": "0 auto",
        "padding": "40px 20px",
        "fontFamily": "'Open Sans', sans-serif"
    }   
}

# Enhanced Navigation sidebar
sidebar = html.Div(
    [
        # Branding Header with improved design
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1(
                                    "iMPACT",
                                    style={
                                        "color": "#2c3e50",
                                        "font-weight": "800",
                                        "font-size": "clamp(2rem, 3.2vw, 3.2rem)",
                                        "margin-bottom": "0.25rem",
                                        "letter-spacing": "-1px",
                                        "font-family": "'Open Sans', sans-serif",
                                        "background": "linear-gradient(135deg, #3498db, #2c3e50)",
                                        "-webkit-background-clip": "text",
                                        "-webkit-text-fill-color": "transparent",
                                        "display": "inline-block",
                                        "text-align": "center",
                                        "text-transform": "none",
                                        "line-height": "1.2"
                                    }
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            "Integrated Monitoring and Predictive Platform for Adaptation to Climatic Threats",
                                            style={
                                                "font-weight": "600",
                                                "color": "#3498db",
                                                "font-size": "0.66rem"
                                            }
                                        ),                               
                                    ],
                                    style={
                                        "margin-bottom": "0.5rem"
                                    }
                                ),
                                html.Hr(style={
                                    "border-top": "2px solid rgba(52, 152, 219, 0.25)",
                                    "margin": "1rem 0 1.5rem 0",
                                    "width": "80%"
                                })
                            ],
                            style={
                                "padding": "2rem 1.5rem 1rem",
                                "text-align": "center"
                            }
                        )
                    ]
                )
            ],
            style={
                "background": "linear-gradient(to bottom, #ffffff 0%, #f8fafc 100%)",
                "border-bottom": "1px solid rgba(0,0,0,0.05)"
            }
        ),
        
        # Navigation Menu with improved styling
        dbc.Nav(
            [
                dbc.NavLink(
                    [
                        html.I(className="fas fa-home me-2"),
                        "About iMPACT"
                    ],
                    href="/",
                    active="exact",
                    id="home-link",
                    className="mb-2 nav-link-custom",
                    style=CUSTOM_STYLES["nav-link"]
                ),
                
                # Precipitation Analysis with dropdown
                html.Div(
                    [
                        dbc.NavLink(
                            [
                                html.I(className="fas fa-tint me-2"),
                                "Precipitation Analysis",
                                html.I(className="fas fa-chevron-down ms-auto", id="precipitation-arrow")
                            ],
                            href="#",
                            id="precipitation-collapse-link",
                            className="mb-2 nav-link-custom",
                            style=CUSTOM_STYLES["nav-link"]
                        ),
                        dbc.Collapse(
                            dbc.Nav(
                                [
                                    dbc.NavLink(
                                        [
                                            html.I(className="fas fa-calendar-alt me-2"),
                                            "Seasonal Analysis"
                                        ],
                                        href="/precipitation/seasonal",
                                        active="exact",
                                        className="ps-4 nav-link-custom",
                                        style={**CUSTOM_STYLES["nav-link"], "padding-left": "2rem"}
                                    ),
                                    dbc.NavLink(
                                        [
                                            html.I(className="fas fa-chart-line me-2"),
                                            "Temporal Analysis"
                                        ],
                                        href="/precipitation/temporal",
                                        active="exact",
                                        className="ps-4 nav-link-custom",
                                        style={**CUSTOM_STYLES["nav-link"], "padding-left": "2rem"}
                                    ),
                                    dbc.NavLink(
                                        [
                                            html.I(className="fas fa-bolt me-2"),
                                            "Climate Extremes"
                                        ],
                                        href="/precipitation/extremes",
                                        active="exact",
                                        className="ps-4 nav-link-custom",
                                        style={**CUSTOM_STYLES["nav-link"], "padding-left": "2rem"}
                                    )
                                ],
                                vertical=True,
                                pills=True,
                                style={"border-left": "2px solid #dee2e6"}
                            ),
                            id="precipitation-collapse",
                            is_open=False
                        )
                    ],
                    className="mb-2"
                ),
                # # DroughtAnalysis with dropdown

                html.Div(
                    [
                        dbc.NavLink(
                            [
                                html.I(className="fas fa-fire me-2"),  # Fixed: className (not classname)
                                "Drought Analysis",  # Fixed: "Drought" (not "Dought")
                                html.I(className="fas fa-chevron-down ms-auto", id="drought-arrow")  # Fixed: id consistency
                            ],
                            href="#",
                            id="drought-collapse-link",  # Matches callback ID
                            className="mb-2 nav-link-custom",
                            style=CUSTOM_STYLES["nav-link"]
                        ),
                        dbc.Collapse(
                            dbc.Nav(
                                [
                                    dbc.NavLink(
                                        [
                                            html.I(className="fas fa-chart-bar me-2"),
                                            "SPI Analysis"  # Fixed: Removed extra space
                                        ],
                                        href="/drought/spi",
                                        active="exact",  # Fixed: Removed space around =
                                        className="ps-4 nav-link-custom",
                                        style={**CUSTOM_STYLES["nav-link"], "padding-left": "2rem"}
                                    ),
                                    dbc.NavLink(
                                        [
                                            html.I(className="fas fa-chart-line me-2"),
                                            "ML-Based SPI Prediction"
                                        ],
                                        href="/drought/severity",
                                        active="exact",
                                        className="ps-4 nav-link-custom",
                                        style={**CUSTOM_STYLES["nav-link"], "padding-left": "2rem"}
                                    )
                                ],
                                vertical=True,
                                pills=True,
                                style={"border-left": "2px solid #dee2e6"}
                            ),
                            id="drought-collapse",  # Matches NavLink ID
                            is_open=False
                        )
                    ],
                    className="mb-2"
                )
            ],
        ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(
            [
                # Footer with improved design....
                html.Div(
                    [
                        html.Hr(style={
                            "border-top": "1px solid rgba(0,0,0,0.05)",
                            "margin": "1.5rem 0"
                        }),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-info-circle me-2"),
                                        f"Data: { data['min_year']}-{max_year}"
                                    ],
                                    className="mb-2"
                                ),
                                html.Div(
                                    [
                                        html.I(className="fas fa-map-marked-alt me-2"),
                                        "Region: Nepal"
                                    ],
                                    className="mb-2"
                                ),
                                html.Div(
                                    [
                                        html.I(className="fas fa-database me-2"),
                                        "Source: Climate Hazards Group InfraRed Precipitation with Station data (CHIRPS)"
                                    ]
                                )
                            ],
                            style={
                                "color": "#7b8a8b",
                                "font-size": "0.85rem",
                                "padding": "0 1.5rem"
                            }
                        ),
                        html.Div(
                            [
                                html.Hr(style={"margin": "1rem 0"}),
                                html.P(
                                    "v1.0.0",
                                    style={
                                        "color": "#bdc3c7",
                                        "font-size": "0.75rem",
                                        "text-align": "center",
                                        "margin-bottom": "0.5rem"
                                    }
                                ),
                                html.P(
                                    "© Developed by Pratistha Katwal",
                                    style={
                                        "color": "#bdc3c7",
                                        "font-size": "0.75rem",
                                        "text-align": "center"
                                    }
                                )
                            ]
                        )
                    ],
                    style={
                        "padding-bottom": "1rem"
                    }
                )
            ],
            className="mt-auto"
        )
    ],
    style=CUSTOM_STYLES["sidebar"],
    id="sidebar"
)

# Home Page Layout with improved design
header = html.Div(
    style={
        "background": "linear-gradient(rgba(255,255,255,0.9), url('assets/nepal-map-bg.png')",
        "backgroundSize": "contain",
        "backgroundPosition": "center",
        "backgroundRepeat": "no-repeat",
        "borderRadius": "12px",
        "marginBottom": "10px",  # Reduced from 1rem (16px) to 20px
    },
    children=[
        html.Div(
            className="text-center",
            style={
                "padding": "20px 20px",  # Reduced padding from py-5 (3rem/48px) to 40px
            },
            children=[
                html.H1(
                    "iMPACT NEPAL",
                    style={
                        "fontSize": "3.5rem",
                        "background": "linear-gradient(135deg, #3498db, #2c3e50)",
                        "WebkitBackgroundClip": "text",
                        "WebkitTextFillColor": "transparent",
                        "marginBottom": "0.5rem",  # Reduced from 1rem to 0.5rem
                        "textTransform": "none",
                        "fontWeight": "700",
                    }
                ),
                html.P(
                    "Integrated Monitoring and Predictive Platform for Adaptation to Climatic Threats",
                    style={
                        "color": "#7f8c8d",
                        "fontSize": "1.25rem",
                        "marginBottom": "1.5rem",  # Reduced from 2.5rem to 1.5rem
                    }
                ),
            ]
        )
    ]
)
# Overview Section
overview = html.Div(
    id="overview",
    style=CUSTOM_STYLES["section"],
    children=[
        html.P("A web-based platform designed to support researchers, policymakers, and practitioners in analyzing spatial and temporal climatic trends in Nepal from 1981 to the present.",style={"fontSize": "1.1rem", "marginBottom": "20px"}
        ),
        html.H3("Key Features", style={"marginTop": "30px", "color": "#2980b9"}),

        dbc.Row([
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Spatiotemporal Visualization", className="mb-0 fs-8")),
                        dbc.CardBody(
                            html.P("Interactive maps and charts showing rainfall patterns across Nepal", className="card-text")
                        ),
                    ],
                    style=CUSTOM_STYLES["featureCard"]
                ),
                md=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Trend Analysis", className="mb-0 fs-8")),
                        dbc.CardBody(
                            html.P("Mann-Kendall test for detecting statistically significant climate trends", className="card-text")
                        ),
                    ],
                    style=CUSTOM_STYLES["featureCard"]
                ),
                md=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Drought Monitoring", className="mb-0 fs-8")),
                        dbc.CardBody(
                            html.P("Standardized Precipitation Index (SPI) calculations at multiple time scales", className="card-text")
                        ),
                    ],
                    style=CUSTOM_STYLES["featureCard"]
                ),
                md=3
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4(" Extreme Events", className="mb-0 fs-8")),
                        dbc.CardBody(
                            html.P("ETCCDI indices for tracking extreme precipitation events", className="card-text")
                        ),
                    ],
                    style=CUSTOM_STYLES["featureCard"]
                ),
                md=3
            )
        ], className="mb-4"),

        html.P(
            "Primary Users: Climate researchers, meteorologists and disaster risk managers.",
            style={"fontWeight": "600", "marginTop": "20px"}
        )
    ]
)

# Data Source Section
data_source = html.Div(
    id="data-source",
    style=CUSTOM_STYLES["section"],
    children=[
        html.H2("Data Source", style=CUSTOM_STYLES["sectionTitle"]),
        html.H3(
            "CHIRPS (Climate Hazards Group InfraRed Precipitation with Station Data)",
            style={"color": "#2980b9", "marginBottom": "20px"}
        ),

        dbc.ListGroup(
            [
                dbc.ListGroupItem([html.Strong("Spatial Resolution:"), " 0.05° (~5 km)"], className="d-flex justify-content-between align-items-center"),
                dbc.ListGroupItem([html.Strong("Spatial Coverage:"), " Nepal "], className="d-flex justify-content-between align-items-center"),
                dbc.ListGroupItem([html.Strong("Temporal Coverage:"), " 1981–Present"], className="d-flex justify-content-between align-items-center"),
                dbc.ListGroupItem([html.Strong("Temporal Resolution:"), " Daily, Monthly and Yearly"], className="d-flex justify-content-between align-items-center"),
                dbc.ListGroupItem([html.Strong("Variable:"), " Precipitation (mm)"], className="d-flex justify-content-between align-items-center")
            ],
            flush=True,
            style={"marginBottom": "20px"}
        ),

        html.P(
            "CHIRPS blends satellite imagery with ground-based station data to generate high-resolution, bias-corrected rainfall estimates.",
            style={"marginTop": "15px"}
        )
    ]
)

# Precipitation Analysis Section
analysis_modules = html.Div(className="container py-4", children=[
    html.H2("Analysis Modules", className="text-center mb-4", style=CUSTOM_STYLES["header"]),
    dbc.Row([
        # Precipitation Analysis Card
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Precipitation Analysis", className="mb-0 text-center")),
            dbc.CardBody([
                html.Ul([
                    html.Li("Seasonal precipitation patterns"),
                    html.Li("Aggregated statistics"),
                    html.Li("Extreme indices (ETCCDI)")
                ]),
                dbc.Badge("Available", color="success", className="mb-3")
            ]),
            dbc.CardFooter(
                dbc.ButtonGroup([
                    dbc.Button("Explore", href="/precipitation/seasonal", color="primary", outline=True),
                    dbc.Button("Learn More", id="ppt-btn", color="primary")
                ], className="w-100")
            )
        ], style=CUSTOM_STYLES["card"]), md=6, className="mb-4"),

        # Drought Analysis Card
        dbc.Col(dbc.Card([
            dbc.CardHeader(html.H4("Drought Monitoring", className="mb-0 text-center")),
            dbc.CardBody([
                html.Ul([
                    html.Li("SPI at multiple timescales"),
                    html.Li("Meteorological to long-term drought")
                ]),
                dbc.Badge("Available", color="success", className="mb-3")
            ]),
            dbc.CardFooter(
                dbc.ButtonGroup([
                    dbc.Button("Explore", href="/drought/spi", color="primary", outline=True),
                    dbc.Button("Learn More", id="drought-btn", color="primary")
                ], className="w-100")
            )
        ], style=CUSTOM_STYLES["card"]), md=6, className="mb-4")
    ])
])

# Limitations Section
limitations = html.Div(
    id="limitations",
    style=CUSTOM_STYLES["section"],
    children=[
        html.H2("Limitations", style=CUSTOM_STYLES["sectionTitle"]),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("CHIRPS estimates not yet validated against Nepal DHM ground stations"),
                dbc.ListGroupItem("Algorithms require peer review by climatology experts")
            ],
            flush=True
        ),

        dbc.Alert(
            [
                html.H4("⚠️ Disclaimer", style={"color": "#c0392b", "marginTop": "0"}),
                html.P("iMPACT is for exploratory analysis only. Outputs should not be used for operational decision-making without expert validation.")
            ],
            color="warning",
            style=CUSTOM_STYLES["warning"]
        )
    ]
)

# Future Plans Section
future_plans = html.Div(
    id="future-plans",
    style=CUSTOM_STYLES["section"],
    children=[
        html.H2("Future Plans", style=CUSTOM_STYLES["sectionTitle"]),
        html.H3("Planned Enhancements", style={"color": "#2980b9"}),
        dbc.ListGroup(
            [
                dbc.ListGroupItem("Temperature datasets and trend analysis"),
                dbc.ListGroupItem("Internationally recognized temperature extremity indices"),
                dbc.ListGroupItem("Ground-station data validation")
            ],
            flush=True
        )
    ]
)

# Collaboration Section
collaboration = html.Div(
    id="collaboration",
    style=CUSTOM_STYLES["section"],
    children=[
        html.H2("Collaboration & Peer Review", style=CUSTOM_STYLES["sectionTitle"]),
        html.P("Help improve iMPACT's scientific rigor and applicability:"),

        dbc.Row([
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Expert Review", style={"color": "#2980b9"})),
                        dbc.CardBody([
                            html.P("Climate scientists for methodology validation", className="card-text")
                        ])
                    ],
                    style={"height": "100%"}
                ),
                md=6
            ),
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Collaboration", style={"color": "#2980b9"})),
                        dbc.CardBody([
                            html.P("Government agencies for ground-station data", className="card-text"),
                            html.P("Research institutions for joint studies", className="card-text")
                        ])
                    ],
                    style={"height": "100%"}
                ),
                md=6
            )
        ], className="mb-4"),

        html.Div(
            style={"textAlign": "center", "marginTop": "30px"},
            children=[
                html.H4("Get In Touch", style={"color": "#2980b9", "marginBottom": "20px"}),
                dbc.Button(
                    "Email Me",
                    color="primary",
                    href="mailto:pratisthaktwl1@gmail.com",
                    style={
                        "padding": "12px 30px",
                        "fontSize": "1.1rem",
                        "borderRadius": "4px",
                        "marginBottom": "15px"
                    }
                )
            ]
        )
    ]
)

# Modals
ppt_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Precipitation Analysis")),
    dbc.ModalBody([
        html.H4("Purpose"),
        html.P("Track shifts in precipitation patterns crucial for long-term planning and climate adaptation."),

        html.H4("Features"),
        html.H5("1. Seasonal Distribution and Trends"),
        html.P("Visualizes average precipitation across Nepal during selected seasons:"),
        dbc.ListGroup([
            dbc.ListGroupItem("Winter (Dec-Feb)"),
            dbc.ListGroupItem("Pre-Monsoon (Mar-May)"),
            dbc.ListGroupItem("Monsoon (Jun-Sep)"),
            dbc.ListGroupItem("Post-Monsoon (Oct-Nov)")
        ], flush=True, className="mb-3"),

        html.H5("2. Extreme Precipitation Indices"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Index"), html.Th("Description"), html.Th("Units")
            ])),
            html.Tbody([
                html.Tr([html.Td("R1mm"), html.Td("Rainy days (≥1mm)"), html.Td("Days")]),
                html.Tr([html.Td("R10mm"), html.Td("Heavy precipitation days"), html.Td("Days")]),
                html.Tr([html.Td("R20mm"), html.Td("Very heavy precipitation days"), html.Td("Days")]),
                html.Tr([html.Td("R95p"), html.Td("Very wet days (95th %ile)"), html.Td("mm")]),
                html.Tr([html.Td("R99p"), html.Td("Extremely wet days (99th %ile)"), html.Td("mm")])
            ])
        ], bordered=True, hover=True)
    ]),
    dbc.ModalFooter(
        dbc.Button("Close", id="close-ppt-modal", className="ml-auto")
    )
], id="ppt-modal", size="lg")

drought_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle("Drought Monitoring")),
    dbc.ModalBody([
        html.H4("Purpose"),
        html.P("Monitor and analyze drought using Standardized Precipitation Index (SPI)"),

        html.H4("Features"),
        html.P("SPI at different accumulation periods:"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Scale"), html.Th("Drought Type"), html.Th("Application")
            ])),
            html.Tbody([
                html.Tr([html.Td("SPI-3"), html.Td("Meteorological"), html.Td("Short-term dry spells")]),
                html.Tr([html.Td("SPI-6"), html.Td("Agricultural"), html.Td("Soil moisture impact")]),
                html.Tr([html.Td("SPI-12"), html.Td("Hydrological"), html.Td("Water availability")]),
                html.Tr([html.Td("SPI-24"), html.Td("Long-term"), html.Td("Ecosystem impacts")])
            ])
        ], bordered=True, hover=True, className="mb-3"),

        html.P("The climate-indices Python package is used for SPI calculation."),
        dbc.Alert("SPI forecasting using machine learning is under development",
                 color="info", className="mt-3")
    ]),
    dbc.ModalFooter(
        dbc.Button("Close", id="close-drought-modal", className="ml-auto")
    )
], id="drought-modal", size="lg")

# =============================================================================
# APP LAYOUT
# =============================================================================
home_layout = html.Div(
    style={"background": "#f5f7fa", "minHeight": "100vh"},
    children=[
        dcc.Location(id='url', refresh=False),  # Added this missing component
        html.Div(
            style=CUSTOM_STYLES["container"],
            children=[
                header,
                overview,
                data_source,
                analysis_modules,
                limitations,
                future_plans,
                collaboration,
                ppt_modal,  # Added modals to layout
                drought_modal
            ]
        )
    ]
)

# =============================================================================
# CALLBACKS
# =============================================================================
# Callbacks for modals
@app.callback(
    Output("ppt-modal", "is_open"),
    [Input("ppt-btn", "n_clicks"),
     Input("close-ppt-modal", "n_clicks")],
    [State("ppt-modal", "is_open")],
)
def toggle_ppt_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("drought-modal", "is_open"),
    [Input("drought-btn", "n_clicks"),
     Input("close-drought-modal", "n_clicks")],
    [State("drought-modal", "is_open")],
)
def toggle_drought_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open
# Precipitation Analysis Layout (container for the tabs)
precipitation_layout = html.Div([
    # Loading spinner for smoother transitions
    dcc.Loading(
        id="loading-precipitation",
        type="circle",
        children=html.Div(id="precipitation-content")
    )
])
#Main drought analysis layout
drought_analysis_layout = html.Div([
    # Loading spinner for smoother transitions
    dcc.Loading(
        id="loading-drought",
        type="circle",
        children=html.Div(id="drought-content")
    )
])
# Seasonal Analysis Page
seasonal_layout = html.Div([
    html.H2("Season-wise precipitation spatial patterns and temporal trends", style=CUSTOM_STYLES["subtitle"]),
    
    dbc.Card(
        dbc.CardBody([
            html.H4("Analysis Parameters", style={**CUSTOM_STYLES["subtitle"], "text-transform": "none","font-size": "1.2rem"}),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Season:", style=CUSTOM_STYLES["control-label"]),
                    dcc.Dropdown(
                        id='season-selector',
                        options=[{'label': k, 'value': k} for k in seasons.keys()],
                        value='Monsoon',
                        className="mb-3"
                    )
                ], width=4),
                
                dbc.Col([
                    html.Label("Select Year Range:", style=CUSTOM_STYLES["control-label"]),
                    dcc.RangeSlider(
                        id='year-range-slider',
                        min=min_year,
                        max=max_year,
                        value=[min_year, max_year],
                        marks={str(year): str(year) for year in range(min_year, max_year+1, 5)},
                        step=1,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="p-3"
                    )
                ], width=8)
            ])
        ]),
        style=CUSTOM_STYLES["card"]
    ),
    
    dbc.Card(
        dbc.CardBody([
            html.Div(id='seasonal-description'),
            dbc.Alert(id="seasonal-warning"),


            #Adding radioitems ##pasta
            dbc.RadioItems(
                id='trend-plot-selector',
                options=[
                    {'label': 'Spatial Distribution', 'value': 'distribution'},
                    {'label': 'Spatial Trend', 'value': 'trend' }],
                value='distribution',
                inline=True,
                style={'margin-bottom': '10px'}
            ),
            ##

            dcc.Graph(id='seasonal-spatial-plot'),  # First graph (full width)
            html.Br(),  # Optional: Adds a small gap between graphs
            dcc.Graph(id='seasonal-temporal-plot')   # Second graph (full width)
        ]),
        style=CUSTOM_STYLES["card"]
    )
])

# Temporal Analysis Page
temporal_layout = html.Div([
    html.H2("Temporal Precipitation Analysis", style=CUSTOM_STYLES["subtitle"]),
    
    dbc.Card(
        dbc.CardBody([
            html.H4("Analysis Parameters", style=CUSTOM_STYLES["subtitle"]),
            dbc.Row([
                dbc.Col([
                    html.Label("Time Aggregation Level:", style=CUSTOM_STYLES["control-label"]),
                    dcc.Dropdown(
                        id='freq-selector',
                        options=[
                            {'label': 'Daily', 'value': 'Daily'},
                            {'label': 'Monthly', 'value': 'Monthly'},
                            {'label': 'Yearly', 'value': 'Yearly'}
                        ],
                        value='Monthly',
                        className="mb-3"
                    )
                ], width=4)
            ]),
            
            html.Div(id='temporal-date-controls'),
            
            html.Div(
                dbc.Row([
                    dbc.Col([
                        html.Label("Start Date:", style=CUSTOM_STYLES["control-label"]),
                        dcc.DatePickerSingle(
                            id='daily-start-date',
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            initial_visible_month=min_date,
                            date=min_date,
                            className="mb-3"
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("End Date:", style=CUSTOM_STYLES["control-label"]),
                        dcc.DatePickerSingle(
                            id='daily-end-date',
                            min_date_allowed=min_date,
                            max_date_allowed=max_date,
                            initial_visible_month=max_date,
                            date=max_date,
                            className="mb-3"
                        )
                    ], width=6)
                ]),
                id='daily-controls',
                style={'display': 'none'}
            ),
            
            html.Div(
                dbc.Row([
                    dbc.Col([
                        html.Label("Start Year:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='monthly-start-year',
                            options=[{'label': str(year), 'value': year} for year in range(min_year, max_year+1)],
                            value=min_year,
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Start Month:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='monthly-start-month',
                            options=[{'label': month, 'value': i+1} for i, month in enumerate(list(calendar.month_name)[1:])],
                            value=1,
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("End Year:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='monthly-end-year',
                            options=[{'label': str(year), 'value': year} for year in range(min_year, max_year+1)],
                            value=max_year,
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("End Month:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='monthly-end-month',
                            options=[{'label': month, 'value': i+1} for i, month in enumerate(list(calendar.month_name)[1:])],
                            value= 12,
                            className="mb-3"
                        )
                    ], width=3)
                ]),
                id='monthly-controls',
                style={'display': 'none'}
            ),
            
            html.Div(
                dbc.Row([
                    dbc.Col([
                        html.Label("Start Year:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='yearly-start-year',
                            options=[{'label': str(year), 'value': year} for year in range(min_year, max_year+1)],
                            value=min_year,
                            className="mb-3"
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("End Year:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='yearly-end-year',
                            options=[{'label': str(year), 'value': year} for year in range(min_year, max_year+1)],
                            value=max_year,
                            className="mb-3"
                        )
                    ], width=6)
                ]),
                id='yearly-controls',
                style={'display': 'none'}
            )
        ]),
        style=CUSTOM_STYLES["card"]
    ),
    
    dbc.Card(
        dbc.CardBody([
            ##pasta

            dbc.RadioItems(
                id='temporal-trend-plot-selector',
                options=[
                    {'label':'Spatial Distribution','value':'distribution'},
                    {'label': 'Spatial Trend', 'value': 'trend'}
                ],
            value='distribution',
            inline=True,
            style={'margin-bottom':'10px'}
            ),
            dcc.Graph(id='temporal-spatial-plot')
        ]),
        style=CUSTOM_STYLES["card"]
    ),
    
    dbc.Card(
        dbc.CardBody([
            dcc.Graph(id='temporal-trend-plot')
        ]),
        style=CUSTOM_STYLES["card"]
    )
])

# Indices Analysis Page
indices_layout = html.Div([
    html.H2("Climate Extremes Indices", style=CUSTOM_STYLES["subtitle"]),
    
    dbc.Card(
        dbc.CardBody([
            html.H4("Analysis Parameters", style=CUSTOM_STYLES["subtitle"]),
            dbc.Row([
                dbc.Col([
                    html.Label("Analysis Type:", style=CUSTOM_STYLES["control-label"]),
                    dcc.Dropdown(
                        id='indices-type-selector',
                        options=[
                            {'label': 'Threshold based', 'value': 'threshold'},
                            {'label': 'Quantile based', 'value': 'quantile'}
                        ],
                        value='threshold',
                        className="mb-3"
                    )
                ], width=6)
            ]),
            
            html.Div(
                dbc.Row([
                    dbc.Col([
                        html.Label("Precipitation Threshold (mm):", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='threshold-selector',
                            options=[{'label': f'{mm} mm', 'value': mm} for mm in [1, 10, 20]],
                            value=10,
                            className="mb-3"
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("Year Range:", style=CUSTOM_STYLES["control-label"]),
                        dcc.RangeSlider(
                            id='indices-year-range-slider',
                            min=min_year,
                            max=max_year,
                            value=[min_year, max_year],
                            marks={str(year): str(year) for year in range(min_year, max_year+1, 5)},
                            step=1,
                            tooltip={"placement": "bottom", "always_visible": True},
                            className="p-3"
                        )
                    ], width=6)
                ]),
                id='threshold-controls',
                style={'display': 'block'}
            ),
            
            html.Div(
                dbc.Row([
                    dbc.Col([
                        html.Label("Percentile Threshold:", style=CUSTOM_STYLES["control-label"]),
                        dcc.Dropdown(
                            id='percentile-selector',
                            options=[{'label': f'{p}th Percentile', 'value': p} for p in [95, 99]],
                            value=95,
                            className="mb-3"
                        )
                    ], width=6)
                ]),
                id='quantile-controls',
                style={'display': 'none'}
            )
        ]),
        style=CUSTOM_STYLES["card"]
    ),
    
    dbc.Card(
        dbc.CardBody([
            dbc.RadioItems(
                id= 'extremes-plot-selector',
                options=[
                    {'label':'Spatial Distribution', 'value':'distribution'},
                {'label': 'Spatial Trend', 'value': 'trend'}],
                value= 'distribution',
                inline=True,
                style={'margin-bottom': '10px'}
            ),

            dcc.Graph(id='indices-spatial-plot')
        ]),
        style=CUSTOM_STYLES["card"]
    ),
    
    dbc.Card(
        dbc.CardBody([
            dcc.Graph(id='indices-temporal-plot')
        ]),
        style=CUSTOM_STYLES["card"]
    )
])
 
# Drought layout
spi_layout = html.Div([
    html.H2("Drought Monitoring and Prediction", style=CUSTOM_STYLES["subtitle"]),
    dbc.Card(
        dbc.CardBody([
            html.H4("Analysis Parameters", style=CUSTOM_STYLES["subtitle"]),
            dbc.Row([
                dbc.Col([  # Fixed: Changed 'dbc.col' to 'dbc.Col'
                    html.Label("Select SPI Type:", style=CUSTOM_STYLES["control-label"]),  # Fixed: Changed 'label' to 'Label' and 'elect' to 'Select'
                    dcc.Dropdown(
                        id='spi-selector',
                        options=[{'label': str(spi), 'value': spi} for spi in [3,6,12,24]],  # Fixed: Added proper dropdown options format
                        value=3,
                        className="mb-3"
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Select Year Range:", style=CUSTOM_STYLES["control-label"]),
                    dcc.Dropdown(
                        id='year-selected',
                        options=[{'label': str(year), 'value': year} for year in range(min_year, max_year+1)],  # Fixed: Added max_year (you'll need to define this)
                        value=min_year,
                        className="mb-3"
                    )
                ], width=6),
                dbc.Col([  # Fixed: Added missing comma after previous Col
                    html.Label("Select Month:", style=CUSTOM_STYLES["control-label"]),
                    dcc.Dropdown(
                        id='month-selected',
                        options=[{'label': month, 'value': i+1} for i, month in enumerate(list(calendar.month_name)[1:])],
                        value=1,
                        className="mb-3"
                    )
                ], width=6)
            ]),
        ]),
        id='spi_layout',
        style={'display': 'block'}
    ),
    dbc.Card(
        dbc.CardBody([
            dcc.Graph(id='spi-spatial-plot') ,
        ]),
        style=CUSTOM_STYLES["card"]
    )
])




# Main app layout
app.layout = dbc.Container(
    [
        dcc.Location(id="url"),
        dbc.Row(
            [
                dbc.Col(sidebar, width=2, className="p-0"),
                dbc.Col(html.Div(id="page-content"), width=10, className="p-4")
            ],
            className="g-0"
        )
    ],
    fluid=True,
    style={"min-height": "100vh"}
)



# Callback to toggle precipitation dropdown

@app.callback(
    Output("precipitation-collapse", "is_open"),
    Output("precipitation-arrow", "className"),
    [Input("precipitation-collapse-link", "n_clicks")],
    [State("precipitation-collapse", "is_open")]
)
def toggle_precipitation_collapse(n, is_open):
    if n:
        if is_open:
            return False, "fas fa-chevron-down ms-auto"
        else:
            return True, "fas fa-chevron-up ms-auto"
    return is_open, "fas fa-chevron-down ms-auto"




# Callback to toggle drought dropdown

@app.callback(
    Output("drought-collapse", "is_open"),
    Output("drought-arrow", "className"),
    [Input("drought-collapse-link", "n_clicks")],
    [State("drought-collapse", "is_open")]
)
def toggle_drought_collapse(n, is_open):
    if n:
        if is_open:
            return False, "fas fa-chevron-down ms-auto"
        else:
            return True, "fas fa-chevron-up ms-auto"
    return is_open, "fas fa-chevron-down ms-auto"


# Update the active nav link callback
@app.callback(
    [Output("home-link", "style"),
     Output("precipitation-collapse-link", "style"),
     Output("drought-collapse-link", "style")],
    [Input("url", "pathname")]
)
def update_nav_links(pathname):
    home_style = CUSTOM_STYLES["nav-link"]
    precip_style = CUSTOM_STYLES["nav-link"]
    drought_style = CUSTOM_STYLES["nav-link"]
    
    if pathname == "/":
        home_style = {**home_style, **CUSTOM_STYLES["nav-link-active"]}
    elif pathname.startswith("/precipitation"):
        precip_style = {**precip_style, **CUSTOM_STYLES["nav-link-active"]}
    elif pathname == "/drought":
        drought_style = {**drought_style, **CUSTOM_STYLES["nav-link-active"]}
    
    return home_style, precip_style, drought_style



# Callback to switch between main pages
# Update your page content callback
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        return home_layout
    elif pathname.startswith("/precipitation"):
        return precipitation_layout
    elif pathname.startswith("/drought"):
        return drought_analysis_layout  # Change this when you implement drought layout
    return home_layout

# Callback to switch between precipitation sub-pages
@app.callback(
    Output("precipitation-content", "children"),
    [Input("url", "pathname")]
)
def render_precipitation_content(pathname):
    if pathname == "/precipitation" or pathname == "/precipitation/seasonal":
        return seasonal_layout
    elif pathname == "/precipitation/temporal":
        return temporal_layout
    elif pathname == "/precipitation/extremes":
        return indices_layout
    return seasonal_layout  # Default to seasonal


# Switch between drought analysis and other pages
@app.callback(
    Output("drought-content", "children"),
    [Input("url", "pathname")]
)

def render_drought_content(pathname):
    if pathname == "/drought" or pathname == "/drought/spi":
        return spi_layout
    return home_layout  # Default to drought layout

####

from dash.dependencies import Input, Output
from datetime import datetime

@app.callback(
    Output('seasonal-warning', 'children'),
    Output('seasonal-warning', 'is_open'),
    Input('season-selector', 'value'),
    Input('year-range-slider', 'value')
)
def check_incomplete_season(selected_season, year_range):
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    # Special handling for winter (Dec-Jan-Feb)
    if selected_season == 'Winter':
        # Winter of 2025 includes Dec 2024 (already complete) + Jan/Feb 2025
        if year_range[1] == current_year:
            # Only Jan/Feb might be incomplete
            incomplete_months = [m for m in [1, 2] if m > current_month]
        else:
            # Future winters are complete if the year before is complete
            incomplete_months = []
    else:
        # For other seasons
        if year_range[1] == current_year:
            season_months = seasons[selected_season]
            incomplete_months = [m for m in season_months if m > current_month]
        else:
            incomplete_months = []
    
    if incomplete_months:
        missing_months = ", ".join([calendar.month_name[m] for m in incomplete_months])
        return (
            f"⚠️ Warning: {selected_season} {year_range[1]} data is incomplete (missing {missing_months}). "
            "Results may be biased.",
            True
        )
    return ("", False)



############
@app.callback(
    Output('monthly-end-month', 'options'),
    Output('monthly-end-month', 'value'),  # Reset value if invalid
    Input('monthly-end-year', 'value'),
)
def update_end_month_options(selected_end_year):
    # If selected year == max_year, restrict months
    if selected_end_year == max_date.year:
        options = [
            {'label': calendar.month_name[i], 'value': i}
            for i in range(1, max_date.month + 1)
        ]
        # Ensure current value is valid (e.g., if previously December was selected)
        current_month = max_date.month
        return options, current_month
    else:
        options = [
            {'label': calendar.month_name[i], 'value': i}
            for i in range(1, 13)
        ]
        return options, 12  # Default to December for past years
    
    
# Seasonal Analysis Callbacks

@app.callback(
    [Output('seasonal-description', 'children'),
     Output('seasonal-temporal-plot', 'figure'),
     Output('seasonal-spatial-plot', 'figure')],
    [Input('season-selector', 'value'),
     Input('year-range-slider', 'value'),
     Input('trend-plot-selector', 'value')]
)
def update_seasonal_analysis(selected_season, selected_years,plot_type):
    # Filter dataset
    start_date = f"{selected_years[0]}-01-01"
    end_date = f"{selected_years[1]}-12-31"
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    filtered_dataset = data['seasonal_monthly_dataset'].sel(time=slice(start_date, end_date))
    
    # Create description
    description = dbc.Alert(
        [
            html.H4(f"Selected Season: {selected_season}", className="alert-heading"),
            html.P(f"Analyzing precipitation patterns from {start_date.year} to {end_date.year}")
        ],
        color="info",
        style={**CUSTOM_STYLES["info-box"],"text-transform": "none", "font-size": "1rem"}
    )
    warning_alert = dbc.Alert(
        id="seasonal-warning",
        color="warning",
        dismissable=True,
        is_open=False,  # Hidden by default
        className="mt-3"
    )
#pasta
    # Spatial plot
    months = seasons[selected_season]
    spatial_data = filtered_dataset.sel(time=filtered_dataset['time.month'].isin(months))
    yearly_spatial = spatial_data.resample(time='YE').sum(skipna=True)
    yearly_spatial_ = yearly_spatial.mean(dim=['time'])
    yearly_spatial_ = yearly_spatial_.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)
    
    da = yearly_spatial_['tp']
    lat = da['lat'].values
    lon = da['lon'].values
    z = da.values

    if plot_type == 'distribution':
        spatial_fig = plot_precipitation_distribution(
            z=z,
            x=lon,
            y=lat,
            colorbar='Total Precipitation (mm)',
            hovertemplate='<b>Longitude</b>: %{x}<br><b>Latitude</b>: %{y}<br><b>Total Precipitation</b>: %{z:.2f} mm<extra></extra>',
            title=f"<b>{selected_season} Average Precipitation ({start_date.year} to {end_date.year})</b><br>Spatial Distribution",
            title2="Precipitation (mm)"
        )
    else:
        trend_data= calculate_spatial_trend(yearly_spatial)
        spatial_fig= spatial_trend_plot(trend_data,"year")
    
    
    # Temporal plot
    yearly_spatial_latlonmean = yearly_spatial.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)   
    df_yearly_spatial = yearly_spatial_latlonmean.mean(dim=['lat','lon']).to_dataframe().reset_index()
    df_yearly_spatial['year'] = df_yearly_spatial['time'].dt.year
    season_dataframe = df_yearly_spatial.groupby('year')['tp'].sum()
    values = season_dataframe.values
    
    temporal_fig = None
    if len(values)>2:
        mk_result = mk.original_test(values)
        y_max = values.max()
        y_min = values.min()
        y_pad = y_max * 0.1

        temporal_fig = plot_precipitation_trend(
            x=season_dataframe.index.astype(int),
            y=season_dataframe.values,
            legend='Total Precipitation',
            hovertemplate='<b>Year</b>: %{x}<br><b>Total Precipitation</b>: %{y:.2f} mm<extra></extra>',
            title=f"<b>{selected_season} Average Precipitation ({start_date.year} to {end_date.year})</b><br>Temporal Trend",
            yaxis='Precipitation (mm/yr)',
            y_max=y_max,
            y_min=y_min,
            y_pad=y_pad,
            mk_result=mk_result,
            unit='mm/year'
        )
    else:
        temporal_fig = go.Figure()
        temporal_fig.update_layout(
            title="Not enough data points for trend analysis",
            xaxis_title="Year",
            yaxis_title="Precipitation (mm)"
        )
    
    return description, temporal_fig, spatial_fig

# Temporal Analysis Callbacks
@app.callback(
    [Output('daily-controls', 'style'),
     Output('monthly-controls', 'style'),
     Output('yearly-controls', 'style')],
    [Input('freq-selector', 'value')]
)
def update_control_visibility(selected_freq):
    daily_style = {'display': 'block'} if selected_freq == 'Daily' else {'display': 'none'}
    monthly_style = {'display': 'block'} if selected_freq == 'Monthly' else {'display': 'none'}
    yearly_style = {'display': 'block'} if selected_freq == 'Yearly' else {'display': 'none'}
    return daily_style, monthly_style, yearly_style

### Update month options based on selected year for monthly analysis

@app.callback(
    [Output('temporal-spatial-plot', 'figure'),
     Output('temporal-trend-plot', 'figure')],
    [Input('freq-selector', 'value'),
     Input('daily-start-date', 'date'),
     Input('daily-end-date', 'date'),
     Input('monthly-start-year', 'value'),
     Input('monthly-start-month', 'value'),
     Input('monthly-end-year', 'value'),
     Input('monthly-end-month', 'value'),
     Input('yearly-start-year', 'value'),
     Input('yearly-end-year', 'value'),
     Input('temporal-trend-plot-selector', 'value')]
)
def update_temporal_analysis(selected_freq, daily_start, daily_end, 
                           monthly_start_year, monthly_start_month, 
                           monthly_end_year, monthly_end_month,
                           yearly_start_year, yearly_end_year, plot_type):
    # Determine the dataset and date range based on frequency
    if selected_freq == "Daily":
        if not daily_start or not daily_end:
            return go.Figure(), go.Figure()
            
        dataset = data['daily_dataset']
        start_date = daily_start
        end_date = daily_end
    elif selected_freq == "Monthly":
        if (not monthly_start_year or not monthly_start_month or 
            not monthly_end_year or not monthly_end_month):
            return go.Figure(), go.Figure()
            
        dataset = data['monthly_dataset']
        start_date = date(int(monthly_start_year), int(monthly_start_month), 1)
        end_date = date(int(monthly_end_year), int(monthly_end_month), 1)
        
        # Adjust to get the last day of the month
        start_str = pd.Timestamp(start_date).strftime('%Y-%m-%d')
        start_date = pd.Timestamp(start_str).to_period('M').end_time.strftime('%Y-%m-%d')
        end_str = pd.Timestamp(end_date).strftime('%Y-%m-%d')
        end_date = pd.Timestamp(end_str).to_period('M').end_time.strftime('%Y-%m-%d')
    else:  # Yearly
        if not yearly_start_year or not yearly_end_year:
            return go.Figure(), go.Figure()
            
        dataset = data['yearly_dataset']
        start_date = date(int(yearly_start_year), 1, 1)
        end_date = date(int(yearly_end_year), 12, 31)
    
    # Rest of your processing remains the same...
    selected_data = dataset.sel(time=slice(str(start_date), str(end_date)))
    start_year = pd.to_datetime(start_date).year
    end_year = pd.to_datetime(end_date).year
    
    #pasta
    # # Spatial plot
    
    avg_precip = selected_data.mean(dim='time')
    avg_precip = avg_precip.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)
    da3 = avg_precip['tp']
    lat3 = da3['lat'].values
    lon3 = da3['lon'].values
    z3 = da3.values
    if plot_type=='distribution':
        spatial_fig = go.Figure()
        if not (np.isnan(z3).all() or np.nansum(z3) == 0):
            spatial_fig = plot_precipitation_distribution(
                z=z3,
                x=lon3,
                y=lat3,
                colorbar='ppt(mm)',
                hovertemplate='<b>Longitude</b>: %{x}<br><b>Latitude</b>: %{y}<br><b>Average Precipitation (mm)</b>: %{z:.2f} mm<extra></extra>',
                title=f"<b>Average {selected_freq} Precipitation ({start_year} to {end_year})</b><br>Spatial Distribution",
                title2="Precipitation (mm)"
            )
        else:
            spatial_fig.update_layout(
                title="No precipitation data available for selected range",
                xaxis_title="Longitude",
                yaxis_title="Latitude"
            )
    else:
        spatial_trend = calculate_spatial_trend(selected_data)
        time_unit = {
            'Daily': 'day',
            'Monthly': 'month',
            'Yearly': 'year'
        }.get(selected_freq, 'year')  # Default to month if not matched

        spatial_fig = spatial_trend_plot(spatial_trend, time_unit)


    # Temporal plot
    dataframe_avg_precip = selected_data['tp'].mean(dim=['lat', 'lon']).to_dataframe(name='tp').reset_index()
    values = dataframe_avg_precip['tp'].dropna().values
    
    temporal_fig = go.Figure()
    if len(values) >= 2:
        try:
            mk_result = mk.original_test(values)
            y_max = values.max()
            y_min = values.min()
            y_pad = y_max * 0.1

            temporal_fig = plot_precipitation_trend(
                x=dataframe_avg_precip['time'],
                y=dataframe_avg_precip['tp'],
                legend='Average Precipitation',
                hovertemplate='<b>Year</b>: %{x}<br><b>Average Precipitation</b>: %{y:.1f} mm<extra></extra>',
                title=f"<b>Average {selected_freq} Precipitation ({start_year} to {end_year})</b><br>Temporal Trend",
                yaxis='Average Precipitation (mm)',
                mk_result=mk_result,
                y_max=y_max,
                y_min=y_min,
                y_pad=y_pad,
                unit='mm'
            )
        except ValueError as e:
            temporal_fig.update_layout(
                title=f"Error in trend analysis: {str(e)}",
                xaxis_title="Time",
                yaxis_title="Precipitation (mm)"
            )
    else:
        temporal_fig.update_layout(
            title="Not enough data points for trend analysis",
            xaxis_title="Time",
            yaxis_title="Precipitation (mm)"
        )
    
    return spatial_fig, temporal_fig

# Indices Analysis Callbacks
@app.callback(
    [Output('threshold-controls', 'style'),
     Output('quantile-controls', 'style')],
    [Input('indices-type-selector', 'value')]
)
def update_indices_controls_visibility(selected_type):
    threshold_style = {'display': 'block'} if selected_type == 'threshold' else {'display': 'none'}
    quantile_style = {'display': 'block'} if selected_type == 'quantile' else {'display': 'none'}
    return threshold_style, quantile_style

@app.callback(
    [Output('indices-spatial-plot', 'figure'),
     Output('indices-temporal-plot', 'figure')],
    [Input('indices-type-selector', 'value'),
     Input('threshold-selector', 'value'),
     Input('indices-year-range-slider', 'value'),
     Input('percentile-selector', 'value'),
     Input('extremes-plot-selector', 'value')]
)
def update_indices_analysis(selected_type, threshold, year_range, percentile, plot_type):
    if selected_type == 'threshold':
        # Threshold-based analysis
        start_date = f"{year_range[0]}-01-01"
        end_date = f"{year_range[1]}-12-31"
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        filtered_dataset = data['daily_dataset'].sel(time=slice(start_date, end_date))
        

        #pasta
        # Spatial plot
        binary_mask = xr.where(filtered_dataset['tp'] >= threshold, 1, 0)
        daily_dataset_mm = binary_mask.resample(time='YE').sum(dim=['time'])
        daily_dataset_mm = daily_dataset_mm.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)
        daily_dataset_mm_ = daily_dataset_mm.mean(dim=['time'], skipna=True)
        daily_dataset_mm_ = daily_dataset_mm_.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)
        da4 = daily_dataset_mm_
        lat4 = da4['lat'].values
        lon4 = da4['lon'].values
        z4 = da4.values
        if plot_type =='distribution':
            spatial_fig = go.Figure()
            if not (np.isnan(z4).all() or np.nansum(z4) == 0):
                spatial_fig = plot_precipitation_distribution(
                    z=z4,
                    x=lon4,
                    y=lat4,
                    colorbar='days per year',
                    hovertemplate='<b>Longitude</b>: %{x}<br><b>Latitude</b>: %{y}<br><b>Average Number of Days</b>: %{z:.2f} days<extra></extra>',
                    title=f"<b>Spatial Distribution of Precipitation Extremes ({start_date.year}–{end_date.year})</b><br>Days with Precipitation > {threshold} mm",
                    title2="Days per year"
                )
            else:
                spatial_fig.update_layout(
                    title="No data available for selected threshold",
                    xaxis_title="Longitude",
                    yaxis_title="Latitude"
                )
        else:
            spatial_trend= calculate_spatial_trend(daily_dataset_mm)
            spatial_fig= spatial_trend_plot(spatial_trend,"year")
        # Temporal plot
        df_daily_dataset_mm_latlonmean = daily_dataset_mm.mean(dim=['lat','lon'], skipna=True)
        yearly = df_daily_dataset_mm_latlonmean.to_dataframe(name='tp').reset_index()
        yearly['year'] = yearly['time'].dt.year
        yearly = yearly.groupby('year')['tp'].sum()
        values = yearly.values
        
        temporal_fig = go.Figure()
        if len(values) > 2:
            mk_result = mk.original_test(values)
            y_max = values.max()
            y_min = values.min()
            y_pad = y_max * 0.1
            
            temporal_fig = plot_precipitation_trend(
                x=yearly.index.astype(int),
                y=yearly.values,
                legend='Total Days',
                hovertemplate='<b>Year</b>: %{x}<br><b>Number of Days</b>: %{y:.0f}<extra></extra>',
                title=f"<b>Temporal Trend of Precipitation Extremes ({start_date.year}–{end_date.year})</b><br>Days with Precipitation > {threshold} mm",
                yaxis='Number of Days per Year',
                y_max=y_max,
                y_min=y_min,
                y_pad=y_pad,
                mk_result=mk_result,
                unit='days/year'
            )
        else:
            temporal_fig.update_layout(
                title="Not enough data points for trend analysis",
                xaxis_title="Year",
                yaxis_title="Number of Days"
            )
        
        return spatial_fig, temporal_fig
    
    else:  # quantile
        # Quantile-based analysis
        reference_period = data['daily_dataset'].sel(time=slice("1981-01-01", "2021-12-31"))
        ref_tp = reference_period['tp'].values.flatten()
        ref_tp = ref_tp[~np.isnan(ref_tp)]
        wet_days = ref_tp[ref_tp >= 1.0]
        scalar_threshold = np.percentile(wet_days, percentile)
        
        wet_days_mask = data['daily_dataset']['tp'] >= 1.0
        wet_days_tp = data['daily_dataset']['tp'].where(wet_days_mask, other=0)
        extreme_days_mask = wet_days_tp > scalar_threshold
        extreme_tp =data['daily_dataset']['tp'].where(extreme_days_mask, other=0)
        annual_total_extreme_prcp = extreme_tp.resample(time='YE').sum(dim='time')
        masked_prcp = annual_total_extreme_prcp.where(annual_total_extreme_prcp > 0)
        annual_mean = masked_prcp.mean(dim=['lat', 'lon'], skipna=True)
        df_annual = annual_mean.to_dataframe(name='mean_extreme_prcp').reset_index()
        df_annual['year'] = df_annual['time'].dt.year
        
        #pasta
        # Spatial plot
        annual_spatial_mean = masked_prcp.mean(dim=['time'], skipna=True)
        annual_spatial_mean = annual_spatial_mean.rio.clip(data['shp'].geometry.apply(mapping), data['shp'].crs, drop=False)
        da4 = annual_spatial_mean
        lat4 = da4['lat'].values
        lon4 = da4['lon'].values
        z4 = da4.values
        
        spatial_fig = go.Figure()
        if not (np.isnan(z4).all() or np.nansum(z4) == 0):
            spatial_fig = plot_precipitation_distribution(
                z=z4,
                x=lon4,
                y=lat4,
                colorbar='ppt',
                hovertemplate='<b>Longitude</b>: %{x}<br><b>Latitude</b>: %{y}<br><b>Total Precipitation</b>: %{z:.2f} mm<extra></extra>',
                title=f"<b>Spatial Distribution of Precipitation Extremes ({min_year}–{max_year})</b><br>Precipitation on Extreme Wet Days (≥ {percentile}th Percentile)",
                title2="Precipitation (mm)"
            )
        else:
            spatial_fig.update_layout(
                title="No data available for selected percentile",
                xaxis_title="Longitude",
                yaxis_title="Latitude"
            )
        
        # Temporal plot
        mk_result = mk.original_test(df_annual['mean_extreme_prcp'])
        y_max = df_annual['mean_extreme_prcp'].max()
        y_min = df_annual['mean_extreme_prcp'].min()
        y_pad = y_max * 0.1
        
        temporal_fig = go.Figure()
        if len(df_annual) > 2:
            temporal_fig = plot_precipitation_trend(
                x=df_annual['year'],
                y=df_annual['mean_extreme_prcp'].values,
                legend='Extreme Precipitation',
                hovertemplate='<b>Year</b>: %{x}<br><b>Extreme Mean PRCP</b>: %{y:.1f} mm<extra></extra>',
                title=f"<b>Temporal Trend of Precipitation Extremes ({min_year}–{max_year})</b><br>Precipitation on Extreme Wet Days (≥ {percentile}th Percentile)",
                yaxis='Mean Precipitation (mm)',
                y_max=y_max,
                y_min=y_min,
                y_pad=y_pad,
                mk_result=mk_result,
                unit='mm'
            )
        else:
            temporal_fig.update_layout(
                title="Not enough data points for trend analysis",
                xaxis_title="Year",
                yaxis_title="Mean Precipitation (mm)"
            )
        
        return spatial_fig, temporal_fig



# Drought Analysis Callbacks
@app.callback(
    Output('spi-spatial-plot', 'figure'),
    [Input('spi-selector', 'value'),
     Input('year-selected', 'value'),
     Input('month-selected', 'value')],
    prevent_initial_call=True
)
def update_drought_analysis(spi_type, year, month):
    try:
        # Basic input validation
        if None in [spi_type, year, month]:
            return go.Figure()
            
        spi_type = int(spi_type)
        year = int(year)
        month = int(month)
        
        # Calculate SPI
        spi_da = calculate_spi_with_ufunc(data['monthly_dataset'], spi_type)
        
        # Get target date
        target_date = pd.Timestamp(year=year, month=month, day=1).to_period('M').end_time
        
        # Select data
        try:
            spi_selected = spi_da.sel(time=str(target_date.date()))
        except KeyError:
            return go.Figure().update_layout(
                title=f"No data for {target_date.strftime('%B %Y')}"
            )

        # Clip to shapefile boundaries
        try:
            spi_clipped = spi_selected.rio.clip(
                data['shp'].geometry.apply(mapping),
                data['shp'].crs,
                drop=False,
                all_touched=True
            )
        except Exception as e:
            print(f"Clipping failed: {str(e)}")
            spi_clipped = spi_selected  # Fallback to unclipped data

        # Define WMO-standard SPI classification
        spi_classes = [
            [-float('inf'), -2.0, "Exceptional Drought"],
            [-2.0, -1.5, "Extreme Drought"],
            [-1.5, -1.0, "Severe Drought"],
            [-1.0, -0.5, "Moderate Drought"],
            [-0.5, 0.5, "Near Normal"],
            [0.5, 1.0, "Moderately Wet"],
            [1.0, 1.5, "Very Wet"],
            [1.5, 2.0, "Extremely Wet"],
            [2.0, float('inf'), "Exceptionally Wet"]
        ]

        # Create meshgrid for proper hover alignment
        lon_mesh, lat_mesh = np.meshgrid(spi_clipped.lon.values, spi_clipped.lat.values)
        
        # Prepare hover text as 2D array
        hover_text = np.empty_like(spi_clipped.values, dtype=object)
        for i in range(spi_clipped.values.shape[0]):
            for j in range(spi_clipped.values.shape[1]):
                z = spi_clipped.values[i,j]
                if np.isnan(z):
                    hover_text[i,j] = "No data"
                    continue
                    
                class_name = next((cls[2] for cls in spi_classes if cls[0] <= z < cls[1]), "N/A")
                hover_text[i,j] = (
                    f"SPI-{spi_type}: {z:.2f}<br>"
                    f"Class: {class_name}<br>"
                    f"Lat: {lat_mesh[i,j]:.2f}°<br>"
                    f"Lon: {lon_mesh[i,j]:.2f}°"
                )

        # Create figure
               # Create figure with map and table
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.1,
            specs=[[{"type": "heatmap"}], [{"type": "table"}]]
        )
        
        # Add heatmap to first row
        fig.add_trace(
            go.Heatmap(
                x=spi_clipped.lon.values,
                y=spi_clipped.lat.values,
                z=spi_clipped.values,
                colorscale=[
                    [0.00, "#730000"], [0.12, "#E60000"], 
                    [0.25, "#FFAA00"], [0.37, "#FCD37F"],
                    [0.50, "#FFFFFF"], [0.62, "#9AECFF"],
                    [0.75, "#00AFFF"], [0.87, "#0064C8"],
                    [1.00, "#0000FF"]
                ],
                zmin=-2.5,
                zmax=2.5,
                hoverinfo="text",
                text=hover_text,
                hovertemplate="%{text}<extra></extra>",
                colorbar=dict(
                    title=f'SPI-{spi_type} Scale',
                    tickvals=[-2.0, -1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5, 2.0],
                    ticktext=[
                        "Exceptional Drought", "Extreme Drought", "Severe Drought", 
                        "Moderate Drought", "Near Normal", "Moderately Wet", 
                        "Very Wet", "Extremely Wet", "Exceptionally Wet"
                    ]
                )
            ),
            row=1, col=1
        )

        # Add SPI classification table to second row
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["<b>SPI Range</b>", "<b>Classification</b>", "<b>Color</b>"],
                    font=dict(size=12, color='white'),
                    fill_color='#3498db',
                    align='center'
                ),
                cells=dict(
                    values=[
                        ["≤ -2.0", "-2.0 to -1.5", "-1.5 to -1.0", "-1.0 to -0.5", 
                         "-0.5 to 0.5", "0.5 to 1.0", "1.0 to 1.5", "1.5 to 2.0", "≥ 2.0"],
                        ["Exceptional Drought", "Extreme Drought", "Severe Drought", 
                         "Moderate Drought", "Near Normal", "Moderately Wet", 
                         "Very Wet", "Extremely Wet", "Exceptionally Wet"],
                        ["", "", "", "", "", "", "", "", ""]  # Empty for color boxes
                    ],
                    fill_color=[
                        ['#730000', '#E60000', '#FFAA00', '#FCD37F', 
                         '#FFFFFF', '#9AECFF', '#00AFFF', '#0064C8', '#0000FF']
                    ],
                    align='center',
                    height=30
                )
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"<b>Drought Conditions: SPI-{spi_type}</b><br>{target_date.strftime('%B %Y')}",
                x=0.5,
                xanchor='center',
                y=0.95
            ),
            margin=dict(l=0, r=0, t=100, b=0),
            height=800,  # Increased height to accommodate table
            showlegend=False
        )
        
        # Update table properties
        fig.update_traces(
            cells_font=dict(size=11),
            selector=dict(type='table')
        )
        
        return fig
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return go.Figure().update_layout(
            title="Error generating map",
            annotations=[dict(text=str(e), showarrow=False)]
        )

# In your main application file (app.py or similar)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)