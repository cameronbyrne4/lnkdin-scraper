from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from datetime import datetime
import time
import json
import re
import random

def sanitize_filename(name):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', name)

def clean_text(text):
    if not text:
        return None
    
    # Split by newlines
    lines = text.split('\n')
    
    # Clean and deduplicate lines
    seen = set()
    unique_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip if this line is a duplicate
        if line in seen:
            continue
            
        # Skip if this line is a duplicate with different date format
        # (e.g., "Sep 2024 - Nov 2024 · 3 mos" vs "Sep 2024 to Nov 2024 · 3 mos")
        is_duplicate_date = False
        if '·' in line and any(char in line for char in ['-', 'to']):
            # Extract the date part and duration
            parts = line.split('·')
            if len(parts) == 2:
                date_part = parts[0].strip()
                duration = parts[1].strip()
                # Check if we've seen a similar date with different format
                for seen_line in seen:
                    if '·' in seen_line and duration in seen_line:
                        is_duplicate_date = True
                        break
        
        if not is_duplicate_date:
            seen.add(line)
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def clean_company_name(company):
    # Remove employment type (e.g., "· Full-time", "· Part-time")
    return re.sub(r'\s*·\s*(Full-time|Part-time|Contract|Internship|Self-employed|Freelance)$', '', company)

def random_human_delay(min_sec=2, max_sec=5):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def random_human_scroll_and_mouse(driver):
    # Random scroll
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(random.randint(2, 5)):
        scroll_to = random.randint(0, scroll_height)
        driver.execute_script(f"window.scrollTo(0, {scroll_to});")
        time.sleep(random.uniform(0.5, 1.5))
    # Random mouse movement
    try:
        action = ActionChains(driver)
        for _ in range(random.randint(2, 5)):
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            action.move_by_offset(x, y).perform()
            time.sleep(random.uniform(0.2, 0.7))
            action.move_by_offset(-x, -y).perform()
    except Exception:
        pass

def scrape_linkedin_profile(url, email, password):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        actions.login(driver, email, password)
        random_human_delay(3, 7)
        driver.get(url)
        random_human_delay(3, 7)
        random_human_scroll_and_mouse(driver)
        person = Person(url, driver=driver)
        alumni_data = {
            "name": person.name,
            "linkedin_url": url,
            "picture_url": person.picture if hasattr(person, 'picture') else None,
            "bio": clean_text(person.about),
            "role": person.job_title,
            "companies": [clean_company_name(exp.institution_name) for exp in person.experiences],
            "current_location": None,
            "has_linkedin": True,
            "scraped": True,
            "manually_verified": False,
            "created_at": datetime.now().isoformat(),
            "experiences": []
        }
        for experience in person.experiences:
            location = getattr(experience, 'location', None)
            if not alumni_data["current_location"] and location:
                alumni_data["current_location"] = location
            experience_data = {
                "position": experience.position_title,
                "company": clean_company_name(experience.institution_name),
                "location": location,
                "duration": f"{experience.from_date} - Present" if not experience.to_date else f"{experience.from_date} to {experience.to_date}",
                "description": clean_text(experience.description) if experience.description else None
            }
            alumni_data["experiences"].append(experience_data)
        print(f"Scraped: {alumni_data['name']} ({url})")
        return alumni_data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
    finally:
        driver.quit()

def main():
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    if not email or not password:
        print("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
        return
    linkedin_urls = [
        "https://www.linkedin.com/in/roy-lee-goat/",
        "https://www.linkedin.com/in/williamhgates",
        "https://www.linkedin.com/in/cameronbyrne00"
        # Add more URLs here
    ]
    mega_data = []
    for url in linkedin_urls:
        data = scrape_linkedin_profile(url, email, password)
        if data:
            mega_data.append(data)
        random_human_delay(4, 9)
    with open("alumni_mega.json", "w", encoding="utf-8") as f:
        json.dump(mega_data, f, indent=2, ensure_ascii=False)
    print("\nAll data saved to alumni_mega.json")

if __name__ == "__main__":
    main() 