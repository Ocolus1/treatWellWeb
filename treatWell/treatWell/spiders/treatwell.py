import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, MoveTargetOutOfBoundsException
import time
import json
import pandas as pd

class TreatwellSpider(scrapy.Spider):
    name = "treatwell"

    def __init__(self, start_urls=None, *args, **kwargs):
        super(TreatwellSpider, self).__init__(*args, **kwargs)

        if start_urls is not None:
            self.start_urls = start_urls.split(',')
        else:
            self.start_urls = [
                "https://www.treatwell.co.uk/place/resa-beauty-salon/#serviceIds=TR1358807289,TR1358807288,TR1358807283&t=706&tt=4"]
    
        # set up the driver
        chrome_options = Options()
        chrome_options.add_argument("--headless") # comment this if you want to appreciate the sight of a possessed browser
        self.driver = webdriver.Chrome(
            executable_path="/usr/local/bin/chromedriver",  options=chrome_options)
        self.driver.maximize_window()


    # using scrapy's native parse to first scrape links on result pages
    def parse(self, response):
        # Accept cookies popup
        self.driver.get(response.url)
        cookies_button = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Accept All")]'))
        )
        cookies_button.click()

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
            '//button[@class="Button-module_button__3VGaT Button-module_primary__2jInt Button-module_sm__lk94L"]'))
        )

        # Click on button
        buttons = self.driver.find_elements(By.XPATH,
            '//button[@class="Button-module_button__3VGaT Button-module_primary__2jInt Button-module_sm__lk94L"]')

        actions = ActionChains(self.driver)

        for i in range(len(buttons)):
            if buttons[i].is_displayed():
                actions.move_to_element(buttons[i]).click().perform()
                break
            else:
                continue

        # Wait for div to appear
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
            '//div[@class="Inline-module_inline__1aHBb Button-module--button--bf18db Button-module--primaryButton--0c4e9a Inline-module_alignCenter__uIC18 Inline-module_justifyCenter__123sj"]'))
        )

        # Click on div
        div = self.driver.find_element(By.XPATH,
            '//div[@class="Inline-module_inline__1aHBb Button-module--button--bf18db Button-module--primaryButton--0c4e9a Inline-module_alignCenter__uIC18 Inline-module_justifyCenter__123sj"]')
        div.click()

        # Wait for page to load completely
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
            '//time[@class="Text-module_body__2lxF8"]'))
        )

        # Wait for page to the div to load completely
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
            '//div[@class="DayList-module_week_ec3b62"]'))
        )

        # list of the collected data
        big_list = []
        dates_skipped = []

        # Get the next button
        next_btn = self.driver.find_element(By.XPATH,
                '//button[@data-cy="CalendarNavigationNext"]')

        # Loop through the list of dates that are available
        for i in range(91):
            # waits for the dates to be available at each iteration
            # If not, it will not get all the data
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                '//time[@class="VisuallyHidden-module_visuallyHidden__3fRX1"]'))
            )
            
            # Gets the dates list 
            dates = self.driver.find_elements(By.XPATH,
                '//time[@class="VisuallyHidden-module_visuallyHidden__3fRX1"]')
            
            # Checks if the index is divisible by 7 and
            # Clicks the next button if to move to the next slide
            if i != 0 and i % 7 == 0:

                # Waits for the button to load completely before clicking on it
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, 
                    '//button[@data-cy="CalendarNavigationNext"]'))
                )
                
                # Checks if the button is dispalyed
                # It will not display on the last slide
                if next_btn.is_displayed():
                    actions.move_to_element(next_btn).click().perform()
            
            # Sleeps the process by one seconds
            time.sleep(1)

            try:
                # clicks on the date to generate the available time
                actions.move_to_element(dates[i]).click().perform()

                # Getss the time div 
                time_div = self.driver.find_element(By.XPATH,
                    '//div[@data-cy="TimeSlotList"]')

                # Checks if the time div exists
                # sometimes there is no available date for that day
                if time_div:
                    # get the the automatically selected time by default
                    time_1 = time_div.find_element(By.XPATH, 
                    '//time[@class="Text-module_captionHeavy__3H4uq"]').text

                    # Appends the first time to the big_list
                    big_list.append({dates[i].text: [time_1]})

                    # Gest the remaing times in a list
                    remaining_time = time_div.find_elements(By.XPATH, 
                    '//time[@class="Text-module_caption__1s14T TimeSlot-module_time_c0d2b8"]')

                    # Loops through the list 
                    for time_element in remaining_time:
                        time_text = time_element.text

                        # append the time to the already appended tie time above 
                        # to avoid duplicates 
                        big_list[-1][dates[i].text].append(time_text)
                else:
                    continue

            except NoSuchElementException:
                print("Time slot list not found!")
                print("Skipping this date ")
                dates_skipped.append(dates[i].text)
                continue

            except MoveTargetOutOfBoundsException:
                print("Scraping ended!")
                break

        # Flatten the list of dictionaries
        flat_list = [(key, val) for item in big_list for key, val in item.items()]

        # Create a DataFrame from the flattened list
        df = pd.DataFrame(flat_list, columns=["Date", "Time Slots"])

        # Apply a lambda function to join the list elements with a comma and a space
        df["Time Slots"] = df["Time Slots"].apply(lambda x: ", ".join(x))

        # Write the DataFrame to an Excel file
        df.to_excel("output.xlsx", index=False)   

        # Output the list of dates that were skiped 
        # because there were not availabble
        with open('skipped_list.json', 'w') as f:
            json.dump(dates_skipped, f, ensure_ascii=False)


    def closed(self, reason):
        self.driver.quit()

       