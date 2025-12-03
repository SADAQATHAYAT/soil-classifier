import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import numpy as np
import pandas as pd
from scipy import interpolate, optimize
from shapely.geometry import LineString, Point, MultiPoint
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy import interpolate
import json
import os
from typing import List, Tuple, Dict, Optional
from tooltip import ToolTip  # Custom tooltip class

# Predefined sieve sizes and sieve numbers
SIEVE_SIZES = [
    (4.75, "No. 4"), (2.36, "No. 8"), (1.18, "No. 16"),
    (0.60, "No. 30"), (0.30, "No. 50"), (0.15, "No. 100"), (0.075, "No. 200")
]

SAMPLE_DATA = {
    "Well Graded Sand": {
        "total_weight": 500,
        "data": [
            (4.75, "No. 4", 0),
            (2.36, "No. 8", 25),
            (1.18, "No. 16", 75),
            (0.60, "No. 30", 150),
            (0.30, "No. 50", 175),
            (0.15, "No. 100", 50),
            (0.075, "No. 200", 25)
        ]
    },
    "Poorly Graded Gravel": {
        "total_weight": 1000,
        "data": [
            (25.0, "1 inch", 400),
            (19.0, "3/4 inch", 300),
            (12.5, "1/2 inch", 200),
            (4.75, "No. 4", 100),
            (0.0, "Pan", 0)
        ]
    }
}

