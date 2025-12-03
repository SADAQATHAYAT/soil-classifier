import tkinter as tk
from tkinter import ttk, messagebox
from SieveAnalysisApp import SieveAnalysisController
from uscs import USCS_Classifier
import os
import sys

class IntegratedSoilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Soil Analysis Tool")
        self.root.geometry("400x300")
        self.sieve_data = None  # To store sieve analysis results
        self.create_main_interface()

    def create_main_interface(self):
        frame = ttk.Frame(self.root, padding=20,style='Accent.TButton')
        frame.pack(expand=True)

        ttk.Label(frame, text="Unified Soil Analysis Tool", font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Button(frame, text="1. Perform Sieve Analysis",style='Accent.TButton', command=self.run_sieve_analysis).pack(pady=10)
        ttk.Button(frame, text="2. Classify Soil (Manual Entry)",style='Accent.TButton', command=self.run_uscs_manual).pack(pady=10)
        ttk.Button(frame, text="3. Classify Soil (Import from Sieve)",style='Accent.TButton', command=self.run_uscs_imported).pack(pady=10)

    def run_sieve_analysis(self):
        """Run the full Sieve Analysis tool in its own window"""
        sieve_window = tk.Toplevel(self.root)
        sieve_window.title("Sieve Analysis Tool")
        
        # Create and pack the full Sieve Analysis application
        sieve_app = SieveAnalysisController(sieve_window)
        
        # Store a reference to the controller for later access
        self.sieve_controller = sieve_app
        
        # Bind to window close to capture the data before destruction
        sieve_window.protocol("WM_DELETE_WINDOW", lambda: self.on_sieve_close(sieve_window))

    def on_sieve_close(self, window):
        """Handle sieve analysis window closing"""
        if hasattr(self, 'sieve_controller'):
            # Store the model data before closing
            self.sieve_data = {
                'model': self.sieve_controller.model,
                'is_valid': self.sieve_controller.model.validate_results()
            }
        window.destroy()

    def run_uscs_manual(self):
        """Run the full USCS Classifier in its own window with manual entry"""
        uscs_window = tk.Toplevel(self.root)
        uscs_window.title("USCS Classifier (Manual Entry)")
        
        # Create and pack the full USCS Classifier application
        USCS_Classifier(uscs_window)

    def run_uscs_imported(self):
        """Run USCS Classifier with data imported from sieve analysis"""
        if not hasattr(self, 'sieve_data') or not self.sieve_data or not self.sieve_data['is_valid']:
            messagebox.showerror("Error", "Please perform a valid Sieve Analysis first")
            return

        uscs_window = tk.Toplevel(self.root)
        uscs_window.title("USCS Classifier (Imported from Sieve)")
        
        # Create the USCS Classifier
        uscs_app = USCS_Classifier(uscs_window)
        
        # Populate the fields with sieve analysis data
        self.populate_uscs_fields(uscs_app)

    def populate_uscs_fields(self, uscs_app):
        """Populate USCS fields with sieve analysis data"""
        model = self.sieve_data['model']
        pd = model.particle_distribution
        dvals = model.intersections
        coeffs = model.coefficients

        # Set particle distribution percentages
        uscs_app.boulders.set(pd.get("Boulders (> 300 mm)", 0.0))
        uscs_app.cobbles.set(pd.get("Cobbles (75 - 300 mm)", 0.0))
        uscs_app.gravel.set(pd.get("Gravel (4.75 - 75 mm)", 0.0))
        uscs_app.sand.set(pd.get("Sand (0.075 - 4.75 mm)", 0.0))
        uscs_app.fines.set(pd.get("Fines (< 0.075 mm)", 0.0))

        # Set D-values
        uscs_app.d10.set(dvals.get("D10", 0.0))
        uscs_app.d30.set(dvals.get("D30", 0.0))
        uscs_app.d60.set(dvals.get("D60", 0.0))

        # Set coefficients
        uscs_app.cu.set(coeffs.get("Cu", 0.0))
        uscs_app.cc.set(coeffs.get("Cc", 0.0))

        # Update the total percentage display
        uscs_app.update_total_percentage()


if __name__ == "__main__":
    root = tk.Tk()
    app = IntegratedSoilApp(root)
    root.mainloop()