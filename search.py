import tkinter as tk
import customtkinter as ctk


class SearchableDropdown(ctk.CTkFrame):
    def __init__(self, master, values, variable, width=150, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.values = values
        self.filtered_values = values.copy()
        self.is_listbox_visible = False

        # Create a frame to hold the dropdown elements
        self.dropdown_frame = ctk.CTkFrame(self)
        self.dropdown_frame.pack(fill="x")

        # Create an entry for searching/display with medium font
        self.entry = ctk.CTkEntry(self.dropdown_frame, width=width, font=ctk.CTkFont(size=13))
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self.filter_list)
        self.entry.bind("<FocusIn>", self.show_listbox)
        self.entry.bind("<Return>", self.select_current)

        # Create a frame to hold the listbox
        self.listbox_frame = ctk.CTkFrame(self)

        # Create a Listbox for dropdown options with medium font
        self.listbox = tk.Listbox(
            self.listbox_frame,
            height=5,
            font=('TkDefaultFont', 18),  # Medium-sized font
            selectbackground="#4a6da7",  # CustomTkinter blue color for selection
            selectforeground="white"
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Set initial value if provided
        if self.variable.get():
            self.entry.insert(0, self.variable.get())

        # Bind events to handle hiding the listbox
        self.entry.bind("<FocusOut>", self.hide_listbox_delayed)
        self.listbox.bind("<FocusOut>", self.hide_listbox_delayed)

        # Update the listbox with initial values
        self.update_listbox()

    def show_listbox(self, event=None):
        """Show the listbox dropdown"""
        if not self.is_listbox_visible:
            self.is_listbox_visible = True
            self.listbox_frame.pack(fill="x", expand=True)
            self.update_listbox()

    def hide_listbox_delayed(self, event=None):
        """Hide the listbox with a slight delay to allow for selection"""
        # Use after to add a small delay to prevent issues with selection
        self.after(100, self.hide_listbox)

    def hide_listbox(self):
        """Hide the listbox dropdown"""
        if self.is_listbox_visible:
            self.is_listbox_visible = False
            self.listbox_frame.pack_forget()

    def filter_list(self, event):
        """Filter the dropdown list based on entry text"""
        search = self.entry.get().lower()
        self.filtered_values = [val for val in self.values if search in val.lower()]
        self.update_listbox()
        # Show the listbox when filtering
        self.show_listbox()

    def update_listbox(self):
        """Update the listbox with filtered values"""
        self.listbox.delete(0, tk.END)
        for val in self.filtered_values:
            self.listbox.insert(tk.END, val)

    def on_select(self, event):
        """Handle item selection from listbox"""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            if index < len(self.filtered_values):
                value = self.filtered_values[index]
                self.variable.set(value)
                self.entry.delete(0, tk.END)
                self.entry.insert(0, value)
                self.hide_listbox()

    def select_current(self, event=None):
        """Select the currently highlighted item when Enter is pressed"""
        if self.listbox.curselection():
            self.on_select(type('Event', (), {'widget': self.listbox}))
            return "break"  # Prevent the Enter from being processed further

    def grid(self, **kwargs):
        """Override grid to match parent's behavior"""
        super().grid(**kwargs)

    def pack(self, **kwargs):
        """Override pack to match parent's behavior"""
        super().pack(**kwargs)