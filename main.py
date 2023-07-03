import os
import time
import mysql.connector
import logging
from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Establish a connection to the MySQL database
try:
    cnx = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="darazdata"
    )
except mysql.connector.Error as err:
    logging.error("Failed to connect to MySQL database: %s", err)
    exit(1)

# Create a cursor to execute SQL queries
cursor = cnx.cursor()

# Execute a SQL query to create the table
create_table_query = """
CREATE TABLE IF NOT EXISTS laptop_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255),
    price VARCHAR(50),
    original_price VARCHAR(50),
    discount_percentage VARCHAR(10),
    rating FLOAT,
    reviews INT
)
"""

try:
    cursor.execute(create_table_query)
except mysql.connector.Error as err:
    logging.error("Failed to create table: %s", err)
    cursor.close()
    cnx.close()
    exit(1)


def my_bot():
    # Configure Selenium options
    drivers_directory = r"D:"
    os.environ['PATH'] += os.pathsep + drivers_directory
    options = Options()
    options.add_argument('--window-size=1920,1080')

    try:
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.daraz.pk/laptops/?spm=a2a0e.home.cate_7.5.24ad4076CkJ0SP")  # actual URL of daraz.px laptop categories

        while True:
            # Find all the laptop listing elements
            listing_elements = driver.find_elements(By.XPATH, "//div[@class='box--pRqdD']")

            # Iterate over each listing element
            for listing_element in listing_elements:
                try:
                    # Extract the product name
                    product_name_element = listing_element.find_element(By.XPATH, ".//div[@class='title--wFj93']/a")
                    product_name = product_name_element.get_attribute("title")

                    # Extract the price
                    price_element = listing_element.find_element(By.XPATH,
                                                                 ".//div[@class='price--NVB62']/span[@class='currency--GVKjl']")
                    price = price_element.text

                    # Extract the original price (if available)
                    original_price_elements = listing_element.find_elements(By.XPATH,
                                                                            ".//div[@class='priceExtra--ocAYk']/span[@class='origPrice--AJxRs']/del[@class='currency--GVKjl']")
                    original_price = original_price_elements[0].text if original_price_elements else None

                    # Extract the discount percentage (if available)
                    discount_elements = listing_element.find_elements(By.XPATH,
                                                                      ".//div[@class='priceExtra--ocAYk']/span[@class='discount--HADrg']")
                    discount_percentage = discount_elements[0].text if discount_elements else None

                    # Extract the rating
                    rating_element = listing_element.find_element(By.XPATH, ".//div[@class='rating--ZI3Ol rate--DCc4j']")
                    rating = rating_element.get_attribute("class").split()[-1].split("-")[-1]

                    # Extract the number of reviews
                    reviews_element = listing_element.find_element(By.XPATH, ".//span[@class='rating__review--ygkUy']")
                    reviews = int(reviews_element.text.strip("()"))

                    # Insert the scraped data into the database
                    insert_query = """
                    INSERT INTO laptop_data (product_name, price, original_price, discount_percentage, rating, reviews)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    insert_values = (product_name, price, original_price, discount_percentage, rating, reviews)

                    try:
                        cursor.execute(insert_query, insert_values)
                        cnx.commit()  # Commit the changes after each insertion (optional)
                    except mysql.connector.Error as err:
                        logging.error("Failed to insert data into the database: %s", err)

                    # Print the extracted information
                    logging.info("Product Name: %s", product_name)
                    logging.info("Price: %s", price)
                    logging.info("Original Price: %s", original_price)
                    logging.info("Discount Percentage: %s", discount_percentage)
                    logging.info("Rating: %s", rating)
                    logging.info("Number of Reviews: %s", reviews)
                    logging.info("---")  # Separator between listings

                except (NoSuchElementException, IndexError) as err:
                    logging.error("Error occurred while scraping a listing element: %s", err)

            # Check if there is a next page
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//li[@title='Next Page']/a[@class='ant-pagination-item-link']"))
            )

            # Click the "Next Page" button
            next_button.click()

            # Delay to allow the next page to load
            time.sleep(10)

    except (WebDriverException, Exception) as err:
        logging.error("Error occurred while executing Selenium script: %s", err)

    finally:
        # Close the Selenium driver
        driver.quit()

        # Close the cursor and database connection
        cursor.close()
        cnx.close()


