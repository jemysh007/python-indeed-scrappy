import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
load_dotenv()

class IndeedJobScraper:
    def __init__(self):
        self.job_data_list = []
        self.processed_job_links = set()
        
        self.conn = None
        self.db = None

        self.connect_to_database() 
        self.create_jobs_table()

        # Set up Selenium with a headless browser
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

    def connect_to_database(self):
        try:
            self.conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),  
                password=os.getenv('DB_PASSWORD'), 
            )
          
            self.initDatabase()

            if self.conn.is_connected():
                print("Connected to the database")
        except Error as e:
            print(f"Error: {e}")

    def initDatabase(self):
        # Create 'scrappy' database if not exists

        db_name = os.getenv('DB_NAME', 'scrappy')

        try:
            cursor = self.conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            self.conn.commit()

            print("Database created successfully.")
        except Error as e:
            print(f"Error: {e}")

        # Use 'scrappy' database
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"USE {db_name}")
            self.conn.commit()
            print("Using database 'scrappy'.")
        except Error as e:
            print(f"Error: {e}")

    def create_jobs_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indeed_jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255),
                    company VARCHAR(255),
                    job_link TEXT,
                    location VARCHAR(255),
                    date_of_post VARCHAR(255),
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            print("Table 'indeed_jobs' created successfully.")
        except Error as e:
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
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.date'))
            )
            date_text = date_element.text
            date = date_text.replace("Employer", "").strip()
            date = date_text.replace("Posted", "").strip()
        except:
            date = "N/A"

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
                        self.job_data_list.append(job_data)

                        # Save job data to the database
                        self.save_to_database(job_data)

                # Break the loop if the number of job cards is less than 15
                if len(job_cards) < 15:
                    break

        except Exception as e:
            print(f"Error: {e}")

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
            cursor.execute("SELECT id FROM indeed_jobs WHERE title = %s AND company = %s AND date_of_post = %s", (job_data["Title"], job_data["Company"], job_data["Date"]))
            existing_job_id = cursor.fetchone()
            if(job_data['Title']):
                if not existing_job_id:
                    # Job link does not exist, insert the new job data
                    cursor.execute("""
                        INSERT INTO indeed_jobs (title, company, job_link, location, date_of_post)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (job_data["Title"], job_data["Company"], job_data["Job Link"], job_data["Location"], job_data["Date"]))

                    self.conn.commit()
                    print(f"Job data saved to the database.")
            else:
                print(f"Job with link '{job_data['Job Link']}' already exists in the database.")

        except Error as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Indeed job data")
    parser.add_argument("--title", required=True, help="Job title to search for")
    parser.add_argument("--location", required=True, help="Location to search for jobs")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages to scrape (default is 2)")
    parser.add_argument("--job_type", type=int, default=0, help="Type of job (default is 1)")
    parser.add_argument("--locale", default="de", help="Localization")

    args = parser.parse_args()

    scraper = IndeedJobScraper()

    job_type = args.job_type
    for i in range(1, 5):
        print(f"{i}: {scraper.select_job_type(i)}")
    
    if(args.job_type == 0):
        job_type = input("Please Select any Job Type: ")
    
    scraper.scrape_jobs(args.title, args.location, args.pages, job_type, args.locale)
    scraper.save_to_json()    
        
    

    
