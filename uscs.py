import tkinter as tk
import numpy as np
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import json
from pathlib import Path
import webbrowser
import time
from threading import Thread
import sys
class USCS_Classifier:
    def __init__(self, root):
        self.root = root
        self.root.title("USCS_Classifier")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)

        
        # Set modern theme with custom colors
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors and fonts
        self.primary_color = '#2c3e50'
        self.secondary_color = '#3498db'
        self.accent_color = '#e74c3c'
        self.light_bg = '#ecf0f1'
        self.dark_text = '#2c3e50'
        
        # Custom style configurations
        self.style.configure('.', background=self.light_bg, foreground=self.dark_text, 
                           font=('Segoe UI', 10))
        self.style.configure('TFrame', background=self.light_bg)
        self.style.configure('TLabel', background=self.light_bg, font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10, 'bold'), 
                           borderwidth=1, relief='raised')
        self.style.configure('TNotebook', background=self.light_bg)
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), 
                           padding=[10, 5], background=self.light_bg)
        self.style.configure('TEntry', fieldbackground='white', borderwidth=1)
        self.style.configure('TCombobox', fieldbackground='white')
        self.style.configure('TLabelframe', background=self.light_bg, 
                           font=('Segoe UI', 10, 'bold'))
        self.style.configure('TLabelframe.Label', background=self.light_bg)
        
        # Map styles for button states
        self.style.map('TButton', 
                     foreground=[('pressed', 'white'), ('active', 'white')],
                     background=[('pressed', self.accent_color), 
                                ('active', self.secondary_color),
                                ('!disabled', self.primary_color)])
        
        # Configure notebook tab colors
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.light_bg), ('!selected', '#bdc3c7')],
                      foreground=[('selected', self.primary_color), ('!selected', '#7f8c8d')])
        
        # Initialize variables first
        self.initialize_variables()
        self.examples = self.load_example_data()
        
        # Create notebook for multiple tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_input_tab()
        self.create_results_tab()
        self.create_help_tab()
        # In your __init__ method after setting the title
        self.root.config(bg=self.primary_color)  # Match title bar color to theme
        # Configure frame styles with subtle borders
        self.style.configure('TFrame', background=self.light_bg, borderwidth=1, relief='groove')
        # Load example data
        self.examples = self.load_example_data()
        # In __init__:
        self.root.bind('<Control-s>', lambda e: self.save_data())
        self.root.bind('<Control-l>', lambda e: self.load_data())
        self.root.bind('<Control-c>', lambda e: self.classify_soil())
        
        # Add status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        self.status_var.set("Ready")

    def initialize_variables(self):
        # Sieve analysis variables
        self.boulders = tk.DoubleVar(value=0.0)
        self.cobbles = tk.DoubleVar(value=0.0)
        self.gravel = tk.DoubleVar(value=0.0)
        self.sand = tk.DoubleVar(value=0.0)
        self.fines = tk.DoubleVar(value=0.0)
        
        # Atterberg limits
        self.ll = tk.DoubleVar(value=0.0)
        self.pl = tk.DoubleVar(value=0.0)
        self.pi = tk.DoubleVar(value=0.0)
        
        # Grain size distribution - D values
        self.d10 = tk.DoubleVar(value=0.0)
        self.d30 = tk.DoubleVar(value=0.0)
        self.d60 = tk.DoubleVar(value=0.0)
        
        # Coefficients
        self.cu = tk.DoubleVar(value=0.0)
        self.cc = tk.DoubleVar(value=0.0)
        
        # Input mode (D values or coefficients)
        self.input_mode = tk.StringVar(value="D_values")
        
        # Organic content check
        self.air_dry_ll = tk.DoubleVar(value=0.0)
        self.oven_dry_ll = tk.DoubleVar(value=0.0)
        
        # Results
        self.classification_result = tk.StringVar(value="")
        self.description_result = tk.StringVar(value="")
        self.cu_result = tk.StringVar(value="")
        self.cc_result = tk.StringVar(value="")
        self.p200_result = tk.StringVar(value="")
        self.detailed_description = tk.StringVar(value="")
        
    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_withdraw()
        
        label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", 
                         borderwidth=1, padding=5, wraplength=300, 
                         font=('Segoe UI', 9))
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty()
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.wm_deiconify()
            
        def leave(event):
            tooltip.wm_withdraw()
            
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        
        return tooltip

    def create_input_tab(self):
        # Input tab
        self.input_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.input_tab, text="Input Data")
        
        # Create frames for organization
        main_frame = ttk.Frame(self.input_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame,padding=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        right_frame = ttk.Frame(main_frame, padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Sieve Analysis Frame
        sieve_frame = ttk.LabelFrame(left_frame, text="Sieve Analysis (% Retained)", padding=10)
        sieve_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Sieve analysis inputs with tooltips
        boulders_label = ttk.Label(sieve_frame, text="Boulders (>300 mm):")
        boulders_label.grid(row=0, column=0, sticky="w", pady=2)
        boulders_entry = ttk.Entry(sieve_frame, textvariable=self.boulders)
        boulders_entry.grid(row=0, column=1, pady=2, padx=5)
        self.create_tooltip(boulders_label, "Percentage of soil particles larger than 300mm")
        
        cobbles_label = ttk.Label(sieve_frame, text="Cobbles (75-300 mm):")
        cobbles_label.grid(row=1, column=0, sticky="w", pady=2)
        cobbles_entry = ttk.Entry(sieve_frame, textvariable=self.cobbles)
        cobbles_entry.grid(row=1, column=1, pady=2, padx=5)
        self.create_tooltip(cobbles_label, "Percentage of soil particles between 75-300mm")
        
        gravel_label = ttk.Label(sieve_frame, text="Gravel (4.75-75 mm):")
        gravel_label.grid(row=2, column=0, sticky="w", pady=2)
        gravel_entry = ttk.Entry(sieve_frame, textvariable=self.gravel)
        gravel_entry.grid(row=2, column=1, pady=2, padx=5)
        self.create_tooltip(gravel_label, "Percentage of soil particles between 4.75-75mm")
        
        sand_label = ttk.Label(sieve_frame, text="Sand (0.075-4.75 mm):")
        sand_label.grid(row=3, column=0, sticky="w", pady=2)
        sand_entry = ttk.Entry(sieve_frame, textvariable=self.sand)
        sand_entry.grid(row=3, column=1, pady=2, padx=5)
        self.create_tooltip(sand_label, "Percentage of soil particles between 0.075-4.75mm")
        
        fines_label = ttk.Label(sieve_frame, text="Fines (<0.075 mm):")
        fines_label.grid(row=4, column=0, sticky="w", pady=2)
        fines_entry = ttk.Entry(sieve_frame, textvariable=self.fines)
        fines_entry.grid(row=4, column=1, pady=2, padx=5)
        self.create_tooltip(fines_label, "Percentage of soil particles smaller than 0.075mm (silt/clay)")
        
        # Add a separator
        ttk.Separator(sieve_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Total percentage label
        self.total_percent = tk.StringVar(value="Total: 0.0%")
        total_label = ttk.Label(sieve_frame, textvariable=self.total_percent, 
                              font=('Segoe UI', 9, 'bold'))
        total_label.grid(row=6, column=0, columnspan=2)
        
        # Bind the entries to update the total
        for var in [self.boulders, self.cobbles, self.gravel, self.sand, self.fines]:
            var.trace_add('write', self.update_total_percentage)
        
        # Atterberg Limits Frame
        atterberg_frame = ttk.LabelFrame(left_frame, text="Atterberg Limits", padding=10)
        atterberg_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        ll_label = ttk.Label(atterberg_frame, text="Liquid Limit (LL):")
        ll_label.grid(row=0, column=0, sticky="w", pady=2)
        ll_entry = ttk.Entry(atterberg_frame, textvariable=self.ll)
        ll_entry.grid(row=0, column=1, pady=2, padx=5)
        self.create_tooltip(ll_label, "Water content where soil changes from plastic to liquid state")
        
        pl_label = ttk.Label(atterberg_frame, text="Plastic Limit (PL):")
        pl_label.grid(row=1, column=0, sticky="w", pady=2)
        pl_entry = ttk.Entry(atterberg_frame, textvariable=self.pl)
        pl_entry.grid(row=1, column=1, pady=2, padx=5)
        self.create_tooltip(pl_label, "Water content where soil changes from semisolid to plastic state")
        
        pi_label = ttk.Label(atterberg_frame, text="Plasticity Index (PI):")
        pi_label.grid(row=2, column=0, sticky="w", pady=2)
        pi_entry = ttk.Entry(atterberg_frame, textvariable=self.pi, state='readonly')
        pi_entry.grid(row=2, column=1, pady=2, padx=5)
        self.create_tooltip(pi_label, "PI = LL - PL (difference between liquid and plastic limits)")
        
        # Grain Size Distribution Frame
        gsd_frame = ttk.LabelFrame(right_frame, text="Grain Size Characteristics", padding=10)
        gsd_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        mode_frame = ttk.Frame(gsd_frame)
        mode_frame.pack(fill='x', pady=5)
        
        ttk.Radiobutton(mode_frame, text="Enter D values", variable=self.input_mode, 
                       value="D_values", command=self.toggle_input_mode).pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Enter Coefficients", variable=self.input_mode, 
                       value="coefficients", command=self.toggle_input_mode).pack(side="left", padx=5)
        
        # D values frame
        self.d_values_frame = ttk.Frame(gsd_frame)
        self.d_values_frame.pack(fill='x', pady=5)
        
        d10_label = ttk.Label(self.d_values_frame, text="D₁₀ (mm):")
        d10_label.grid(row=0, column=0, sticky="w", pady=2)
        d10_entry = ttk.Entry(self.d_values_frame, textvariable=self.d10)
        d10_entry.grid(row=0, column=1, pady=2, padx=5)
        self.create_tooltip(d10_label, "Particle diameter where 10% of soil is finer (effective size)")
        
        d30_label = ttk.Label(self.d_values_frame, text="D₃₀ (mm):")
        d30_label.grid(row=1, column=0, sticky="w", pady=2)
        d30_entry = ttk.Entry(self.d_values_frame, textvariable=self.d30)
        d30_entry.grid(row=1, column=1, pady=2, padx=5)
        self.create_tooltip(d30_label, "Particle diameter where 30% of soil is finer")
        
        d60_label = ttk.Label(self.d_values_frame, text="D₆₀ (mm):")
        d60_label.grid(row=2, column=0, sticky="w", pady=2)
        d60_entry = ttk.Entry(self.d_values_frame, textvariable=self.d60)
        d60_entry.grid(row=2, column=1, pady=2, padx=5)
        self.create_tooltip(d60_label, "Particle diameter where 60% of soil is finer")
        
        # Coefficients frame (initially hidden)
        self.coeff_frame = ttk.Frame(gsd_frame)
        
        cu_label = ttk.Label(self.coeff_frame, text="Coefficient of Uniformity (Cᵤ):")
        cu_label.grid(row=0, column=0, sticky="w", pady=2)
        cu_entry = ttk.Entry(self.coeff_frame, textvariable=self.cu)
        cu_entry.grid(row=0, column=1, pady=2, padx=5)
        self.create_tooltip(cu_label, "Cᵤ = D₆₀/D₁₀ (measure of particle size range)")
        
        cc_label = ttk.Label(self.coeff_frame, text="Coefficient of Curvature (C꜀):")
        cc_label.grid(row=1, column=0, sticky="w", pady=2)
        cc_entry = ttk.Entry(self.coeff_frame, textvariable=self.cc)
        cc_entry.grid(row=1, column=1, pady=2, padx=5)
        self.create_tooltip(cc_label, "C꜀ = (D₃₀)²/(D₁₀ × D₆₀) (measure of gradation curve shape)")
        
        # Buttons for calculating coefficients
        self.calc_button_frame = ttk.Frame(gsd_frame)
        self.calc_button_frame.pack(fill='x', pady=5)
        
        ttk.Button(self.calc_button_frame, text="Calculate Coefficients", 
                  command=self.calculate_coefficients, style='Accent.TButton').pack(side="left", padx=5)
        
        # Organic Content Frame
        organic_frame = ttk.LabelFrame(right_frame, text="Organic Content Check", padding=10)
        organic_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        air_dry_label = ttk.Label(organic_frame, text="Air-dried LL:")
        air_dry_label.grid(row=0, column=0, sticky="w", pady=2)
        air_dry_entry = ttk.Entry(organic_frame, textvariable=self.air_dry_ll)
        air_dry_entry.grid(row=0, column=1, pady=2, padx=5)
        self.create_tooltip(air_dry_label, "Liquid limit of air-dried soil sample")
        
        oven_dry_label = ttk.Label(organic_frame, text="Oven-dried LL:")
        oven_dry_label.grid(row=1, column=0, sticky="w", pady=2)
        oven_dry_entry = ttk.Entry(organic_frame, textvariable=self.oven_dry_ll)
        oven_dry_entry.grid(row=1, column=1, pady=2, padx=5)
        self.create_tooltip(oven_dry_label, "Liquid limit of oven-dried soil sample (105°C for 24 hours)")
        
        # Button Frame
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Calculate PI", command=self.calculate_pi, 
                  style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Classify Soil", command=self.classify_soil, 
                  style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all, style='Accent.TButton').pack(side="left", padx=5)
        
        # Example data button
        example_btn = ttk.Button(button_frame, text="Load Example", command=self.load_example , style='Accent.TButton')
        example_btn.pack(side="right", padx=5)
        self.create_tooltip(example_btn, "Load example soil data for testing")
        
        # Save/Load buttons
        save_load_frame = ttk.Frame(right_frame, style='Accent.TButton')
        save_load_frame.pack(fill='x', pady=5)
        
        ttk.Button(save_load_frame, text="Save Data", command=self.save_data , style='Accent.TButton').pack(side="left", padx=5)
        ttk.Button(save_load_frame, text="Load Data", command=self.load_data, style='Accent.TButton').pack(side="left", padx=5)
        
        # Create a custom style for accent buttons
        self.style.configure('Accent.TButton', background=self.secondary_color, 
                           foreground='white')
        self.style.map('Accent.TButton', 
                      background=[('pressed', self.accent_color), 
                                 ('active', self.primary_color)])
        
        # Initialize input mode
        self.toggle_input_mode()
    
    def update_total_percentage(self, *args):
        """Update the total percentage display"""
        try:
            total = (self.boulders.get() + self.cobbles.get() + self.gravel.get() + 
                    self.sand.get() + self.fines.get())
            self.total_percent.set(f"Total: {total:.1f}%")
            
            # Change color if not 100%
            if abs(total - 100) > 0.1:
                self.total_percent.set(f"Total: {total:.1f}% (should be 100%)")
        except:
            self.total_percent.set("Total: N/A")
    
    def create_results_tab(self):
        # Results tab
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Results")
        
        # Main results frame
        main_frame = ttk.Frame(self.results_tab)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left frame for text results
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Right frame for chart
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Results display
        results_frame = ttk.LabelFrame(left_frame, text="Classification Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure grid for better alignment
        results_frame.columnconfigure(1, weight=1)
        
        # Create a bold font for labels
        bold_font = ('Segoe UI', 10, 'bold')
        
        ttk.Label(results_frame, text="USCS Symbol:", font=bold_font).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(results_frame, textvariable=self.classification_result, 
                 font=('Segoe UI', 14, 'bold'), foreground=self.primary_color).grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(results_frame, text="Description:", font=bold_font).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(results_frame, textvariable=self.description_result, 
                 wraplength=400, justify="left").grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(results_frame, text="Detailed Description:", font=bold_font).grid(row=2, column=0, sticky="nw", pady=5)
        ttk.Label(results_frame, textvariable=self.detailed_description, 
                 wraplength=400, justify="left").grid(row=2, column=1, sticky="w", pady=5)
        
        # Add separator
        ttk.Separator(results_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)
        
        ttk.Label(results_frame, text="Coefficient of Uniformity (Cᵤ):", font=bold_font).grid(row=4, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, textvariable=self.cu_result).grid(row=4, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="Coefficient of Curvature (C꜀):", font=bold_font).grid(row=5, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, textvariable=self.cc_result).grid(row=5, column=1, sticky="w", pady=2)
        
        ttk.Label(results_frame, text="% Passing No. 200 Sieve:", font=bold_font).grid(row=6, column=0, sticky="w", pady=2)
        ttk.Label(results_frame, textvariable=self.p200_result).grid(row=6, column=1, sticky="w", pady=2)
        
        # Export button
        export_btn = ttk.Button(left_frame, text="Export Results", command=self.export_results,
                               style='Accent.TButton')
        export_btn.pack(pady=10)
        
        # Plasticity chart
        chart_frame = ttk.LabelFrame(right_frame, text="Plasticity Chart", padding=10)
        chart_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.patch.set_facecolor(self.light_bg)
        self.ax.set_facecolor(self.light_bg)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add navigation toolbar with custom style
        toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        toolbar.update()
        self.canvas._tkcanvas.pack(fill='both', expand=True)
        # In your results display code:
        result_label = ttk.Label(results_frame, textvariable=self.classification_result, 
                                font=('Segoe UI', 14, 'bold'))
        if "GW" in self.classification_result.get():
            result_label.config(foreground='green')
        elif "CH" in self.classification_result.get():
            result_label.config(foreground='red')
        else:
            result_label.config(foreground=self.primary_color)
        # Add export button to toolbar          
        # Style the toolbar
        for child in toolbar.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(style='TButton')
        
        self.draw_blank_plasticity_chart()
    
    def draw_blank_plasticity_chart(self):
        """Draw the USCS plasticity chart with A-line, U-line, and shaded regions."""
        self.ax.clear()

        # Set background color and style
        self.ax.set_facecolor('#f9f9f9') # Light gray background
        self.ax.grid(True, linestyle='--', alpha=0.7, color='lightgray') # Subtle grid

        # --- Define constants and line functions ---
        pi_max = 60
        ll_max = 100 # Chart limit, image goes to 120, but 100 is common
        
        # A-line: Horizontally PI=4 till LL=25.5, then PI = 0.73 * (LL - 20)
        def a_line_func(ll_values):
            # Ensure that PI doesn't go below 0
            return np.maximum(0, np.where(ll_values <= 25.5, 4.0, 0.73 * (ll_values - 20.0)))

        # U-line: PI = 0.9 * (LL - 8)
        def u_line_func(ll_values):
            # Ensure that PI doesn't go below 0
            return np.maximum(7, 0.9 * (ll_values - 8.0))

        # --- Plot A-line ---
        ll_a_plot = np.linspace(0, ll_max, 200) # Use a single linspace for the whole A-line
        pi_a_plot = a_line_func(ll_a_plot)
        self.ax.plot(ll_a_plot, pi_a_plot, 'k-', linewidth=2, label="A-line")

        # --- Plot U-line ---
        ll_u_plot = np.linspace(8, ll_max, 200) # U-line starts at LL=8
        pi_u_plot = u_line_func(ll_u_plot)
        pi_u_plot_clipped = np.minimum(pi_u_plot, pi_max) # Clip to chart top
        self.ax.plot(ll_u_plot, pi_u_plot_clipped, color='dimgray', linestyle='--', linewidth=1.5, label="U-line")

        # --- Plot reference lines ---
        self.ax.axvline(x=50, color='darkgray', linestyle='-.', linewidth=1, label="LL=50")
        self.ax.axhline(y=4, color='silver', linestyle=':', linewidth=0.8) # No label needed for minor lines
        self.ax.axhline(y=7, color='silver', linestyle=':', linewidth=0.8) # No label needed for minor lines

        # --- Define colors for regions ---
        color_ch = '#FF6347'  # Tomato (for CH or OH)
        color_mh = '#FFD700'  # Gold (for MH or OH)
        color_clml = '#DDA0DD' # Plum (for CL-ML) - Hatched
        color_cl = '#90EE90'  # Light Green (for CL or OL)
        color_ml = '#ADD8E6'  # Light Blue (for ML or OL)

        # --- Shaded Regions (Order of plotting can matter for overlaps) ---
        # CH or OH: LL >= 50, Above A-line, Below U-line
        ll_ch_fill = np.linspace(50, ll_max, 100)
        pi_ch_lower = a_line_func(ll_ch_fill)
        pi_ch_upper = np.minimum(pi_max, u_line_func(ll_ch_fill))
        self.ax.fill_between(ll_ch_fill, pi_ch_lower, pi_ch_upper, 
                            where=(pi_ch_lower <= pi_ch_upper), # Condition to ensure lower <= upper
                            color=color_ch, alpha=0.6, interpolate=True, label="CH or OH")

        # MH or OH: LL >= 50, Below A-line
        ll_mh_fill = np.linspace(50, ll_max, 100)
        pi_mh_upper = a_line_func(ll_mh_fill)
        self.ax.fill_between(ll_mh_fill, 0, pi_mh_upper, 
                                color=color_mh, alpha=0.6, interpolate=True, label="MH or OH")
        
        # CL-ML (Hatched Zone): Approx. LL from 7.5 to 25.5, PI from 4 to 7
        clml_ll_pts = [10, 25.479452, 29.589, 10, 10]
        clml_pi_pts = [4, 4, 7, 7, 4]
        self.ax.fill(clml_ll_pts, clml_pi_pts, color=color_clml, alpha=0.7, hatch='///', edgecolor='gray', zorder=2, label="CL-ML")

        # CL or OL: LL < 50, above A-line and above CL-ML zone
        ll_cl_region = np.linspace(0, ll_max, 200) # Use a wider range for evaluation
        
        # Define lower boundary for CL region (it's either A-line or PI=7, depending on LL)
        conditions_cl_lower = [ll_cl_region < 7.5, (ll_cl_region >= 7.5) & (ll_cl_region <= 25.5)]
        choices_cl_lower = [a_line_func(ll_cl_region), 7.0]
        pi_cl_lower = np.select(conditions_cl_lower, choices_cl_lower, default=a_line_func(ll_cl_region))
        
        pi_cl_upper = u_line_func(ll_cl_region)
        pi_cl_upper_clipped = np.minimum(pi_max, pi_cl_upper) # Clip to chart top
        
        self.ax.fill_between(ll_cl_region, pi_cl_lower, pi_cl_upper_clipped, 
                            where=(pi_cl_lower <= pi_cl_upper_clipped) & (ll_cl_region < 50), # Explicitly limit to LL < 50 for filling
                            color=color_cl, alpha=0.6, interpolate=True, zorder=1, label="CL or OL")

        # ML or OL: LL < 50, below A-line and below CL-ML zone
        ll_ml_region = np.linspace(0, ll_max, 200) # Use a wider range for evaluation
        
        # Define upper boundary for ML region (it's either A-line or PI=4, depending on LL)
        conditions_ml_upper = [ll_ml_region < 7.5, (ll_ml_region >= 7.5) & (ll_ml_region <= 25.5)]
        choices_ml_upper = [a_line_func(ll_ml_region), 4.0]
        pi_ml_upper = np.select(conditions_ml_upper, choices_ml_upper, default=a_line_func(ll_ml_region))

        self.ax.fill_between(ll_ml_region, 0, pi_ml_upper, 
                                where=(ll_ml_region < 50), # Explicitly limit to LL < 50 for filling
                                color=color_ml, alpha=0.6, interpolate=True, zorder=1, label="ML or OL")


        # --- Labels, title, and limits ---
        self.ax.set_xlabel("Liquid Limit (LL)", fontsize=11, fontweight='bold')
        self.ax.set_ylabel("Plasticity Index (PI)", fontsize=11, fontweight='bold')
        self.ax.set_title("USCS Plasticity Chart (ASTM D2487)", fontsize=12, fontweight='bold', pad=15)
        self.ax.set_xlim(0, ll_max)
        self.ax.set_ylim(0, pi_max)

        # --- Add text labels for soil types ---
        # Moved fontsize out of bbox_props
        label_props = dict(facecolor='white', alpha=0.75, edgecolor='lightgray', boxstyle='round,pad=0.3') # Removed fontsize
        
        self.ax.text(15, 5.5, "CL-ML", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(15, 2, "ML or OL", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(38, 2.5, "ML or OL", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(38, 20, "CL or OL", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(38, 20, "CL or OL", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(75, 15, "MH or OH", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)
        self.ax.text(75, 53, "CH or OH", ha='center', va='center', bbox=label_props, fontsize=9, zorder=3)

        # --- Legend ---
        # Get handles and labels from all plotted elements
        handles, labels = self.ax.get_legend_handles_labels()
        
        # Filter out duplicate labels for a cleaner legend
        unique_handles = {}
        for handle, label in zip(handles, labels):
            # For fill_between, handle is a list of polygons. Use the first one.
            # For lines, handle is a Line2D object.
            if isinstance(handle, list):
                handle = handle[0]
            if label not in unique_handles:
                unique_handles[label] = handle
        
        self.ax.legend(unique_handles.values(), unique_handles.keys(), fontsize=8, framealpha=0.9, facecolor='white', loc='lower right')

        # Robust check for canvas existence and validity before drawing
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.draw()
        else:
            # This indicates a setup problem where canvas is not available.
            # This print is for debugging purposes; you might remove it in a final version.
            print("Error: self.canvas is not initialized or is None. Chart cannot be drawn.")
    def update_plasticity_chart(self, ll, pi, classification):
        """Update plasticity chart with the current soil point"""
        self.draw_blank_plasticity_chart()
        
        # Plot the point with better styling
        self.ax.plot(ll, pi, 'o', markersize=10, color=self.accent_color, 
                    markeredgecolor='white', markeredgewidth=1.5, label="Current Soil")
        
        # Add classification text with arrow
        self.ax.annotate(classification, xy=(ll, pi), xytext=(ll + 5, pi + 5),
                        arrowprops=dict(facecolor='black', shrink=0.05),
                        bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))
        
        # Add connecting lines to axes
        self.ax.plot([ll, ll], [0, pi], '--', color=self.accent_color, alpha=0.5, linewidth=1)
        self.ax.plot([0, ll], [pi, pi], '--', color=self.accent_color, alpha=0.5, linewidth=1)
        
        # Add axis labels for the point
        self.ax.text(ll, -2, f"{ll:.1f}", ha='center', va='top', color=self.accent_color)
        self.ax.text(-5, pi, f"{pi:.1f}", ha='right', va='center', color=self.accent_color)
        
        self.ax.legend(loc='upper right')
        self.canvas.draw()

    def create_help_tab(self):
        # Help tab
        self.help_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.help_tab, text="Help")
        
        # Create notebook for help sections
        help_notebook = ttk.Notebook(self.help_tab)
        help_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Instructions tab
        instructions_tab = ttk.Frame(help_notebook)
        help_notebook.add(instructions_tab, text="Instructions")
        
        help_text = """
        USCS Soil Classifier Help
        
        1. Sieve Analysis:
           - Enter percentages retained on each sieve
           - Values should add up to 100%
           - Negative values are not allowed
           - Values >100% are not allowed
        
        2. Atterberg Limits:
           - Enter Liquid Limit (LL) and Plastic Limit (PL)
           - Click "Calculate PI" to compute Plasticity Index
           - Typical ranges: LL (20-100), PL (10-50)
        
        3. Grain Size Distribution:
           - Enter D₁₀, D₃₀, and D₆₀ values in mm
           - Or directly enter Cᵤ and C꜀ coefficients
           - Required for coarse-grained soil classification
        
        4. Organic Content Check:
           - Optional for organic soils
           - Compare air-dried vs oven-dried LL values
           - If oven-dried LL / air-dried LL < 0.75, soil is organic
        
        5. Click "Classify Soil" to get USCS classification
        
        Key Definitions:
        - Cᵤ = D₆₀/D₁₀ (Coefficient of Uniformity)
        - C꜀ = (D₃₀)²/(D₁₀ × D₆₀) (Coefficient of Curvature)
        - Well-graded soils: Cᵤ ≥ 4 (gravel) or 6 (sand) AND 1 ≤ C꜀ ≤ 3
        """
        
        ttk.Label(instructions_tab, text=help_text, justify="left", padding=10).pack(fill='both', expand=True)
        
        # Examples tab
        examples_tab = ttk.Frame(help_notebook)
        help_notebook.add(examples_tab, text="Examples")
        
        example_text = """
        Common Soil Types and Their Properties:
        
        1. Well-graded Gravel (GW):
           - Gravel: 60%, Sand: 30%, Fines: 10%
           - D₁₀: 0.5mm, D₃₀: 5mm, D₆₀: 20mm
           - Cᵤ ≈ 40, C꜀ ≈ 2.5
        
        2. Poorly-graded Sand (SP):
           - Gravel: 10%, Sand: 85%, Fines: 5%
           - D₁₀: 0.1mm, D₃₀: 0.2mm, D₆₀: 0.5mm
           - Cᵤ ≈ 5, C꜀ ≈ 0.8
        
        3. Clay with High Plasticity (CH):
           - Gravel: 5%, Sand: 10%, Fines: 85%
           - LL: 65, PL: 25, PI: 40
        
        4. Silty Sand (SM):
           - Gravel: 5%, Sand: 60%, Fines: 35%
           - LL: 32, PL: 25, PI: 7
           - D₁₀: 0.08mm, D₃₀: 0.2mm, D₆₀: 1.0mm
        
        Use the "Load Example" button to try these examples.
        """
        
        ttk.Label(examples_tab, text=example_text, justify="left", padding=10).pack(fill='both', expand=True)
        
        # References tab
        references_tab = ttk.Frame(help_notebook)
        help_notebook.add(references_tab, text="References")
        
        ref_text = """
        References and Standards:
        
        1. ASTM D2487 - Standard Practice for Classification of Soils for Engineering Purposes (USCS)
        2. ASTM D2488 - Standard Practice for Description and Identification of Soils (Visual-Manual Procedure)
        3. ASTM D4318 - Standard Test Methods for Liquid Limit, Plastic Limit, and Plasticity Index of Soils
        
        For more information:
        - Visit the ASTM website: www.astm.org
        - Consult geotechnical engineering textbooks
        """
        
        ttk.Label(references_tab, text=ref_text, justify="left", padding=10).pack(fill='both', expand=True)
        
        def open_astm(event):
            webbrowser.open_new("https://www.astm.org")
            
        astm_link = ttk.Label(references_tab, text="www.astm.org", foreground="blue", cursor="hand2")
        astm_link.pack()
        astm_link.bind("<Button-1>", open_astm)
    
    def validate_percentage(self, value, var_name):
        """Validate that a percentage value is between 0 and 100"""
        try:
            num = float(value)
            if num < 0:
                messagebox.showerror("Invalid Input", f"{var_name} cannot be negative")
                return False
            if num > 100:
                messagebox.showerror("Invalid Input", f"{var_name} cannot exceed 100%")
                return False
            return True
        except ValueError:
            messagebox.showerror("Invalid Input", f"{var_name} must be a number")
            return False
    
    def calculate_pi(self):
        """Calculate Plasticity Index from LL and PL"""
        try:
            ll = self.ll.get()
            pl = self.pl.get()
            
            if ll < pl:
                messagebox.showerror("Error", "Liquid Limit cannot be less than Plastic Limit")
                return
                
            pi = ll - pl
            self.pi.set(round(pi, 1))
        except ValueError:
            messagebox.showerror("Error", "Please enter valid LL and PL values")
    
    def calculate_coefficients(self):
        """Calculate Cu and Cc from D values"""
        try:
            d10 = self.d10.get()
            d30 = self.d30.get()
            d60 = self.d60.get()
            
            if d10 <= 0:
                raise ValueError("D10 must be greater than zero")
            if d30 <= 0:
                raise ValueError("D30 must be greater than zero")
            if d60 <= 0:
                raise ValueError("D60 must be greater than zero")
            if d60 < d30 or d30 < d10:
                raise ValueError("D values must be in order: D60 ≥ D30 ≥ D10")
            
            cu = d60 / d10
            cc = (d30 ** 2) / (d10 * d60)
            
            self.cu.set(round(cu, 2))
            self.cc.set(round(cc, 2))
            
            # Switch to coefficients view to show results
            self.input_mode.set("coefficients")
            self.toggle_input_mode()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def calculate_pi(self):
        """Calculate Plasticity Index from LL and PL"""
        try:
            ll = self.ll.get()
            pl = self.pl.get()
            
            if ll < pl:
                messagebox.showerror("Error", "Liquid Limit cannot be less than Plastic Limit")
                return
                
            pi = ll - pl
            self.pi.set(round(pi, 1))
        except ValueError:
            messagebox.showerror("Error", "Please enter valid LL and PL values")
    
    def calculate_coefficients(self):
        """Calculate Cu and Cc from D values"""
        try:
            d10 = self.d10.get()
            d30 = self.d30.get()
            d60 = self.d60.get()
            
            if d10 <= 0:
                raise ValueError("D10 must be greater than zero")
            if d30 <= 0:
                raise ValueError("D30 must be greater than zero")
            if d60 <= 0:
                raise ValueError("D60 must be greater than zero")
            if d60 < d30 or d30 < d10:
                raise ValueError("D values must be in order: D60 ≥ D30 ≥ D10")
            
            cu = d60 / d10
            cc = (d30 ** 2) / (d10 * d60)
            
            self.cu.set(round(cu, 2))
            self.cc.set(round(cc, 2))
            
            # Switch to coefficients view to show results
            self.input_mode.set("coefficients")
            self.toggle_input_mode()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    def export_results(self):
        """Export classification results to a text file."""
        result_text = (
            f"USCS Symbol: {self.classification_result.get()}\n"
            f"Description: {self.description_result.get()}\n"
            f"Detailed Description: {self.detailed_description.get()}\n"
            f"Coefficient of Uniformity (Cu): {self.cu_result.get()}\n"
            f"Coefficient of Curvature (Cc): {self.cc_result.get()}\n"
            f"% Passing No. 200 Sieve: {self.p200_result.get()}"
        )

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Results"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as file:
                    file.write(result_text)
                messagebox.showinfo("Export Successful", "Results exported successfully.")
            except Exception as e:
                messagebox.showerror("Export Failed", f"An error occurred: {str(e)}")

        
    def classify_soil(self):
        try:
            # Validate sieve analysis percentages
            sieve_values = [
                ("Boulders", self.boulders.get()),
                ("Cobbles", self.cobbles.get()),
                ("Gravel", self.gravel.get()),
                ("Sand", self.sand.get()),
                ("Fines", self.fines.get())
            ]
            
            for name, value in sieve_values:
                if not self.validate_percentage(value, name):
                    return
            
            total = sum(val for _, val in sieve_values)
            if abs(total - 100) > 0.1:
                messagebox.showwarning("Warning", f"Percentages sum to {total:.1f}% (should be 100%)")
                return
                
            p200 = self.fines.get()
            gravel_pct = self.gravel.get()
            sand_pct = self.sand.get()
            
            # Validate Atterberg limits
            ll = self.ll.get()
            pl = self.pl.get()
            
            if ll < 0 or pl < 0:
                messagebox.showerror("Error", "LL and PL cannot be negative")
                return
                
            if ll > 150 or pl > 100:
                if not messagebox.askyesno("Warning", "Unusually high LL/PL values detected. Continue?"):
                    return
            
            pi_val = self.pi.get()
            # If PI is 0, recalc as ll - pl
            pi = pi_val if pi_val != 0 else ll - pl
            
            # Validate grain size data
            if self.input_mode.get() == "D_values":
                d10 = self.d10.get()
                d30 = self.d30.get()
                d60 = self.d60.get()
                
                if d10 < 0 or d30 < 0 or d60 < 0:
                    messagebox.showerror("Error", "D values cannot be negative")
                    return
                    
                if d10 > d30 or d30 > d60:
                    messagebox.showerror("Error", "D values must be in order: D10 ≤ D30 ≤ D60")
                    return
                    
                # Calculate coefficients
                cu = d60 / d10 if d10 != 0 else 0
                cc = (d30 ** 2) / (d10 * d60) if (d10 != 0 and d60 != 0) else 0
            else:
                cu = self.cu.get()
                cc = self.cc.get()
                
                if cu < 0 or cc < 0:
                    messagebox.showerror("Error", "Coefficients cannot be negative")
                    return
            
            # Check organic content
            organic = False
            air_dry = self.air_dry_ll.get()
            oven_dry = self.oven_dry_ll.get()
            
            if air_dry > 0 and oven_dry > 0:
                if air_dry < oven_dry:
                    messagebox.showwarning("Warning", "Oven-dried LL should be less than air-dried LL")
                ratio = oven_dry / air_dry
                organic = ratio < 0.75
            
            # Classify soil
            if p200 >= 50:  # Fine-grained soil
                classification, description, detailed = self.classify_fine_grained(
                    ll, pi, organic, percent_sand=sand_pct, percent_gravel=gravel_pct, percent_plus_200=100-p200
                )
            else:  # Coarse-grained soil
                classification, description, detailed = self.classify_coarse_grained(
                    p200, gravel_pct, sand_pct, cu, cc, ll, pi
                )

            
            # Update results
            self.classification_result.set(classification)
            self.description_result.set(description)
            self.detailed_description.set(detailed)
            self.cu_result.set(f"{cu:.2f}")
            self.cc_result.set(f"{cc:.2f}")
            self.p200_result.set(f"{p200:.1f}%")
            
            # Switch to results tab
            self.notebook.select(self.results_tab)
            
            # Update plasticity chart
            if p200 < 5:
                self.draw_blank_plasticity_chart()
            else:
                self.update_plasticity_chart(ll, pi, classification)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
    
    def classify_fine_grained(self, ll, pi, organic, percent_sand=0, percent_gravel=0, percent_plus_200=0):
        # Determine position relative to A-line (corrected formula)
        below_a_line = (pi < 4) or (pi < 0.73 * (ll - 20))
        
        # Determine coarse fraction characteristics
        has_sand = percent_sand >= 15
        has_gravel = percent_gravel >= 15
        sand_dominant = percent_sand >= percent_gravel
        gravel_dominant = percent_gravel > percent_sand
        
        if organic:
            # ORGANIC SOIL CLASSIFICATION (Figure 5.6)
            if ll >= 50:
                base_name = "OH"
                base_type = "Organic clay" if not below_a_line else "Organic silt"
            else:
                base_name = "OL"
                base_type = "Organic clay" if not below_a_line else "Organic silt"
            detail = (
                        f"Organic soil with LL={ll} ({'≥50' if ll>=50 else '<50'}). "
                        f"PI={pi} places it {'below' if below_a_line else 'above'} A-line. "
                        f"Contains {percent_plus_200}% fines with "
    )
            
            # Apply modifiers for coarse content
            if percent_plus_200 >= 30:
                if sand_dominant:
                    if has_gravel:
                        symbol = f"{base_name}"
                        base_desc = f"Sandy {base_type} with gravel"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
        )
                    else:
                        symbol = f"{base_name}"
                        base_desc = f"Sandy {base_type}"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
        )
                else:
                    if has_sand:
                        symbol = f"{base_name}"
                        base_desc = f"Gravelly {base_type} with sand"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
        )
                    else:
                        symbol = f"{base_name}"
                        base_desc = f"Gravelly {base_type}"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
        )
            else:
                if percent_plus_200 < 15 :
                    symbol = f" {base_name}"
                    base_desc = f"{base_type}"
                    detail += (f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). ")
                else:
                    if sand_dominant:
                        symbol = f"{base_name}"
                        base_desc = f"{base_type} with sand"
                        detail += (f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). ")
                    else:
                        symbol = f"{base_name}"
                        base_desc = f"{base_type} with gravel"
                        detail += (f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). ")
        
        else:
            detail = (
        f"Inorganic soil with LL={ll} ({'≥50' if ll>=50 else '<50'}), "
        f"PI={pi} ({'≥7' if pi>=7 else '<7'}) places it {'below' if below_a_line else 'above'} A-line. "
        f"Contains {percent_plus_200}% fines with "
    )
            if ll >= 50:
                # INORGANIC FINE-GRAINED SOIL CLASSIFICATION
                if (pi < 4) or (pi < 0.73 * (ll - 20)):
                    # SILT classification
                    base_name = "MH"
                    base_type = "elastic silt"
                else:
                    base_name = "CH"
                    base_type = "fat clay"
            else:
                if (pi < 4) or (pi < 0.73 * (ll - 20)):
                    base_name = "ML"
                    base_type = "silt"
                    # CLAY classification
                elif (pi > 7) and (pi >= 0.73 * (ll - 20)):
                    base_name = "CL"
                    base_type = "lean clay"
                else:
                    base_name = "CL_ML"
                    base_type = "silty clay"
            
            # Apply modifiers for coarse content
            if percent_plus_200 >= 30:
                if percent_sand >= percent_gravel:
                    if has_gravel:
                        symbol = f" {base_name}"
                        base_desc= f"Sandy {base_type} with gravel"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"{'Sandy' if sand_dominant else 'Gravelly'} dominant coarse fraction."
        )
                    else:
                        symbol = f"{base_name}"
                        base_desc = f"Sandy {base_type}"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"{'Sandy' if sand_dominant else 'Gravelly'} dominant coarse fraction."
        )
                    if has_sand:
                        symbol = f" {base_name} "
                        base_desc = f"Gravelly {base_type} with sand"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"{'Sandy' if sand_dominant else 'Gravelly'} dominant coarse fraction."
        )
                    else:
                        symbol = f" {base_name}"
                        base_desc = f"Gravelly {base_type}"
                        detail += (
            f"significant coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"{'Sandy' if sand_dominant else 'Gravelly'} dominant coarse fraction."
        )
            else:
                if percent_plus_200 <= 30 :
                    if percent_plus_200 <= 15:
                        symbol = f"{base_name}"
                        base_desc = f"{base_type}"
                        detail += (
            f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"Typical {base_type} behavior expected with "
            f"{'high' if ll>=50 else 'moderate'} plasticity characteristics."
        )
                    else:
                        if percent_sand >= percent_gravel:
                            symbol = f"{base_name}"
                            base_desc = f"{base_type} with sand"
                            detail += (
            f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"Typical {base_type} behavior expected with "
            f"{'high' if ll>=50 else 'moderate'} plasticity characteristics."
        )
                        else:
                            symbol = f"{base_name}"
                            base_desc = f"{base_type} with gravel"
                            detail += (
            f"minimal coarse fraction ({percent_sand}% sand, {percent_gravel}% gravel). "
            f"Typical {base_type} behavior expected with "
            f"{'high' if ll>=50 else 'moderate'} plasticity characteristics."
        )
        desc = base_desc
        # Build detailed description
        return symbol, desc, detail

    
    def classify_coarse_grained(self, p200, gravel_pct, sand_pct, cu, cc, ll, pi):
        """Classify coarse-grained soils with detailed description including subcategories"""
    # Determine dominant fraction and coarse type
        if gravel_pct > sand_pct:
            first_letter = "G"
            cu_min = 4  # Gravel requires Cu ≥ 4 for well-graded
            coarse_type = "gravel"
            other_type = "sand"
            other_pct = sand_pct
        else:
            first_letter = "S"
            cu_min = 6  # Sand requires Cu ≥ 6 for well-graded
            coarse_type = "sand"
            other_type = "gravel"
            other_pct = gravel_pct

        # Check fines content
        if p200 < 5:
            # Clean soil (less than 5% fines)
            well_graded = (cu >= cu_min) and (1 <= cc <= 3)
            
            if well_graded:
                symbol = f"{first_letter}W"
                if other_pct >= 15:
                    desc = f"Well-graded {coarse_type} with {other_type}"
                    detail = (f"Good particle size distribution with Cᵤ ≥ {cu_min} and 1 ≤ C꜀ ≤ 3. "
                            f"Contains ≥15% {other_type}. "
                            )
                else:
                    desc = f"Well-graded {coarse_type}"
                    detail = (f"Good particle size distribution with Cᵤ ≥ {cu_min} and 1 ≤ C꜀ ≤ 3. "
                            f"Contains <15% {other_type}. "
                            )
            else:
                symbol = f"{first_letter}P"
                if other_pct >= 15:
                    desc = f"Poorly-graded {coarse_type} with {other_type}"
                    detail = (f"Uniform or gap-graded {coarse_type} with ≥15% {other_type}. "
                            f"Cᵤ < {cu_min} or C꜀ outside 1-3 range"
                            )
                else:
                    desc = f"Poorly-graded {coarse_type}"
                    detail = (f"Uniform or gap-graded {coarse_type} with Cᵤ < {cu_min} or C꜀ outside 1-3 range. "
                            f"Contains <15% {other_type} "
                            )

        elif 5 <= p200 <= 12:
            # Dual classification (5-12% fines)
            base_class = ""
            if (cu >= cu_min) and (1 <= cc <= 3):
                base_class = f"{first_letter}W"
                gradation = "well-graded"
            else:
                base_class = f"{first_letter}P"
                gradation = "poorly-graded"

            # Determine fines type
            if pi >= 4 and not (ll > 25.5 and pi < 0.73 * (ll - 20)):
                # Clayey fines
                symbol = f"{base_class}-{first_letter}C"
                if other_pct >= 15:
                    desc = f"{gradation.capitalize()} {coarse_type} with clay and {other_type} "
                    detail = (f"{coarse_type.capitalize()} with 5-12% clayey fines and ≥15% {other_type}. "
                            )
                else:
                    desc = f"{gradation.capitalize()} {coarse_type} with clay"
                    detail = (f"{coarse_type.capitalize()} with 5-12% clayey fines and <15% {other_type}. "
                            )
            else:
                # Silty fines
                symbol = f"{base_class}-{first_letter}M"
                if other_pct >= 15:
                    desc = f"{gradation.capitalize()} {coarse_type} with silt and {other_type}"
                    detail = (f"{coarse_type.capitalize()} with 5-12% silty fines and ≥15% {other_type}. "
                            )
                else:
                    desc = f"{gradation.capitalize()} {coarse_type} with silt"
                    detail = (f"{coarse_type.capitalize()} with 5-12% silty fines and <15% {other_type}. "
                            )

        else:
            # Dirty soil (more than 12% fines)
            if pi > 7 and not (ll > 25.5 and pi < 0.73 * (ll - 20)):
                # Clayey fines
                symbol = f"{first_letter}C"
                if other_pct >= 15:
                    desc = f"Clayey {coarse_type.capitalize()} with {other_type}"
                    detail = (f"{coarse_type.capitalize()} with >12% clay fines and ≥15% {other_type}. "
                            )
                else:
                    desc = f"Clayey {coarse_type.capitalize()}"
                    detail = (f"{coarse_type.capitalize()} with >12% clay fines and <15% {other_type}. "
                            )
                    
            
            elif pi < 4:
                # Below A-line (silt)
                # Silty fines
                symbol = f"{first_letter}M"
                if other_pct >= 15:
                    desc = f"Silty {coarse_type.capitalize()} with {other_type}"
                    detail = (f"{coarse_type.capitalize()} with >12% silty fines and ≥15% {other_type}. "
                            )
                else:
                    desc = f" Silty {coarse_type.capitalize()}"
                    detail = (f"{coarse_type.capitalize()} with >12% silty fines and <15% {other_type}. "
                            )
            else:
                # Silty fines
                symbol = f"{first_letter}C-{first_letter}M" if first_letter == "G" else f"{first_letter}C-{first_letter}M"
                if other_pct >= 15:
                    desc = f"Silty clayey {coarse_type.capitalize()} with {other_type}"
                    detail = (f"{coarse_type.capitalize()} with >12% clayey-silty fines and ≥15% {other_type}. "
                            )
                else:
                    desc = f"Silty clayey {coarse_type.capitalize()}"
                    detail = (f"{coarse_type.capitalize()} with >12% clayey-silty fines and <15% {other_type}. "
                            )

        return symbol, desc, detail
    
    def toggle_input_mode(self):
        """Show/hide the appropriate input fields based on selected mode"""
        if self.input_mode.get() == "D_values":
            self.d_values_frame.pack(fill='x', pady=5)
            self.coeff_frame.pack_forget()
            self.calc_button_frame.pack(fill='x', pady=5)
        else:
            self.d_values_frame.pack_forget()
            self.coeff_frame.pack(fill='x', pady=5)
            self.calc_button_frame.pack_forget()
    
    def clear_all(self):
        """Reset all input fields and results"""
        # Reset all variables
        for var in [self.boulders, self.cobbles, self.gravel, self.sand, self.fines,
                   self.ll, self.pl, self.pi, self.d10, self.d30, self.d60,
                   self.cu, self.cc, self.air_dry_ll, self.oven_dry_ll]:
            var.set(0.0)
        
        # Clear results
        self.classification_result.set("")
        self.description_result.set("")
        self.detailed_description.set("")
        self.cu_result.set("")
        self.cc_result.set("")
        self.p200_result.set("")
        
        # Reset input mode
        self.input_mode.set("D_values")
        self.toggle_input_mode()
        
        # Reset chart
        self.draw_blank_plasticity_chart()
    
    def load_example_data(self):
        """Return dictionary of example soil data"""
        examples = {
            "Well-graded Gravel (GW)": {
                "boulders": 0, "cobbles": 0, "gravel": 60, "sand": 30, "fines": 10,
                "ll": 0, "pl": 0, "d10": 0.5, "d30": 5, "d60": 20
            },
            "Poorly-graded Sand (SP)": {
                "boulders": 0, "cobbles": 0, "gravel": 10, "sand": 85, "fines": 5,
                "ll": 0, "pl": 0, "d10": 0.1, "d30": 0.2, "d60": 0.5
            },
            "Clay with High Plasticity (CH)": {
                "boulders": 0, "cobbles": 0, "gravel": 5, "sand": 10, "fines": 85,
                "ll": 65, "pl": 25, "d10": 0, "d30": 0, "d60": 0
            },
            "Silty Sand (SM)": {
                "boulders": 0, "cobbles": 0, "gravel": 5, "sand": 60, "fines": 35,
                "ll": 32, "pl": 25, "d10": 0.08, "d30": 0.2, "d60": 1.0
            },
            "Organic Clay (OH)": {
                "boulders": 0, "cobbles": 0, "gravel": 0, "sand": 20, "fines": 80,
                "ll": 68, "pl": 32, "air_dry_ll": 70, "oven_dry_ll": 50,
                "d10": 0, "d30": 0, "d60": 0
            }
        }
        return examples
    
    def load_example(self):
        """Load example data from the examples dictionary"""
        example_names = list(self.examples.keys())
        
        def on_select(event):
            selected = example_listbox.get(example_listbox.curselection())
            data = self.examples[selected]
            
            # Set all values
            self.boulders.set(data.get("boulders", 0))
            self.cobbles.set(data.get("cobbles", 0))
            self.gravel.set(data.get("gravel", 0))
            self.sand.set(data.get("sand", 0))
            self.fines.set(data.get("fines", 0))
            self.ll.set(data.get("ll", 0))
            self.pl.set(data.get("pl", 0))
            self.d10.set(data.get("d10", 0))
            self.d30.set(data.get("d30", 0))
            self.d60.set(data.get("d60", 0))
            self.air_dry_ll.set(data.get("air_dry_ll", 0))
            self.oven_dry_ll.set(data.get("oven_dry_ll", 0))
            
            # Calculate PI if LL and PL are provided
            if data.get("ll", 0) > 0 and data.get("pl", 0) > 0:
                self.calculate_pi()
            
            # Calculate coefficients if D values are provided
            if data.get("d10", 0) > 0:
                self.calculate_coefficients()
            
            example_dialog.destroy()
        
        # Create dialog to select example
        example_dialog = tk.Toplevel(self.root)
        example_dialog.title("Select Example")
        example_dialog.geometry("300x300")
        
        ttk.Label(example_dialog, text="Select an example soil:").pack(pady=5)
        
        example_listbox = tk.Listbox(example_dialog)
        example_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        for name in example_names:
            example_listbox.insert('end', name)
        
        example_listbox.bind('<<ListboxSelect>>', on_select)
        
        ttk.Button(example_dialog, text="Cancel", style="Accent.TButton",
                  command=example_dialog.destroy).pack(pady=5)
    
    def save_data(self):
        """Save current input data to JSON file"""
        data = {
            "boulders": self.boulders.get(),
            "cobbles": self.cobbles.get(),
            "gravel": self.gravel.get(),
            "sand": self.sand.get(),
            "fines": self.fines.get(),
            "ll": self.ll.get(),
            "pl": self.pl.get(),
            "d10": self.d10.get(),
            "d30": self.d30.get(),
            "d60": self.d60.get(),
            "air_dry_ll": self.air_dry_ll.get(),
            "oven_dry_ll": self.oven_dry_ll.get()
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Soil Data"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                messagebox.showinfo("Success", "Soil data saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def load_data(self):
        """Load input data from JSON file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Open Soil Data"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Set all values
                self.boulders.set(data.get("boulders", 0))
                self.cobbles.set(data.get("cobbles", 0))
                self.gravel.set(data.get("gravel", 0))
                self.sand.set(data.get("sand", 0))
                self.fines.set(data.get("fines", 0))
                self.ll.set(data.get("ll", 0))
                self.pl.set(data.get("pl", 0))
                self.d10.set(data.get("d10", 0))
                self.d30.set(data.get("d30", 0))
                self.d60.set(data.get("d60", 0))
                self.air_dry_ll.set(data.get("air_dry_ll", 0))
                self.oven_dry_ll.set(data.get("oven_dry_ll", 0))
                
                # Calculate PI if LL and PL are provided
                if data.get("ll", 0) > 0 and data.get("pl", 0) > 0:
                    self.calculate_pi()
                
                messagebox.showinfo("Success", "Soil data loaded successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = USCS_Classifier(root)
    root.mainloop()