import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from threading import Thread
from functools import partial
from indeed_job_scraper import IndeedJobScraper 
from indeed_job_database import IndeedJobDatabaseManager
import subprocess

import json
import os

class IndeedJobScraperGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Indeed Job Scraper")
        self.master.geometry("600x400")

        self.default_config = self.load_config("config.json")
        self.title_label = ttk.Label(self.master, text="Job Title:")
        self.title_entry = ttk.Entry(self.master, width=30)
        self.title_entry.insert(0, self.default_config["title"])

        self.location_label = ttk.Label(self.master, text="Location:")
        self.location_entry = ttk.Entry(self.master, width=30)
        self.location_entry.insert(0, self.default_config["location"])
        self.location_note = ttk.Label(self.master, text="Leaving this empty will search through the entire country", foreground="gray")

        self.pages_label = ttk.Label(self.master, text="Number of Pages:")
        self.pages_entry = ttk.Entry(self.master, width=30)
        self.pages_entry.insert(0, self.default_config["pages"])

        self.job_type_label = ttk.Label(self.master, text="Job Type:")
        self.job_type_entry = tk.StringVar(value=self.default_config["job_type"])
        self.job_type_dropdown = ttk.Combobox(self.master, textvariable=self.job_type_entry, values=["Fulltime", "Permanent", "Parttime", "Subcontract"], state="readonly")

        self.locale_label = ttk.Label(self.master, text="Locale:")
        self.locale_entry = ttk.Entry(self.master, width=30)
        self.locale_entry.insert(0, self.default_config["locale"])
        self.locale_note = ttk.Label(self.master, text="Examples: nl, de, in", foreground="gray")

        self.switched_by_label = ttk.Label(self.master, text="Switched by:")
        self.switched_by_entry = tk.StringVar(value="Employer")
        self.switched_by_dropdown = ttk.Combobox(self.master, textvariable=self.switched_by_entry, values=["All", "Employer", "Recruiter"], state="readonly")

        self.run_button = ttk.Button(self.master, text="Fetch Data", command=self.run_script)

        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.title_entry.grid(row=0, column=1, padx=10, pady=10)

        self.location_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.location_entry.grid(row=1, column=1, padx=10, pady=10)
        self.location_note.grid(row=2, column=1, padx=10, pady=0, sticky="w")

        self.pages_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.pages_entry.grid(row=3, column=1, padx=10, pady=10)

        self.job_type_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.job_type_dropdown.grid(row=4, column=1, padx=10, pady=10)

        self.locale_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.locale_entry.grid(row=5, column=1, padx=10, pady=10)
        self.locale_note.grid(row=6, column=1, padx=10, pady=0, sticky="w")

        self.switched_by_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.switched_by_dropdown.grid(row=7, column=1, padx=10, pady=10)

        self.run_button = ttk.Button(self.master, text="Fetch Data", command=self.run_script)
        self.export_button = ttk.Button(self.master, text="Export Database", command=self.export_database)
        self.run_button.grid(row=9, column=0, padx=10, pady=10, sticky="we")
        self.export_button.grid(row=9, column=1, padx=10, pady=10, sticky="we")


    def export_database(self):
            title = self.title_entry.get()
            location = self.location_entry.get()

            try:
                # Instantiate the IndeedJobDatabaseManager
                database_manager = IndeedJobDatabaseManager()

                # Execute export command
                database_manager.export_data(location, title)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export database: {e}")

    def clear_database(self):
            try:
                # Instantiate the IndeedJobDatabaseManager
                database_manager = IndeedJobDatabaseManager()

                # Clear the database
                database_manager.delete_data("","")
                messagebox.showinfo("Success", "Database cleared successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear database: {e}")

    def run_script(self):
        title = self.title_entry.get()
        location = self.location_entry.get()
        pages = self.pages_entry.get()
        job_type = self.job_type_entry.get()
        locale = self.locale_entry.get()
        switched_by = self.switched_by_entry.get()
        
        self.update_config_callback()

        scraper = IndeedJobScraper()
        scraper.scrape_jobs(title, location, int(pages), job_type, locale, switched_by)


    def load_config(self, file_path):
        abs_file_path = os.path.abspath(file_path)
        if not os.path.exists(abs_file_path):  # Check if config file exists
            self.create_default_config(abs_file_path)
        try:
            with open(abs_file_path, "r") as json_file:
                config = json.load(json_file)
            return config
        except FileNotFoundError:
            messagebox.showwarning("Warning", f"Config file {abs_file_path} not found. Using default values.")
            return {}
        
    def create_default_config(self, file_path):
        default_config = {
            "title": "web",
            "location": "Berlin",
            "pages": "2",
            "job_type": "Fulltime",
            "locale": "de"
        }
        with open(file_path, "w") as json_file:
            json.dump(default_config, json_file, indent=4)

    def update_config(self, file_path, new_config):
        try:
            with open(file_path, "w") as json_file:
                json.dump(new_config, json_file, indent=2)
            messagebox.showinfo("Success", "Config file updated, now scrapping the data...")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update config file: {e}")

    def update_config_callback(self):
            new_config = {
                "title": self.title_entry.get(),
                "location": self.location_entry.get(),
                "pages": self.pages_entry.get(),
                "job_type": self.job_type_entry.get(),
                "locale": self.locale_entry.get(),
            }
            selected_config_file = "config.json"  

            self.update_config(selected_config_file, new_config)

if __name__ == "__main__":
    root = tk.Tk()
    app = IndeedJobScraperGUI(root)
    root.mainloop()