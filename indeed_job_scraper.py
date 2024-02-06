import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
import traceback
from datetime import datetime, timedelta

class IndeedJobScraper:
    def __init__(self):
        self.job_data_list = []
        self.processed_job_links = set()
        
        self.conn = None

        self.connect_to_database() 
        self.create_jobs_table()

        options = Options()
        options.headless = True
        options.add_argument("--window-size=3,2")

        self.driver = webdriver.Chrome(options=options)

    def connect_to_database(self):
        try:
            self.conn = sqlite3.connect("scrappy.db")
            print("Connected to the database")
        except sqlite3.Error as e:
            print(f"Error: {e}")

    def create_jobs_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indeed_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    title_search TEXT,
                    company TEXT,
                    job_link TEXT,
                    location TEXT,
                    location_search TEXT,
                    date_of_post DATE,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            print("Table 'indeed_jobs' created successfully.")
        except sqlite3.Error as e:
            print(f"Error: {e}")

    def extract_job_details(self, card):
        try:
            job_link_element = card.find_element(By.CSS_SELECTOR, 'h2.jobTitle span')
            job_link = job_link_element.find_element(By.XPATH, './parent::a').get_attribute('href')
        except:
            job_link = "N/A"
        try:
            title_element = WebDriverWait(card, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.jobTitle span'))
            )
            title = title_element.text
        except:
            title = "N/A"
        try:
            company_element = WebDriverWait(card, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="company-name"]'))
            )
            company = company_element.text
        except:
            company = "N/A"
        try:
            location_element = WebDriverWait(card, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="text-location"]'))
            )
            location = location_element.text
        except:
            location = "N/A"

        try:
            date_element = WebDriverWait(card, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="myJobsStateDate"]'))
            )
            date_text = date_element.text
            date = date_text.replace("Employer", "").strip()
            date = date.replace("Posted", "").strip()
            date = convert_date(date)
        except:
            date = None

        return {
            "Title": title,
            "Company": company,
            "Job Link": job_link,
            "Location": location,
            "Date": date,
        }
    
    def scrape_jobs(self, designation, location, num_pages, job_type, locale="de"):
        job_type = self.select_job_type(job_type)
        self.locale = locale
        self.location = location
        self.title = designation
        language = "in" if locale == "in" else "de"

        try:
            for page in range(0, num_pages):
                start_index = page * 10  # Each page displays 10 results, adjust as needed
                url = f"https://{self.locale}.indeed.com/jobs?q={designation}&l={location}&start={start_index}&fromage=14&sort=date&lang={language}&sc=0kf%3Ajt({job_type})%3B"
                
                print(url)
                self.driver.get(url)
                time.sleep(7)  # Wait for the page to load (you might need to adjust this time)

                job_cards = self.driver.find_elements(By.CSS_SELECTOR, 'div.job_seen_beacon')
                print(f"\nPage {page + 1} - Number of job cards found: {len(job_cards)}")

                for card in job_cards:
                    job_data = self.extract_job_details(card)
                    job_link = job_data.get("Job Link", "")

                    # Check if the job link is not in the set to avoid duplicates
                    if job_link not in self.processed_job_links:
                        self.processed_job_links.add(job_link)

                        # Save job data to the database
                        if job_data["Date"] is not None:
                            self.job_data_list.append(job_data)
                            self.save_to_database(job_data)

                # Break the loop if the number of job cards is less than 15
                if len(job_cards) < 15:
                    break

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()


        finally:
            print("Scraping complete.")
            self.driver.quit()

    def select_job_type(self, choice):
       
        try:
            choice = int(choice)
        except ValueError:
            print("Invalid choice. Defaulting to full-time.")
            return "fulltime"

        if choice == 1:
            job_type = "fulltime"
        elif choice == 2:
            job_type = "permanent"
        elif choice == 3:
            job_type = "parttime"
        elif choice == 4:
            job_type = "subcontract"
        else:
            print("Invalid choice. Defaulting to full-time.")
            job_type = "fulltime"

        return job_type
    
    def save_to_json(self, output_file_path="job_data.json"):
        with open(output_file_path, "w", encoding="utf-8") as json_file:
            json.dump(self.job_data_list, json_file, ensure_ascii=False, indent=2)
        print(f"Data saved to {output_file_path}.")

    def save_to_database(self, job_data):
        try:
            cursor = self.conn.cursor()
            # Check if the job link already exists in the 'indeed_jobs' table
            cursor.execute("SELECT id FROM indeed_jobs WHERE title = ? AND company = ? AND date_of_post = ?", (job_data["Title"], job_data["Company"], job_data["Date"]))
            existing_job_id = cursor.fetchone()
            if(job_data['Title']):
                if not existing_job_id:
                    # Job link does not exist, insert the new job data
                    cursor.execute("""
                        INSERT INTO indeed_jobs (title, company, job_link, location, date_of_post, title_search, location_search)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (job_data["Title"], job_data["Company"], job_data["Job Link"], job_data["Location"], job_data["Date"], self.title, self.location))

                    self.conn.commit()
                    print(f"Job data saved to the database.")
            else:
                print(f"Job with link '{job_data['Job Link']}' already exists in the database.")

        except sqlite3.Error as e:
            print(f"Error: {e}")

def convert_date(date_str):
    if "Aktiv" in date_str:
        days_ago = int(date_str.split("Aktiv: vor ")[1].split(" ")[0])
        date = None
    elif "Vor" in date_str:
        days_ago = int(date_str.split("Vor ")[1].split(" ")[0])
        date = datetime.today() - timedelta(days=days_ago)
    elif "Heute" in date_str:
        date = datetime.today()
    else:
        date = None
    
    if date:
        return date.strftime("%Y-%m-%d")
    else:
        return None



def load_config(file_path):
    abs_file_path = os.path.abspath(file_path)
    try:
        with open(abs_file_path, "r") as json_file:
            config = json.load(json_file)
        return config
    except FileNotFoundError:
        print(f"Config file {abs_file_path} not found. Using default values.")
        return {}

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Scrape Indeed job data")
    # parser.add_argument("--title", required=True, help="Job title to search for")
    # parser.add_argument("--location", required=True, help="Location to search for jobs")
    # parser.add_argument("--pages", type=int, default=2, help="Number of pages to scrape (default is 2)")
    # parser.add_argument("--job_type", type=int, default=0, help="Type of job (default is 1)")
    # parser.add_argument("--locale", default="de", help="Localization")

    # args = parser.parse_args()

    scraper = IndeedJobScraper()

    # job_type = args.job_type
    # for i in range(1, 5):
    #     print(f"{i}: {scraper.select_job_type(i)}")
    
    # if(args.job_type == 0):
    #     job_type = input("Please Select any Job Type: ")
    
    config = load_config("config.json")
    print(config)

    scraper.scrape_jobs(config['title'], config['location'], int(config['pages']), config['job_type'], config['locale'])
    scraper.save_to_json()    
