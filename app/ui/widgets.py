# app/ui/widgets.py
import tkinter as tk


class DragDropListbox(tk.Listbox):

    def __init__(self, master, on_reorder_callback=None, on_delete_callback=None, **kw):
        super().__init__(master, **kw)
        # 1. Bind Mouse Events
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_drop)
        self.bind('<Button-3>', self.show_context_menu)

        # --- NEW: Hover Events ---
        self.bind('<Motion>', self.on_mouse_move)
        self.bind('<Leave>', self.on_mouse_leave)

        self.on_reorder_callback = on_reorder_callback
        self.on_delete_callback = on_delete_callback
        self.cur_index = None

        # --- NEW: Color Config ---
        self.default_bg = kw.get("bg", "#1f2937")
        self.hover_bg = "#374151"  # Lighter gray for hover
        self.hovered_index = None

        # Right-Click Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Location", command=self.delete_selected)

    def on_click(self, event):
        self.cur_index = self.nearest(event.y)

    def on_drag(self, event):
        i = self.nearest(event.y)
        if i < self.size():
            self.selection_clear(0, tk.END)
            self.selection_set(i)

    def on_drop(self, event):
        new_index = self.nearest(event.y)
        if self.cur_index is not None and new_index != self.cur_index:
            if self.on_reorder_callback:
                self.on_reorder_callback(self.cur_index, new_index)
        self.cur_index = None

    # --- NEW: Context Menu Logic ---
    def show_context_menu(self, event):
        # 1. Select the item under the mouse automatically
        index = self.nearest(event.y)
        self.selection_clear(0, tk.END)
        self.selection_set(index)
        self.activate(index)

        # 2. Show the menu at the mouse position
        self.context_menu.post(event.x_root, event.y_root)

    def delete_selected(self):
        # Get the currently selected index
        selection = self.curselection()
        if selection and self.on_delete_callback:
            index = selection[0]
            self.on_delete_callback(index)

    def on_mouse_move(self, event):
        # 1. Find which row is under the mouse
        index = self.nearest(event.y)

        # 2. Only update if we moved to a new row
        if index != self.hovered_index:
            # Restore the previous row to normal color
            if self.hovered_index is not None and self.hovered_index < self.size():
                # Only restore if it's not the currently selected one (optional polish)
                self.itemconfigure(self.hovered_index, background=self.default_bg)

            # Highlight the new row
            if index >= 0 and index < self.size():
                self.itemconfigure(index, background=self.hover_bg)
                self.hovered_index = index

    def on_mouse_leave(self, event):
        # Restore color when mouse leaves the widget entirely
        if self.hovered_index is not None and self.hovered_index < self.size():
            self.itemconfigure(self.hovered_index, background=self.default_bg)
        self.hovered_index = None