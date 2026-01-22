# app/ui/main_window.py
import tkinter as tk
import customtkinter as ctk
import tkintermapview
import googlemaps
import osmnx as ox
import threading
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk

# Internal module imports
from ..logic.routing import RoutingEngine
from .widgets import DragDropListbox
import config


class RouteApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(config.APP_TITLE)
        self.geometry(config.APP_GEOMETRY)

        # Initialize API and Engine
        self.gmaps = googlemaps.Client(key=config.GOOGLE_MAPS_API_KEY)
        self.engine = RoutingEngine()

        self.stops = []
        self.markers = []
        self.path_object = None
        self.dot_markers = []  # Initialize storage for red dots
        self._after_id = None

        # Track hover state for suggestion list
        self.suggestion_hover_index = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="Route Planner", font=("Arial", 22, "bold")).pack(pady=(20, 10))

        self.clear_btn = ctk.CTkButton(
            self.sidebar, text="Clear All Locations",
            fg_color="#ef4444", hover_color="#dc2626",
            corner_radius=0,
            command=self.clear_all
        )
        self.clear_btn.pack(pady=(0, 10), padx=10, fill="x")

        ctk.CTkLabel(self.sidebar, text="Locations:", anchor="w").pack(padx=10, fill="x")

        # Custom Widget
        self.stops_box = DragDropListbox(
            self.sidebar,
            on_reorder_callback=self.handle_reorder,
            on_delete_callback=self.handle_delete,
            bg="#1f2937", fg="white",
            borderwidth=0, highlightthickness=0, font=("Arial", 12),
            selectbackground="#3b82f6",
            activestyle="none"
        )
        self.stops_box.pack(pady=5, padx=10, fill="both", expand=True)

        self.route_btn = ctk.CTkButton(
            self.sidebar, text="Route Generate",
            fg_color="#22c55e", hover_color="#16a34a",
            height=40, font=("Arial", 14, "bold"),
            corner_radius=0,
            command=self.start_routing_thread
        )
        self.route_btn.pack(pady=20, padx=10, fill="x", side="bottom")

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", text_color="gray")
        self.status_label.pack(pady=(0, 10), side="bottom")

        # --- Map ---
        self.map = tkintermapview.TkinterMapView(self, corner_radius=0)
        self.map.grid(row=0, column=1, sticky="nsew")
        self.map.set_position(config.DEFAULT_LAT, config.DEFAULT_LNG)
        self.map.set_zoom(config.DEFAULT_ZOOM)

        # --- SQUARE SEARCH BAR ---
        SEARCH_BG = "#2b2b2b"

        self.search_container = ctk.CTkFrame(
            self, height=50, corner_radius=0,
            fg_color=SEARCH_BG,
            border_width=1, border_color="#555"
        )
        self.search_container.place(relx=0.5, rely=0.03, anchor="n", relwidth=0.5)

        # Search Hover Bindings
        self.search_container.bind("<Enter>", self.on_search_enter)
        self.search_container.bind("<Leave>", self.on_search_leave)

        self.search_label = ctk.CTkLabel(self.search_container, text="🔍", font=("Arial", 16))
        self.search_label.pack(side="left", padx=(15, 5))

        self.search_entry = ctk.CTkEntry(
            self.search_container,
            placeholder_text="Search Google Maps...",
            border_width=0,
            fg_color="transparent",
            font=("Arial", 14),
            height=40,
            corner_radius=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Search Entry Bindings
        self.search_entry.bind("<KeyRelease>", self.handle_typing)
        self.search_entry.bind("<Return>", lambda e: self.add_manual_stop())
        self.search_entry.bind("<Enter>", self.on_search_enter)
        self.search_entry.bind("<Leave>", self.on_search_leave)

        self.add_btn = ctk.CTkButton(
            self.search_container, text="Add", width=70, height=32,
            fg_color="#3b82f6",
            bg_color=SEARCH_BG,
            corner_radius=0,
            command=self.add_manual_stop
        )
        self.add_btn.pack(side="right", padx=(5, 10), pady=5)

        # --- SQUARE SUGGESTION DROPDOWN ---
        self.suggestion_container = ctk.CTkFrame(
            self, corner_radius=0, fg_color="#2b2b2b",
            border_width=1, border_color="#555"
        )

        self.suggestion_list = tk.Listbox(
            self.suggestion_container,
            bg="#2b2b2b", fg="white",
            borderwidth=0, highlightthickness=0,
            font=("Arial", 12), activestyle="none"
        )
        self.suggestion_list.pack(fill="both", expand=True, padx=4, pady=4)

        # Suggestion Events
        self.suggestion_list.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestion_list.bind("<Motion>", self.on_suggestion_hover)  # <--- NEW
        self.suggestion_list.bind("<Leave>", self.on_suggestion_leave)  # <--- NEW

        self.suggestion_container.place_forget()

    # --- AUTOCOMPLETE LOGIC ---
    def handle_typing(self, event):
        if self._after_id:
            self.after_cancel(self._after_id)

        val = self.search_entry.get()
        if len(val) < 3:
            self.hide_suggestions()
            return

        self._after_id = self.after(500, self.fetch_suggestions)

    def fetch_suggestions(self):
        query = self.search_entry.get()
        try:
            results = self.gmaps.places_autocomplete(query)
            self.suggestion_list.delete(0, tk.END)

            if results:
                self.suggestion_container.configure(height=40 * min(len(results), 5))
                for res in results:
                    self.suggestion_list.insert(tk.END, res['description'])

                self.suggestion_container.place(
                    relx=0.5, rely=0.095, anchor="n", relwidth=0.5
                )
                self.suggestion_container.lift()
            else:
                self.hide_suggestions()

        except Exception as e:
            print(f"Autocomplete error: {e}")

    def hide_suggestions(self):
        self.suggestion_container.place_forget()

    def on_suggestion_select(self, event):
        selection = self.suggestion_list.curselection()
        if selection:
            address = self.suggestion_list.get(selection[0])
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, address)
            self.hide_suggestions()
            self.add_manual_stop()

    def on_suggestion_hover(self, event):
        # Find which item is under the mouse
        index = self.suggestion_list.nearest(event.y)

        # Only update if the index changed
        if index != self.suggestion_hover_index:
            # 1. Reset the previous item to Dark Gray
            if self.suggestion_hover_index is not None:
                self.suggestion_list.itemconfigure(self.suggestion_hover_index, background="#2b2b2b")

            # 2. Highlight the new item (Blue)
            if index >= 0 and index < self.suggestion_list.size():
                self.suggestion_list.itemconfigure(index, background="#3b82f6")  # Blue Highlight
                self.suggestion_hover_index = index

    def on_suggestion_leave(self, event):
        # Reset any highlighted item when mouse leaves the widget
        if self.suggestion_hover_index is not None:
            self.suggestion_list.itemconfigure(self.suggestion_hover_index, background="#2b2b2b")
            self.suggestion_hover_index = None

    # --- ROUTING LOGIC ---
    def add_manual_stop(self):
        addr = self.search_entry.get()
        if not addr:
            return
        try:
            geo = self.gmaps.geocode(addr)
            if geo:
                loc = geo[0]["geometry"]["location"]

                self.stops.append({
                    "lat": loc["lat"],
                    "lng": loc["lng"],
                    "address": addr[:40]
                })

                temp_marker = self.map.set_marker(loc["lat"], loc["lng"])
                self.markers.append(temp_marker)
                self.map.set_position(loc["lat"], loc["lng"])

                self.refresh_stops_list()
                self.search_entry.delete(0, tk.END)
                self.hide_suggestions()
        except Exception as e:
            messagebox.showerror("Error", f"Geocoding failed: {e}")

    def clear_all(self):
        self.stops = []
        self.stops_box.delete(0, tk.END)
        for m in self.markers:
            m.delete()
        if self.path_object:
            self.path_object.delete()
        self.markers = []
        # Clear dots as well
        for dot in self.dot_markers:
            dot.delete()
        self.dot_markers = []

    def start_routing_thread(self):
        if len(self.stops) < 2:
            messagebox.showwarning("Warning", "Please add at least 2 stops.")
            return
        self.route_btn.configure(state="disabled", text="Calculating...")
        threading.Thread(target=self.generate_route, daemon=True).start()

    def generate_route(self):
        try:
            full_route_path = []
            on_road_stops = []

            for i in range(len(self.stops) - 1):
                self.after(0, lambda idx=i: self.route_btn.configure(
                    text=f"Calculating Leg {idx + 1}/{len(self.stops) - 1}..."
                ))

                start_coords = (self.stops[i]['lat'], self.stops[i]['lng'])
                end_coords = (self.stops[i + 1]['lat'], self.stops[i + 1]['lng'])

                # Use engine to get graph
                graph = self.engine.get_graph_for_segment(start_coords, end_coords)

                # Find the nodes on the actual road network
                orig_node = ox.distance.nearest_nodes(graph, start_coords[1], start_coords[0])
                dest_node = ox.distance.nearest_nodes(graph, end_coords[1], end_coords[0])

                snapped_start = self.engine.get_node_coords(graph, orig_node)
                on_road_stops.append(snapped_start)

                if i == len(self.stops) - 2:
                    snapped_end = self.engine.get_node_coords(graph, dest_node)
                    on_road_stops.append(snapped_end)

                segment_path = self.engine.a_star_algorithm(graph, orig_node, dest_node)

                if segment_path:
                    full_route_path.extend(segment_path)
                else:
                    raise Exception(f"Could not find path between Stop {i + 1} and Stop {i + 2}")

            if full_route_path:
                self.after(0, lambda: self.draw_path(full_route_path, on_road_stops))
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Path calculation failed."))

        except Exception as e:
            print(f"Detailed Error: {e}")
            self.after(0, lambda err=str(e): messagebox.showerror("Routing Error", err))

        finally:
            self.after(0, lambda: self.route_btn.configure(state="normal", text="Run A* Pathfinding"))

    def draw_path(self, path, on_road_stops):
        for m in self.markers:
            m.delete()
        self.markers = []

        if self.path_object:
            self.path_object.delete()
        self.path_object = self.map.set_path(path, color="#3b82f6", width=5)

        for dot in self.dot_markers:
            dot.delete()
        self.dot_markers = []

        dot_icon = self.get_red_dot_icon()

        for i, (lat, lng) in enumerate(on_road_stops):
            stop_num = str(i + 1)

            dot = self.map.set_marker(
                lat, lng,
                text=stop_num,
                text_color="black",
                font=("Arial", 15, "bold"),
                icon=dot_icon,
                icon_anchor="center"
            )
            self.dot_markers.append(dot)

        lats, lngs = zip(*path)
        self.map.fit_bounding_box((max(lats), min(lngs)), (min(lats), max(lngs)))

    def handle_reorder(self, old_index, new_index):
        item = self.stops.pop(old_index)
        self.stops.insert(new_index, item)

        marker = self.markers.pop(old_index)
        self.markers.insert(new_index, marker)

        self.refresh_stops_list()

    def refresh_stops_list(self):
        self.stops_box.delete(0, tk.END)
        for m in self.markers:
            m.delete()
        self.markers = []

        for i, stop in enumerate(self.stops):
            stop_number = str(i + 1)
            addr_text = stop.get('address', f"Stop at {stop['lat']:.4f}...")
            self.stops_box.insert(tk.END, f"{stop_number}. {addr_text}")

            new_marker = self.map.set_marker(
                stop['lat'],
                stop['lng'],
                text=stop_number,
                marker_color_circle="#ef4444",
                marker_color_outside="#991b1b"
            )
            self.markers.append(new_marker)

    def get_red_dot_icon(self):
        size = 16
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((2, 2, size - 2, size - 2), fill="#ef4444", outline="#991b1b")
        return ImageTk.PhotoImage(image)

    def handle_delete(self, index):
        self.stops.pop(index)
        marker_to_remove = self.markers.pop(index)
        marker_to_remove.delete()
        self.refresh_stops_list()

        if self.path_object:
            self.path_object.delete()
            self.path_object = None
            for dot in self.dot_markers:
                dot.delete()
            self.dot_markers = []

    def on_search_enter(self, event):
        self.search_container.configure(border_color="#3b82f6")

    def on_search_leave(self, event):
        if self.focus_get() != self.search_entry:
            self.search_container.configure(border_color="#555")