class SieveAnalysisModel:
    """
    A comprehensive model for sieve analysis calculations with precise D-value determination.
    Maintains PCHIP interpolation while ensuring accurate curve intersections.
    """

    def __init__(self):
        """Initialize the model with default values"""
        self.reset_data()

    def reset_data(self) -> None:
        """
        Reset all data structures to their initial state.
        Called when starting a new analysis.
        """
        self.total_weight: float = 0.0
        self.sieve_sizes: List[float] = []
        self.sieve_numbers: List[str] = []
        self.retained_masses: List[float] = []
        self.xs: np.ndarray = np.array([])
        self.ys: np.ndarray = np.array([])
        self.x_smooth: np.ndarray = np.array([])
        self.y_smooth: np.ndarray = np.array([])
        self.intersections: Dict[str, float] = {}
        self.coefficients: Dict[str, Optional[float]] = {}
        self.particle_distribution: Dict[str, float] = {}
        self.plot_type: str = "semi-log"
        self.pchip_interpolator: Optional[interpolate.PchipInterpolator]
    def classify_particle_size(self, size: float) -> str:
        """
        Classifies particle size into standard categories according to ASTM D2487/USCS.
        
        Args:
            size: Particle size in millimeters (mm)
            
        Returns:
            str: The particle size category description
            
        Categories:
            - Boulders (> 300 mm)
            - Cobbles (75 - 300 mm)
            - Gravel (4.75 - 75 mm)
            - Sand (0.075 - 4.75 mm)
            - Fines (< 0.075 mm)
        """
       
        if size > 300:
            return "Boulders (> 300 mm)"
        elif 75 <= size <= 300:
            return "Cobbles (75 - 300 mm)"
        elif 4.75 <= size < 75:
            return "Gravel (4.75 - 75 mm)"
        elif 0.075 <= size < 4.75:
            return "Sand (0.075 - 4.75 mm)"
        else:  # size <= 0.075
            return "Fines (< 0.075 mm)"

    def calculate(self, total_weight: float, sieve_data: List[Tuple[float, str, float]]) -> None:
        """
        Perform complete sieve analysis calculations.
        
        Args:
            total_weight: Total weight of the sample in grams
            sieve_data: List of tuples (sieve_size, sieve_number, retained_mass)
        """
        self.total_weight = total_weight
        self.sieve_sizes = [d[0] for d in sieve_data]
        self.sieve_numbers = [d[1] for d in sieve_data]
        self.retained_masses = [d[2] for d in sieve_data]

        # Calculate cumulative percentages
        self._calculate_percentages()
        
        # Create smooth PCHIP curve
        self.create_smooth_curve()
        
        # Calculate precise D-values
        self.calculate_d_values()
        
        # Compute derived parameters
        self.calculate_coefficients()
        self.calculate_particle_distribution()

    def _calculate_percentages(self) -> None:
        """Calculate cumulative percentages from retained masses"""
        # Calculate the cumulative sum of the retained masses
        cum_rets = np.cumsum(self.retained_masses)
        # Get the total retained mass
        total = cum_rets[-1] if len(cum_rets) > 0 else 0
        
        # If the total retained mass is greater than 0
        if total > 0:
            # Calculate the cumulative percentage
            self.cum_percent = np.round(cum_rets / total * 100, 4)
            # Calculate the pass percentage
            self.pass_percent = np.round(100 - self.cum_percent, 4)
        else:
            # If the total retained mass is 0, set the cumulative and pass percentages to 0
            self.cum_percent = np.zeros_like(cum_rets)
            self.pass_percent = np.zeros_like(cum_rets)
        
        # Convert the sieve sizes to an array
        self.xs = np.array(self.sieve_sizes)
        # Convert the pass percentages to an array
        self.ys = np.array(self.pass_percent)

    def create_smooth_curve(self) -> None:
        """
        Create a smooth grain size distribution curve using PCHIP interpolation.
        Falls back to linear interpolation if PCHIP fails.
        """
        if len(self.xs) < 2:
            raise ValueError("At least two data points required for interpolation")
            
        # Sort data by particle size
        sorted_idx = np.argsort(self.xs)
        x_sorted = self.xs[sorted_idx]
        y_sorted = self.ys[sorted_idx]
        
        try:
            # Create PCHIP interpolator and store it for later use
            self.pchip_interpolator = interpolate.PchipInterpolator(x_sorted, y_sorted)
            
            # Generate smooth curve with high resolution (1000 points)
            self.x_smooth = np.logspace(
                np.log10(min(x_sorted)), 
                np.log10(max(x_sorted)), 
                1000
            )
            self.y_smooth = self.pchip_interpolator(self.x_smooth)
            
        except Exception as e:
            print(f"PCHIP interpolation failed, falling back to linear: {e}")
            self.pchip_interpolator = interpolate.interp1d(
                x_sorted, y_sorted, 
                kind='linear', 
                fill_value='extrapolate'
            )
            self.x_smooth = np.logspace(
                np.log10(min(x_sorted)), 
                np.log10(max(x_sorted)), 
                1000
            )
            self.y_smooth = self.pchip_interpolator(self.x_smooth)

    def calculate_d_values(self) -> None:
        """
        Calculate D10, D30, D60 values with precision guaranteed to lie on the curve.
        Uses a three-stage approach for robustness:
        1. Exact root finding
        2. Refined local search
        3. Closest point fallback
        """
        P_values = [10, 30, 60]
        self.intersections = {}

        for P in P_values:
            try:
                # Stage 1: Try exact root finding
                root = self._find_exact_intersection(P)
                if root is not None:
                    self.intersections[f"D{P}"] = round(root, 4)
                    continue
                    
                # Stage 2: Refined search near closest point
                refined_val = self._refined_intersection_search(P)
                if refined_val is not None:
                    self.intersections[f"D{P}"] = round(refined_val, 4)
                    continue
                    
                # Stage 3: Fallback to closest point
                closest_idx = np.argmin(np.abs(self.y_smooth - P))
                self.intersections[f"D{P}"] = round(self.x_smooth[closest_idx], 4)
                
            except Exception as e:
                print(f"Error calculating D{P}: {e}")
                closest_idx = np.argmin(np.abs(self.y_smooth - P))
                self.intersections[f"D{P}"] = round(self.x_smooth[closest_idx], 4)

    def _find_exact_intersection(self, P: float) -> Optional[float]:
        """
        Find exact intersection point using root finding.
        
        Args:
            P: Percentage value to find (10, 30, or 60)
            
        Returns:
            The particle size (D-value) where the curve intersects P, or None if not found
        """
        if self.pchip_interpolator is None:
            return None
            
        # Define the function to find roots for: f(x) = y(x) - P
        def f(x):
            return self.pchip_interpolator(x) - P
            
        # Get the data bounds
        x_min, x_max = min(self.xs), max(self.xs)
        
        # Find all crossing points where the curve passes through P
        crossing_points = []
        for i in range(len(self.y_smooth)-1):
            if (self.y_smooth[i] - P) * (self.y_smooth[i+1] - P) < 0:
                x0 = self.x_smooth[i]
                x1 = self.x_smooth[i+1]
                try:
                    root = optimize.brentq(
                        f, x0, x1, 
                        xtol=1e-8,  # Very tight tolerance
                        rtol=1e-8,
                        maxiter=100
                    )
                    if x_min <= root <= x_max:  # Only accept roots within data range
                        crossing_points.append(root)
                except:
                    continue
                    
        return min(crossing_points) if crossing_points else None

    def _refined_intersection_search(self, P: float) -> Optional[float]:
        """
        Perform a refined search near the closest point to find better intersection.
        
        Args:
            P: Percentage value to find (10, 30, or 60)
            
        Returns:
            The best found particle size near the closest point, or None if search fails
        """
        if self.pchip_interpolator is None:
            return None
            
        # Find the closest point on the smooth curve
        closest_idx = np.argmin(np.abs(self.y_smooth - P))
        x_closest = self.x_smooth[closest_idx]
        
        # Determine search window around the closest point
        if closest_idx == 0:
            x0, x1 = x_closest, self.x_smooth[closest_idx+1]
        elif closest_idx == len(self.x_smooth)-1:
            x0, x1 = self.x_smooth[closest_idx-1], x_closest
        else:
            x0, x1 = self.x_smooth[closest_idx-1], self.x_smooth[closest_idx+1]
            
        # Sample many points in this window
        x_window = np.linspace(x0, x1, 1000)
        y_window = self.pchip_interpolator(x_window)
        
        # Find the point with minimum distance to P
        best_idx = np.argmin(np.abs(y_window - P))
        return x_window[best_idx]

    def calculate_coefficients(self) -> None:
        """
        Calculate the coefficient of uniformity (Cu) and coefficient of curvature (Cc).
        Ensures proper handling of edge cases and division by zero.
        """
        D10 = self.intersections.get("D10", None)
        D30 = self.intersections.get("D30", None)
        D60 = self.intersections.get("D60", None)
        
        # Calculate Cu = D60/D10 with safety checks
        try:
            Cu = D60 / D10 if all(v is not None for v in [D10, D60]) and D10 != 0 else None
        except:
            Cu = None
            
        # Calculate Cc = (D30)^2/(D60*D10) with safety checks
        try:
            Cc = (D30**2) / (D60 * D10) if all(v is not None for v in [D10, D30, D60]) and (D60 * D10) != 0 else None
        except:
            Cc = None
            
        self.coefficients = {
            "Cu": round(Cu, 4) if Cu is not None else None,
            "Cc": round(Cc, 4) if Cc is not None else None
        }

    
    def calculate_particle_distribution(self) -> None: #
        """
        Calculates particle distribution based on direct retained masses according to ASTM D2487/USCS.
        - Boulders: Retained on sieves > 300 mm.
        - Cobbles: Retained on sieves between 75 mm and 300 mm (inclusive).
        - Gravel: Retained on sieves between 4.75 mm and < 75 mm.
        - Sand: Retained on sieves between 0.075 mm and < 4.75 mm.
        - Fines: Passing 0.075 mm sieve (material on Pan).
        """
        # Initialize dictionary with all categories
        self.particle_distribution = { #
            "Boulders (> 300 mm)": 0.0, #
            "Cobbles (75 - 300 mm)": 0.0, #
            "Gravel (4.75 - 75 mm)": 0.0, #
            "Sand (0.075 - 4.75 mm)": 0.0, #
            "Fines (< 0.075 mm)": 0.0, #
        }

        if not hasattr(self, 'total_weight') or self.total_weight <= 0: #
            # This check might be better placed in the main 'calculate' method
            # or handled by the controller to avoid direct UI calls from model.
            # For now, retaining similar error handling as in the original code.
            if hasattr(self.view, 'total_weight_entry'): # Check if view is available
                 messagebox.showerror("Error", "Total weight must be positive to calculate particle distribution.") #
            return

        if not hasattr(self, 'sieve_sizes') or not hasattr(self, 'retained_masses') or \
           not self.sieve_sizes or not self.retained_masses: #
            if hasattr(self.view, 'total_weight_entry'): # Check if view is available
                messagebox.showerror("Error", "Sieve data (sizes and masses) is missing.") #
            return

        mass_boulders = 0.0
        mass_cobbles = 0.0
        mass_gravel = 0.0
        mass_sand = 0.0
        
        # Sum of masses retained on all actual sieves
        sum_retained_on_sieves = sum(m for s, m in zip(self.sieve_sizes, self.retained_masses) if s > 0) # Exclude pan if it has size 0.0

        # Calculate mass on pan (fines)
        # This is the material finer than the smallest sieve (typically 0.075mm)
        mass_fines_pan = self.total_weight - sum_retained_on_sieves #

        # Check for data consistency: sum of retained masses (including calculated pan) should equal total weight.
        # A small tolerance is used for floating point comparisons.
        if mass_fines_pan < -1e-9:  # If sum_retained_on_sieves > self.total_weight #
            error_msg = (f"Data Error: Sum of retained masses on sieves ({sum_retained_on_sieves:.2f}g) " #
                         f"exceeds total sample weight ({self.total_weight:.2f}g). " #
                         "Please check input data.") #
            if hasattr(self.view, 'total_weight_entry'): # Check if view is available
                 messagebox.showerror("Data Error", error_msg) #
            else:
                print(f"[ERROR] {error_msg}") #
            # Reset distribution to zeros as it's invalid
            for key in self.particle_distribution: #
                self.particle_distribution[key] = 0.0 #
            return
        mass_fines_pan = max(0, mass_fines_pan) # Ensure it's not negative due to minor precision issues

        # Iterate through each sieve and its retained mass to categorize particles
        for size, retained_mass in zip(self.sieve_sizes, self.retained_masses): #
            if size <= 0: # Skip pan if it was included in sieve_data with size 0
                continue
            if size > 300: # Boulders
                mass_boulders += retained_mass
            elif 75 <= size <= 300: # Cobbles
                mass_cobbles += retained_mass
            elif 4.75 <= size < 75: # Gravel
                mass_gravel += retained_mass
            elif 0.075 <= size < 4.75: # Sand
                mass_sand += retained_mass
            # Material retained on a sieve smaller than 0.075mm is not standard;
            # fines are defined as passing 0.075mm.

        # Calculate percentages based on the total weight of the sample
        if self.total_weight > 0:
            self.particle_distribution["Boulders (> 300 mm)"] = round((mass_boulders / self.total_weight) * 100, 2) #
            self.particle_distribution["Cobbles (75 - 300 mm)"] = round((mass_cobbles / self.total_weight) * 100, 2) #
            self.particle_distribution["Gravel (4.75 - 75 mm)"] = round((mass_gravel / self.total_weight) * 100, 2) #
            self.particle_distribution["Sand (0.075 - 4.75 mm)"] = round((mass_sand / self.total_weight) * 100, 2) #
            self.particle_distribution["Fines (< 0.075 mm)"] = round((mass_fines_pan / self.total_weight) * 100, 2) #
        
        # Optional: Validate that the sum of percentages is close to 100%
        current_total_percentage = sum(self.particle_distribution.values()) #
        if not (99.9 <= current_total_percentage <= 100.1) and self.total_weight > 0: #
            # This might indicate a slight discrepancy due to rounding or an issue if pan mass was miscalculated.
            print(f"[INFO] Particle distribution percentages sum to {current_total_percentage:.2f}%. This is usually due to rounding.") #
            # Adjust Fines to make total 100% if the discrepancy is small and due to rounding.
            if abs(100.0 - current_total_percentage) < 0.5 : # Small discrepancy threshold
                diff = 100.0 - current_total_percentage
                self.particle_distribution["Fines (< 0.075 mm)"] = round(self.particle_distribution["Fines (< 0.075 mm)"] + diff, 2)
                # Ensure fines percentage is not negative after adjustment
                if self.particle_distribution["Fines (< 0.075 mm)"] < 0:
                    # If fines become negative, it implies a larger issue,
                    # redistribute deficit/surplus proportionally or revert adjustment.
                    # For simplicity here, we'll just cap at 0 and accept minor total deviation.
                    self.particle_distribution["Fines (< 0.075 mm)"] = 0.0
                current_total_percentage = sum(self.particle_distribution.values()) # Re-check
                print(f"[INFO] Adjusted particle distribution percentages sum to {current_total_percentage:.2f}%.")

    def validate_results(self) -> bool:
        """
        Validate that the calculated results are physically reasonable.
        
        Returns:
            True if results are valid, False otherwise
        """
        # Check D-values are monotonically increasing
        Ds = [self.intersections.get(f"D{p}", None) for p in [10, 30, 60]]
        if None in Ds:
            return False
        if not (Ds[0] <= Ds[1] <= Ds[2]):
            return False
            
        # Check coefficients are within reasonable bounds
        Cu = self.coefficients.get("Cu", None)
        Cc = self.coefficients.get("Cc", None)
        if Cu is not None and Cu <= 0:
            return False
        if Cc is not None and Cc <= 0:
            return False
            
        # Check percentages sum to 100 ± 0.1%
        total_percent = sum(self.particle_distribution.values())
        if abs(total_percent - 100) > 0.1:
            return False
            
        return True

