import logging
import os
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


logger = logging.getLogger(__name__)


FRONTEND_HOST = os.environ['FRONTEND_HOST']
BOT_USERNAME = os.environ['BOT_USERNAME']
BOT_PASSWORD = os.environ['BOT_PASSWORD']


def main():
    logging.basicConfig(level=logging.INFO)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    while True:
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Open front page
            logger.info("Opening front page...")
            
            driver.get(FRONTEND_HOST)
            time.sleep(random.uniform(1, 3))
            
            # Click Login
            logger.info("Navigating to login page...")
            
            login_button = driver.find_element("link text", "Login")
            
            login_button.click()
            time.sleep(random.uniform(1, 3))

            # Enter credentials
            logger.info("Logging in...")
            
            assert driver.current_url == f"{FRONTEND_HOST}/login.php"
            
            username_field = driver.find_element("name", "username")
            password_field = driver.find_element("name", "password")
            login_button = driver.find_element("xpath", "//input[@type='submit']")
            
            username_field.send_keys(BOT_USERNAME)
            password_field.send_keys(BOT_PASSWORD)
            
            login_button.click()
            time.sleep(random.uniform(1, 3))

            # Fill out order form
            logger.info("Submitting order...")
            
            assert driver.current_url == f"{FRONTEND_HOST}/order.php"
            
            product_field = driver.find_element("name", "product")
            quantity_field = driver.find_element("name", "quantity")
            address_field = driver.find_element("name", "address")
            notes_field = driver.find_element("name", "notes")
            place_order_button = driver.find_element("xpath", "//input[@type='submit']")
            
            product_field.send_keys("Corporate Gadget")
            quantity_field.send_keys("10")
            address_field.send_keys("123 Corporate Blvd")
            notes_field.send_keys("Please deliver between 9am-5pm.")
            
            place_order_button.click()
            time.sleep(random.uniform(1, 3))

        except Exception as e:
            logger.exception(f"An error occurred while submitting order.")

        finally:
            driver.quit()

        # Wait for a minute before placing the next order
        time.sleep(60)


if __name__ == "__main__":
    main()