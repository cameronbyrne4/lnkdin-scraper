from linkedin_scraper import Person, actions
from selenium import webdriver
import os

def test_linkedin_scraper():
    # Initialize the Chrome driver
    driver = webdriver.Chrome()
    
    try:
        # Login to LinkedIn
        email = input("Enter your LinkedIn email: ")
        password = input("Enter your LinkedIn password: ")
        actions.login(driver, email, password)
        
        # Test scraping a public profile
        # Using a well-known public profile as an example
        test_profile = "https://www.linkedin.com/in/williamhgates"
        person = Person(test_profile, driver=driver)
        
        # Print the scraped information
        print("\nScraped Profile Information:")
        print(f"Name: {person.name}")
        print(f"About: {person.about}")
        print(f"Job Title: {person.job_title}")
        print(f"Company: {person.company}")
        
        # Print experiences
        print("\nExperiences:")
        for experience in person.experiences:
            print(f"- {experience.position_title} at {experience.institution_name}")
            if experience.description:
                print(f"  Description: {experience.description}")
            if experience.from_date and experience.to_date:
                print(f"  Duration: {experience.from_date} to {experience.to_date}")
            else:
                print(f"  Duration: {experience.from_date} - Present")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_linkedin_scraper() 