class SieveAnalysisView(ttk.Frame):
    """View class handling all UI components"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()
        
    def create_widgets(self):
        """Create all UI widgets"""
        self.create_gradient_background()
        self.show_welcome_message()
        
    def create_gradient_background(self):
        """Create gradient background canvas"""
        self.canvas = tk.Canvas(self, width=1000, height=700, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        for i in range(700):
            color = self.get_gradient_color(i, 700)
            self.canvas.create_line(0, i, 1000, i, fill=color, width=1)
            
    def get_gradient_color(self, y, height):
        """Generate gradient color based on y-coordinate"""
        r = int(135 + (120 * y / height))
        g = int(206 + (50 * y / height))
        b = int(250 - (50 * y / height))
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def show_welcome_message(self):
        """Show welcome message with delay"""
        self.welcome_label = tk.Label(
            self.canvas, text="Welcome to Sieve Analysis Tool", 
            font=("Arial", 28, "bold"), fg="#1E9D22", bg="#f0f0f0"
        )
        self.welcome_label.place(relx=0.5, rely=0.5, anchor="center")
        self.after(2000, self.setup_main_ui)
        
    def setup_main_ui(self):
        """Setup main UI after welcome message"""
        self.welcome_label.place_forget()
        
        # Create scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Create input widgets
        self.create_input_widgets()
        
    def create_input_widgets(self):
        """Create all input widgets"""
        # Title
        self.title_label = tk.Label(
            self.scrollable_frame, text="Sieve Analysis Input", 
            font=("Arial", 20, "bold"), fg="#333399", bg="#f0f0f0"
        )
        self.title_label.pack(pady=20)
        
        # Total weight input
        self.total_weight_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.total_weight_frame.pack(pady=10)
        
        self.total_weight_label = tk.Label(
            self.total_weight_frame, text="Total Weight (g):", 
            font=("Arial", 14, "bold"), fg="#009999", bg="#f0f0f0"
        )
        self.total_weight_label.pack(side=tk.LEFT, padx=10)
        
        self.total_weight_entry = tk.Entry(
            self.total_weight_frame, font=("Arial", 14), width=15
        )
        self.total_weight_entry.pack(side=tk.LEFT)
        
        # Add tooltip for total weight
        ToolTip(self.total_weight_label, 
               "Enter the total weight of the sample before sieving in grams")
        
        # Sample data dropdown
        self.sample_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.sample_frame.pack(pady=10)
        
        self.sample_label = tk.Label(
            self.sample_frame, text="Load Sample Data:", 
            font=("Arial", 14, "bold"), fg="#009999", bg="#f0f0f0"
        )
        self.sample_label.pack(side=tk.LEFT, padx=10)
        
        self.sample_var = tk.StringVar()
        self.sample_dropdown = ttk.Combobox(
            self.sample_frame, textvariable=self.sample_var, 
            values=["Select Sample..."] + list(SAMPLE_DATA.keys()), 
            state="readonly", font=("Arial", 12), width=20
        )
        self.sample_dropdown.current(0)
        self.sample_dropdown.pack(side=tk.LEFT)
        self.sample_dropdown.bind("<<ComboboxSelected>>", self.load_sample_data)
        
        # Input table frame
        self.input_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.input_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Table headers
        headers = ["Sieve Size (mm)", "Sieve Number", "Retained (g)"]
        for col, header in enumerate(headers):
            label = tk.Label(
                self.input_frame, text=header, 
                font=("Arial", 14, "bold"), fg="#009999", bg="#f0f0f0"
            )
            label.grid(row=0, column=col, padx=10, pady=5)
            
            # Add tooltips for headers
            if col == 0:
                ToolTip(label, "Enter the sieve opening size in millimeters")
            elif col == 1:
                ToolTip(label, "Enter the standard sieve number designation")
            else:
                ToolTip(label, "Enter the mass retained on each sieve in grams")
        
        # Add initial rows
        self.entries = []
        for size, number in SIEVE_SIZES:
            self.add_row(size, number)
        
        # Button frame
        self.button_frame = tk.Frame(self.scrollable_frame, bg="#f0f0f0")
        self.button_frame.pack(pady=20)
        
        # Action buttons
        buttons = [
            ("Add Sieve", self.controller.add_row, "#4CAF50"),
            ("Calculate", self.controller.calculate, "#2196F3"),
            ("Save Data", self.controller.save_data, "#FF9800"),
            ("Load Data", self.controller.load_data, "#9C27B0"),
            ("Clear Inputs", self.controller.clear_inputs, "#F44336")
        ]
        
        for col, (text, command, color) in enumerate(buttons):
            btn = tk.Button(
                self.button_frame, text=text, command=command,
                font=("Arial", 14, "bold"), bg=color, fg="white", 
                padx=10, pady=5, width=12
            )
            btn.grid(row=0, column=col, padx=5)
            
            # Add tooltips for buttons
            if text == "Add Sieve":
                ToolTip(btn, "Add a new row for additional sieve data")
            elif text == "Calculate":
                ToolTip(btn, "Calculate particle size distribution and coefficients")
            elif text == "Save Data":
                ToolTip(btn, "Save current data to a file")
            elif text == "Load Data":
                ToolTip(btn, "Load data from a previously saved file")
            else:
                ToolTip(btn, "Clear all input fields")
    
    def add_row(self, size_value="", number_value="", retained_value=""):
        """Add a new row to the input table"""
        row = len(self.entries) + 1
        
        size_entry = tk.Entry(self.input_frame, font=("Arial", 14))
        size_entry.insert(0, str(size_value))
        
        number_entry = tk.Entry(self.input_frame, font=("Arial", 14))
        number_entry.insert(0, str(number_value))
        
        ret_entry = tk.Entry(self.input_frame, font=("Arial", 14))
        ret_entry.insert(0, str(retained_value))
        
        size_entry.grid(row=row, column=0, padx=10, pady=5)
        number_entry.grid(row=row, column=1, padx=10, pady=5)
        ret_entry.grid(row=row, column=2, padx=10, pady=5)
        
        # Bind navigation keys
        for entry in [size_entry, number_entry, ret_entry]:
            entry.bind("<Tab>", lambda e: e.widget.tk_focusNext().focus())
            entry.bind("<Return>", lambda e: e.widget.tk_focusNext().focus())
        
        self.entries.append((size_entry, number_entry, ret_entry))
        
    def load_sample_data(self, event):
        """Load selected sample data"""
        sample_name = self.sample_var.get()
        if sample_name in SAMPLE_DATA:
            sample = SAMPLE_DATA[sample_name]
            
            # Clear existing entries
            for size_entry, number_entry, ret_entry in self.entries:
                size_entry.destroy()
                number_entry.destroy()
                ret_entry.destroy()
            self.entries = []
            
            # Set total weight
            self.total_weight_entry.delete(0, tk.END)
            self.total_weight_entry.insert(0, str(sample["total_weight"]))
            
            # Add sample data rows
            for size, number, retained in sample["data"]:
                self.add_row(size, number, retained)
                
            messagebox.showinfo("Sample Loaded", f"'{sample_name}' sample data loaded successfully")
            
    def show_results_view(self):
        """Show results view after calculation"""
        self.clear_current_view()
        
        # Results buttons
        self.results_button = tk.Button(
            self.scrollable_frame, text="📊 Results", 
            command=self.controller.show_results,
            font=("Arial", 16, "bold"), bg="#4CAF50", fg="white", 
            padx=20, pady=10, width=15
        )
        self.results_button.pack(pady=10)
        
        self.graph_button = tk.Button(
            self.scrollable_frame, text="📈 Graph", 
            command=self.controller.show_graph,
            font=("Arial", 16, "bold"), bg="#2196F3", fg="white", 
            padx=20, pady=10, width=15
        )
        self.graph_button.pack(pady=10)
        
        self.coefficients_button = tk.Button(
            self.scrollable_frame, text="🧮 Coefficients", 
            command=self.controller.show_coefficients,
            font=("Arial", 16, "bold"), bg="#9C27B0", fg="white", 
            padx=20, pady=10, width=15
        )
        self.coefficients_button.pack(pady=10)
        
        self.back_button = tk.Button(
            self.scrollable_frame, text="⬅ Back to Input", 
            command=self.controller.show_input_view,
            font=("Arial", 14), bg="#607D8B", fg="white", 
            padx=10, pady=5
        )
        self.back_button.pack(pady=20)
        
    def show_input_view(self):
        """Show input view"""
        self.clear_current_view()
        self.create_input_widgets()
        
    def clear_current_view(self):
        """Clear current view widgets"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
   
    def show_results_window(self, results, particle_distribution):
        """Display results in a new window with enhanced features"""
        results_window = tk.Toplevel(self)
        results_window.title("Sieve Analysis Results")
        results_window.geometry("800x600")
        results_window.resizable(True, True)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("Treeview", font=("Helvetica", 10))

        # Notebook tabs
        notebook = ttk.Notebook(results_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- D-values tab ---
        dvalues_frame = ttk.Frame(notebook)
        notebook.add(dvalues_frame, text="D-Values")

        dvalues_tree = ttk.Treeview(dvalues_frame, columns=("Parameter", "Value"), show="headings", height=10)
        dvalues_tree.heading("Parameter", text="Parameter")
        dvalues_tree.heading("Value", text="Value (mm)")
        dvalues_tree.column("Parameter", width=200, anchor=tk.CENTER)
        dvalues_tree.column("Value", width=100, anchor=tk.CENTER)

        for param, value in results.items():
            val_str = f"{value:.2f}" if value is not None else "N/A"
            dvalues_tree.insert("", tk.END, values=(param, val_str))

        dvalues_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar for D-values
        d_scroll = ttk.Scrollbar(dvalues_frame, orient="vertical", command=dvalues_tree.yview)
        dvalues_tree.configure(yscrollcommand=d_scroll.set)
        d_scroll.pack(side=tk.RIGHT, fill="y")

        # --- Particle Distribution tab ---
        dist_frame = ttk.Frame(notebook)
        notebook.add(dist_frame, text="Particle Distribution")

        dist_tree = ttk.Treeview(dist_frame, columns=("Category", "Percentage"), show="headings", height=10)
        dist_tree.heading("Category", text="Particle Size Category")
        dist_tree.heading("Percentage", text="Percentage (%)")
        dist_tree.column("Category", width=300, anchor=tk.W)
        dist_tree.column("Percentage", width=100, anchor=tk.CENTER)

        for category, percent in particle_distribution.items():
            dist_tree.insert("", tk.END, values=(category, f"{percent:.2f}"))

        dist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar for Distribution
        pd_scroll = ttk.Scrollbar(dist_frame, orient="vertical", command=dist_tree.yview)
        dist_tree.configure(yscrollcommand=pd_scroll.set)
        pd_scroll.pack(side=tk.RIGHT, fill="y")

        # --- Tooltips ---
        ToolTip(dvalues_tree, "D-values represent the particle size (mm) where \n"
                            "D10 = 10% of particles are finer\n"
                            "D30 = 30% of particles are finer\n"
                            "D60 = 60% of particles are finer")
        ToolTip(dist_tree, "Particle size distribution showing percentage \n"
                        "of material in each size category")

        # --- Export Buttons ---
        def export_to_csv(tree, filename_default):
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=filename_default,
                                                    filetypes=[("CSV files", "*.csv")])
            if file_path:
                with open(file_path, mode="w", newline="") as file:
                    writer = csv.writer(file)
                    # Write headers
                    writer.writerow([tree.heading(col)["text"] for col in tree["columns"]])
                    # Write data
                    for row in tree.get_children():
                        writer.writerow(tree.item(row)["values"])

        btn_frame = ttk.Frame(results_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Export D-Values to CSV",
                command=lambda: export_to_csv(dvalues_tree, "d_values.csv")).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Export Distribution to CSV",
                command=lambda: export_to_csv(dist_tree, "particle_distribution.csv")).pack(side=tk.LEFT, padx=5)

    
    def show_graph_window(self, x_smooth, y_smooth, xs, ys, intersections, plot_type="semi-log"):
        """Display graph in a new window with interactive features"""
        graph_window = tk.Toplevel(self)
        graph_window.title("Grain Size Distribution Curve")
        graph_window.geometry("900x700")
        graph_window.resizable(True, True)
        
        # Create figure
        fig = plt.Figure(figsize=(9, 7), dpi=100)
        ax = fig.add_subplot(111)
        
        # Set plot type
        if plot_type == "semi-log":
            ax.set_xscale("log")
            ax.set_xlabel("Particle Size (mm) - Logarithmic Scale")
        elif plot_type == "log-log":
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel("Particle Size (mm) - Logarithmic Scale")
            ax.set_ylabel("Percentage Finer (%) - Logarithmic Scale")
        else:  # simple
            ax.set_xlabel("Particle Size (mm)")
        
        ax.set_ylabel("Percentage Finer (%)")
        ax.set_title("Grain Size Distribution Curve")
        ax.grid(True, which='both', linestyle='--', alpha=0.7)
        
        # Plot data
        ax.plot(x_smooth, y_smooth, 'b-', linewidth=2, label="Grain Size Curve")
        ax.plot(xs, ys, 'ro', markersize=8, label="Data Points")
        
        # Plot horizontal lines at 10%, 30%, 60% passing through y axis
        for P in [10, 30, 60]:
            ax.axhline(y=P, color='orange', linestyle='dashed', linewidth=1)
        
        # Plot D-values
        for label, x_val in intersections.items():
            if x_val is not None:
                ax.plot(x_val, float(label[1:]), 'gD', markersize=10, 
                       label=f"{label} = {x_val:.2f} mm")
                ax.annotate(f"{label}\n{x_val:.2f} mm", 
                          xy=(x_val, float(label[1:])),
                          xytext=(10, 10), textcoords='offset points',
                          bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8),
                          arrowprops=dict(arrowstyle='->'))
        
        ax.legend(loc='lower right')
        
        # Add secondary axis with sieve numbers
        def sieve_num(x):
            for size, num in SIEVE_SIZES:
                if abs(x - size) < 0.001:
                    return num
            return ""
        
        secax = ax.secondary_xaxis('top', functions=(lambda x: x, lambda x: x))
        secax.set_xticks(xs)
        secax.set_xticklabels([sieve_num(x) for x in xs])
        secax.set_xlabel("Standard Sieve Numbers", fontsize=10, labelpad=10)
        
        # Embed plot in Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, graph_window)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add plot type selector
        plot_frame = tk.Frame(graph_window)
        plot_frame.pack(fill=tk.X, padx=5, pady=5)
        
        plot_var = tk.StringVar(value=plot_type)
        tk.Label(plot_frame, text="Plot Type:").pack(side=tk.LEFT, padx=5)
        
        for ptype in ["simple", "semi-log", "log-log"]:
            rb = tk.Radiobutton(
                plot_frame, text=ptype, variable=plot_var, value=ptype,
                command=lambda: self.controller.update_plot_type(plot_var.get())
            )
            rb.pack(side=tk.LEFT, padx=5)
        
        # Add export buttons
        button_frame = tk.Frame(graph_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        formats = [("PNG", ".png"), ("PDF", ".pdf"), ("SVG", ".svg")]
        for text, ext in formats:
            btn = tk.Button(
                button_frame, text=f"Save as {text}",
                command=lambda e=ext: self.controller.save_graph(fig, e),
                font=("Arial", 10)
            )
            btn.pack(side=tk.LEFT, padx=5)
    
    def show_coefficients_window(self, coefficients):
        """Display coefficients in a new window"""
        coeff_window = tk.Toplevel(self)
        coeff_window.title("Soil Coefficients")
        coeff_window.geometry("500x300")
        coeff_window.resizable(False, False)
        
        # Create frame
        coeff_frame = tk.Frame(coeff_window, bg="#f0f0f0")
        coeff_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add title
        title_label = tk.Label(
            coeff_frame, text="Soil Classification Coefficients", 
            font=("Arial", 16, "bold"), fg="#333399", bg="#f0f0f0"
        )
        title_label.pack(pady=10)
        
        # Add coefficients table
        tree = ttk.Treeview(coeff_frame, columns=("Coefficient", "Value"), show="headings")
        tree.heading("Coefficient", text="Coefficient")
        tree.heading("Value", text="Value")
        tree.column("Coefficient", width=250, anchor=tk.W)
        tree.column("Value", width=150, anchor=tk.CENTER)
        
        tree.insert("", tk.END, values=(
            "Coefficient of Uniformity (Cu)", 
            f"{coefficients['Cu']:.2f}" if coefficients['Cu'] else "N/A"
        ))
        tree.insert("", tk.END, values=(
            "Coefficient of Curvature (Cc)", 
            f"{coefficients['Cc']:.2f}" if coefficients['Cc'] else "N/A"
        ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add interpretation
        interp_frame = tk.Frame(coeff_frame, bg="#f0f0f0")
        interp_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        cu = coefficients['Cu']
        cc = coefficients['Cc']
        
        if cu is None or cc is None:
            interp_text = "Insufficient data for classification"
        elif cu >= 4 and 1 <= cc <= 3:
            interp_text = "Well-graded soil"
        elif cu < 4 or cc < 1 or cc > 3:
            interp_text = "Poorly-graded soil"
        else:
            interp_text = "Unable to determine grading"
        
        interp_label = tk.Label(
            interp_frame, text=f"Interpretation: {interp_text}", 
            font=("Arial", 12), bg="#f0f0f0", fg="#009999"
        )
        interp_label.pack()
        
        # Add tooltips
        ToolTip(tree, "Cu = D60/D10 - Measures the range of particle sizes\n"
                    "Cc = (D30)²/(D60×D10) - Measures the shape of the distribution\n\n"
                    "Well-graded soil: Cu ≥ 4 and 1 ≤ Cc ≤ 3\n"
                    "Poorly-graded soil: Cu < 4 or Cc < 1 or Cc > 3")

class SieveAnalysisController:
    """Controller class handling user interactions"""
    def __init__(self, root):
        self.model = SieveAnalysisModel()
        self.view = SieveAnalysisView(root, self)
        self.view.pack(fill=tk.BOTH, expand=True)
        
    def add_row(self):
        """Add a new row to the input table"""
        self.view.add_row()
        
    def calculate(self):
        """Perform calcul.ations and show results"""
        try:
            # Get total weight
            total_weight = float(self.view.total_weight_entry.get())
            if total_weight <= 0:
                raise ValueError("Total weight must be positive")
            
            # Get sieve data
            sieve_data = []
            for size_entry, number_entry, ret_entry in self.view.entries:
                size = float(size_entry.get()) if size_entry.get() else 0
                number = number_entry.get()
                retained = float(ret_entry.get()) if ret_entry.get() else 0
                
                if retained < 0:
                    raise ValueError("Retained mass cannot be negative")
                
                sieve_data.append((size, number, retained))
            
            if not sieve_data:
                raise ValueError("No sieve data entered")
            
            # Perform calculations
            self.model.calculate(total_weight, sieve_data)
            
            # Show results view
            self.view.show_results_view()
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred: {str(e)}")
    
    def show_results(self):
        """Show calculation results"""
        self.view.show_results_window(
            self.model.intersections, 
            self.model.particle_distribution
        )
    
    def show_graph(self):
        """Show grain size distribution graph"""
        self.view.show_graph_window(
            self.model.x_smooth,
            self.model.y_smooth,
            self.model.xs,
            self.model.ys,
            self.model.intersections,
            self.model.plot_type
        )
    
    def show_coefficients(self):
        """Show soil coefficients"""
        self.view.show_coefficients_window(self.model.coefficients)
    
    def show_input_view(self):
        """Show input view"""
        self.view.show_input_view()
    
    def save_data(self):
        """Save current data to file"""
        try:
            # Get data from entries
            data = {
                "total_weight": self.view.total_weight_entry.get(),
                "sieve_data": []
            }
            
            for size_entry, number_entry, ret_entry in self.view.entries:
                data["sieve_data"].append({
                    "size": size_entry.get(),
                    "number": number_entry.get(),
                    "retained": ret_entry.get()
                })
            
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                
                messagebox.showinfo("Success", f"Data saved to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {str(e)}")
    
    def load_data(self):
        """Load data from file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Clear existing entries
                for size_entry, number_entry, ret_entry in self.view.entries:
                    size_entry.destroy()
                    number_entry.destroy()
                    ret_entry.destroy()
                self.view.entries = []
                
                # Set total weight
                self.view.total_weight_entry.delete(0, tk.END)
                self.view.total_weight_entry.insert(0, data["total_weight"])
                
                # Add data rows
                for item in data["sieve_data"]:
                    self.view.add_row(
                        item["size"],
                        item["number"],
                        item["retained"]
                    )
                
                messagebox.showinfo("Success", f"Data loaded from {file_path}")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {str(e)}")
    
    def clear_inputs(self):
        """Clear all input fields"""
        for size_entry, number_entry, ret_entry in self.view.entries:
            size_entry.delete(0, tk.END)
            number_entry.delete(0, tk.END)
            ret_entry.delete(0, tk.END)
        
        self.view.total_weight_entry.delete(0, tk.END)
        messagebox.showinfo("Cleared", "All inputs have been cleared")
    
    def update_plot_type(self, plot_type):
        """Update plot type and redraw graph"""
        self.model.plot_type = plot_type
        self.show_graph()

class ToolTip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        
    def show_tip(self, event=None):
        """Display text in tooltip window"""
        # If the tooltip window is already open or there is no text to display, return
        if self.tip_window or not self.text:
            return
            
        # Get the position of the widget
        x, y, _, _ = self.widget.bbox("insert")
        # Add 25 pixels to the x and y coordinates to position the tooltip window
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create a new tooltip window
        self.tip_window = tw = tk.Toplevel(self.widget)
        # Set the window to be on top of all other windows
        tw.wm_overrideredirect(True)
        # Set the position of the tooltip window
        tw.wm_geometry(f"+{x}+{y}")
        
        # Create a label to display the text in the tooltip window
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("Arial", 10)
        )
        # Pack the label into the tooltip window
        label.pack(ipadx=1)
        
    def hide_tip(self, event=None):
        """Hide tooltip window"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sieve Analysis Tool")
    root.geometry("1000x700")
    root.resizable(True, True)
    
    # Set window icon if available
    try:
        root.iconbitmap("sieve_icon.ico")  # Provide your icon file
    except:
        pass
    
    app = SieveAnalysisController(root)
    root.mainloop()

