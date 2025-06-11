from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
from datetime import datetime
import time
import json
import re

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

def test_linkedin_scraper():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    
    # Initialize the Chrome driver with options
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Get credentials from environment variables
        email = os.getenv('LINKEDIN_EMAIL')
        password = os.getenv('LINKEDIN_PASSWORD')
        
        if not email or not password:
            print("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
            return
            
        # Login to LinkedIn
        actions.login(driver, email, password)
        
        # Wait a bit for the page to load
        time.sleep(5)
        
        # Test scraping a public profile
        # Using a well-known public profile as an example
        test_profile = "https://www.linkedin.com/in/roy-lee-goat/"
        person = Person(test_profile, driver=driver)
        
        # Create a dictionary to store all the data
        alumni_data = {
            "name": person.name,
            "linkedin_url": test_profile,
            "picture_url": person.picture if hasattr(person, 'picture') else None,
            "bio": clean_text(person.about),
            "role": person.job_title,
            "companies": [clean_company_name(exp.institution_name) for exp in person.experiences],
            "current_location": None,  # Will be set from most recent experience
            "has_linkedin": True,
            "scraped": True,
            "manually_verified": False,
            "created_at": datetime.now().isoformat(),
            "experiences": []
        }
        
        # Process experiences and extract location information
        for experience in person.experiences:
            # Get location from experience if available
            location = None
            if hasattr(experience, 'location'):
                location = experience.location
            
            # For the first (most recent) experience, set it as current location
            if not alumni_data["current_location"] and location:
                alumni_data["current_location"] = location
            
            # Add experience to the list
            experience_data = {
                "position": experience.position_title,
                "company": clean_company_name(experience.institution_name),
                "location": location,
                "duration": f"{experience.from_date} - Present" if not experience.to_date else f"{experience.from_date} to {experience.to_date}",
                "description": clean_text(experience.description) if experience.description else None
            }
            alumni_data["experiences"].append(experience_data)
        
        # Print the scraped information in a structured way
        print("\nScraped Profile Information:")
        print(f"Name: {alumni_data['name']}")
        print(f"LinkedIn URL: {alumni_data['linkedin_url']}")
        if alumni_data['picture_url']:
            print(f"Picture URL: {alumni_data['picture_url']}")
        print(f"Bio: {alumni_data['bio']}")
        print(f"Current Role: {alumni_data['role']}")
        print(f"Current Location: {alumni_data['current_location'] or 'Not specified'}")
        
        print("\nCompanies:")
        for company in alumni_data['companies']:
            print(f"- {company}")
        
        print("\nCareer History:")
        for exp in alumni_data['experiences']:
            print(f"\nPosition: {exp['position']}")
            print(f"Company: {exp['company']}")
            if exp['location']:
                print(f"Location: {exp['location']}")
            print(f"Duration: {exp['duration']}")
            if exp['description']:
                print(f"Description: {exp['description']}")
        
        # Print metadata
        print("\nMetadata:")
        print(f"Scraped: {alumni_data['scraped']}")
        print(f"Manually Verified: {alumni_data['manually_verified']}")
        print(f"Created At: {alumni_data['created_at']}")
        
        # Save to JSON file
        # Create a filename based on the person's name
        filename = f"linkedin_data_{sanitize_filename(alumni_data['name'])}.json"
        
        # Save the data to a JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(alumni_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nData saved to {filename}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_linkedin_scraper() 