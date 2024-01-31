from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# Function to extract job details from a job card
def extract_job_details(card):
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

# Function to select job type based on user input
def select_job_type():
    print("Select the type of job:")
    print("1. Full-time")
    print("2. Permanent Position")
    print("3. Part-time")
    print("4. Freelance Work")

    choice = input("Enter the number corresponding to your choice: ")
    job_type = ""
    if choice == "1":
        job_type = "fulltime"
    elif choice == "2":
        job_type = "permanent"
    elif choice == "3":
        job_type = "parttime"
    elif choice == "4":
        job_type = "subcontract"
    else:
        print("Invalid choice. Defaulting to full-time.")
        job_type = "fulltime"

    return job_type

locale = "de"
designation = input("Enter the job designation: ")
location = input("Enter the location: ")

num_pages = int(input("Enter the number of pages to scrape: "))
language = "de"
job_type = select_job_type()
# Set up Selenium with a headless browser
options = Options()
options.headless = True
driver = webdriver.Chrome(options=options)


try:
    job_data_list = []
    processed_job_links = set()  # Set to keep track of processed job links

    for page in range(0, num_pages):
        start_index = page * 10  # Each page displays 10 results, adjust as needed
        url = f"https://{locale}.indeed.com/jobs?q={designation}&l={location}&start={start_index}&fromage=14&sort=date&lang={language}&sc=0kf%3Ajt({job_type})%3B"

        # url = f"https://{locale}.indeed.com/jobs?q=Software+Developer&l=Surat"
        print(url)
        driver.get(url)
        time.sleep(7)  # Wait for the page to load (you might need to adjust this time)

        job_cards = driver.find_elements(By.CSS_SELECTOR, 'div.job_seen_beacon')
        print(f"\nPage {page + 1} - Number of job cards found: {len(job_cards)}")

        for card in job_cards:
            job_data = extract_job_details(card)
            job_link = job_data.get("Job Link", "")

            # Check if the job link is not in the set to avoid duplicates
            if job_link not in processed_job_links:
                processed_job_links.add(job_link)
                job_data_list.append(job_data)

                # print(f"Title: {job_data['Title']}")
                # print(f"Company: {job_data['Company']}")
                # print(f"Job Link: {job_data['Job Link']}")
                # print(f"Location: {job_data['Location']}")
                # print(f"Date: {job_data['Date']}")
                # print("\n" + "=" * 50 + "\n")

        # Break the loop if the number of job cards is less than 15
        if len(job_cards) < 15:
            break

except Exception as e:
    print(f"Error: {e}")

finally:
    # driver.quit()
    print("ok")

output_file_path = "job_data.json"
with open(output_file_path, "w", encoding="utf-8") as json_file:
    json.dump(job_data_list, json_file, ensure_ascii=False, indent=2)
exit


# print("Job Data List:")
# print(job_data_list)