# Route Planner A* BASE

A professional desktop route planning application built with **Python**. This tool utilizes an advanced **Traffic-Aware A* (A-Star) Algorithm** to calculate optimal driving paths on real-world road networks. It goes beyond simple distance calculation by integrating **Google Maps Real-Time Traffic** data to penalize congested routes exponentially.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-orange?style=for-the-badge)

## Overview

Unlike standard GPS tools, this Route Planner gives users granular control over their pathfinding logic. It visualizes the exact graph nodes traversed and allows for multi-stop trip planning. The application features a robust **MVC Architecture**, a modern dark-themed UI, and intelligent graph caching for high performance.

##  Key Features

###  Intelligent Pathfinding
- **Traffic-Aware A*:** The algorithm minimizes **Time**, not just distance.  
- **Exponential Congestion Penalty:** Uses a non-linear cost function to aggressively avoid heavy traffic.  
- **Heuristic Optimization:** Implements Haversine distance heuristics for rapid convergence.  

###  Modern User Interface
- **Interactive Map:** Powered by `tkintermapview` with smooth zooming and panning.  
- **Drag & Drop Waypoints:** Reorder stops instantly using a custom-built draggable listbox.  
- **Smart Search:** Google Places API autocomplete for finding addresses.  
- **Visual Debugging:**  
  - Blue path for the calculated optimal route  
  - Red dots for snapped road-network nodes  
  - Hover effects for reactive UI elements  

###  Performance
- **Graph Caching:** Automatically saves downloaded OpenStreetMap data (`.graphml`) to a local `cache/` directory.  
- **Multi-threading:** Heavy routing calculations run on background threads to keep the GUI responsive.  

##  Project Structure

```text
mid_mat/
├── main.py                  # Application Entry Point
├── config.py                # Global Configuration & API Keys
├── cache/                   # Auto-generated map data storage
└── app/
    ├── __init__.py
    ├── logic/
    │   ├── __init__.py
    │   └── routing.py       # A* Core Logic & Traffic Calculation
    └── ui/
        ├── __init__.py
        ├── main_window.py   # Main Controller & GUI Setup
        └── widgets.py       # Custom Widgets (DragDropListbox)
```

##  Installation

### Prerequisites
- Python 3.10 or higher  
- A Google Maps API Key with the following enabled:  
  - Maps SDK  
  - Places API  
  - Geocoding API  
  - Distance Matrix API  

### Clone the Repository

```bash
git clone https://github.com/your-username/smart-route-planner.git
cd smart-route-planner
```

### Install Dependencies

```bash
pip install customtkinter tkintermapview googlemaps osmnx networkx geopy Pillow requests
```

### Configure API Key

Open `config.py` and paste your API key:

```python
# config.py
GOOGLE_MAPS_API_KEY = "AIzaSy..."  # Replace with your actual key
```

##  Usage

### Launch the App

```bash
python main.py
```

### Add Waypoints
- Type a location (for example: "Hoan Kiem Lake") in the search bar  
- Select a suggestion or click Add  

### Manage Route
- Drag and drop items in the sidebar to reorder the route  
- Right-click a stop to delete it  

### Calculate
- Click "Route Generate"  
- First run downloads map data (takes a few seconds)  
- Next runs load from cache instantly  

##  Technical Deep Dive: The Cost Function

The routing engine uses A* with a custom cost function:

```
f(n) = g(n) + h(n)
```

### Real Cost g(n) — Time + Frustration

```
Cost = T_free_flow × (TrafficRatio)^2
```

- `T_free_flow`: Base travel time from OpenStreetMap speed limits  
- `TrafficRatio`: RealTime / FreeFlow  
- Squaring the ratio applies the congestion penalty and forces avoidance of jams  

### Heuristic h(n)

Haversine distance divided by maximum highway speed.  
This heuristic is admissible and guarantees the shortest-time path.

##  Contributing

Contributions are welcome.

Developed with Python, CustomTkinter, and OpenStreetMap.
