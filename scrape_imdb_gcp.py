import time
import random
import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, TimeoutException, StaleElementReferenceException

# Selenium configuration
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

# List of common User-Agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

# Randomly select a User-Agent from the list
options.add_argument(f"user-agent={random.choice(user_agents)}")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# Connect to Cloud SQL Server
conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=<your-server>;'
    r'DATABASE=<your-database>;'
    r'UID=<your-username>;'
    r'PWD=<your-password>;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Reconnect function to reconnect when the connection is lost
def reconnect():
    while True:
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            print("Reconnected successfully")
            return conn, cursor
        except pyodbc.OperationalError as e:
            print("Connection error, retrying...")
            time.sleep(5)  

# Check and create table if it does not exist in SQL Server
create_table_query = '''
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'Movies'
)
BEGIN
    CREATE TABLE Movies (
        Title NVARCHAR(255),
        Year INT,
        Duration NVARCHAR(10),
        MPAA NVARCHAR(10),
        Genres NVARCHAR(255),
        IMDb_Rating DECIMAL(3,1),
        Director NVARCHAR(100),
        Stars NVARCHAR(255),
        Plot_Summary NVARCHAR(MAX),
        CONSTRAINT unique_movie UNIQUE (Title)
    );
END
'''

cursor.execute(create_table_query)
conn.commit()

# URL to crawl
url = "https://www.imdb.com/search/title/?title_type=feature&release_date=2013-01-01,2024-12-31&user_rating=6.5,10&languages=en"
driver.get(url)

# Number of times to click "Load More" to load enough 10,000 movies
load_more_clicks_needed = 199
current_clicks = 0

while current_clicks < load_more_clicks_needed:
    try:
        load_more_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ipc-see-more__button'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
        time.sleep(1)
        load_more_button.click()
        current_clicks += 1
        time.sleep(random.uniform(2, 4))  

    except TimeoutException:
        print(f"Cannot find 'Load More' button after {current_clicks + 1} clicks. Stopping.")
        break

# After clicking, get the list of movies
movies_list = driver.find_elements(By.CSS_SELECTOR, 'li.ipc-metadata-list-summary-item')

# Start collecting data from the first movie
movies_data = []
total_movies_to_crawl = 10000
i = 0

while i < total_movies_to_crawl and i < len(movies_list):
    try:
        movie = movies_list[i]

        # Scroll to the movie to get information
        # Use a loop to retry if encountering StaleElementReferenceException
        stale_attempts = 0
        while stale_attempts < 3:  # Retry up to 3 times
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", movie)
                time.sleep(random.uniform(1, 2))  # Random sleep to avoid being detected as a bot
                break  # If no error, exit the loop
            except StaleElementReferenceException:
                print(f"StaleElementReferenceException error, retrying {stale_attempts + 1}")
                stale_attempts += 1
                # Refresh the list of elements and retry
                movies_list = driver.find_elements(By.CSS_SELECTOR, 'li.ipc-metadata-list-summary-item')
                movie = movies_list[i]

        # Find the "See more information" button and click
        info_button = movie.find_element(By.CSS_SELECTOR, 'button[title^="See more information"]')
        info_button.click()
        time.sleep(random.uniform(1, 2))

        # Check if the popup has opened
        if EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')):
            popup_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')))
        else:
            print(f"No popup container for movie {i + 1}, skipping.")
            continue

        # Get movie information
        title = popup_container.find_element(By.CSS_SELECTOR, 'h3.ipc-title__text.prompt-title-text').text
        print(f"Crawling movie {i + 1}: {title}")

        # Get other information
        try:
            info_list = popup_container.find_elements(By.CSS_SELECTOR, 'ul[data-testid="btp_ml"] li')
            year = info_list[0].text if len(info_list) > 0 else ""
            duration = info_list[1].text if len(info_list) > 1 else ""
            mpaa = info_list[2].text if len(info_list) > 2 else ""
        except NoSuchElementException:
            year, duration, mpaa = "", "", ""  

        try:
            genres = ', '.join([genre.text for genre in popup_container.find_elements(By.CSS_SELECTOR, 'ul[data-testid="btp_gl"] li.ipc-inline-list__item')])
        except NoSuchElementException:
            genres = ""

        try:
            imdb_rating = popup_container.find_element(By.CSS_SELECTOR, 'span.ipc-rating-star--rating').text
            imdb_rating = float(imdb_rating) if imdb_rating else None  
        except (NoSuchElementException, ValueError):
            imdb_rating = None

        try:
            plot_summary = popup_container.find_element(By.CSS_SELECTOR, 'div.sc-65f72df1-2.geapts').text 
        except NoSuchElementException:
            plot_summary = ""
            
        try:
            director = popup_container.find_element(By.CSS_SELECTOR, 'div.sc-1582ce06-3.iWfkOS > div:nth-child(1) > ul > li > a').text
        except NoSuchElementException:
            director = ""

        try:
            stars_elements = popup_container.find_elements(By.CSS_SELECTOR, 'div.sc-1582ce06-3.iWfkOS > div:nth-child(2) > ul li')
            stars = ', '.join([star.text for star in stars_elements if star.text != director]) if stars_elements else ""
        except NoSuchElementException:
            stars = ""

        # Save data to the list
        movie_data = {
            'Title': title,
            'Year': year,
            'Duration': duration,
            'MPAA': mpaa,
            'Genres': genres,
            'IMDb_Rating': imdb_rating,
            'Director': director,
            'Stars': stars,
            'Plot_Summary': plot_summary
        }

        movies_data.append(movie_data)

        # Save to the database every 10 movies crawled
        if len(movies_data) >= 10:
            try:
                for movie in movies_data:
                    insert_query = '''
                    INSERT INTO Movies (Title, Year, Duration, MPAA, Genres, IMDb_Rating, Director, Stars, Plot_Summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    cursor.execute(insert_query, movie['Title'], movie['Year'], movie['Duration'], movie['MPAA'], movie['Genres'], movie['IMDb_Rating'], movie['Director'], movie['Stars'], movie['Plot_Summary'])                
                conn.commit()
                print(f"Successfully saved {len(movies_data)} movies to the database!")
                movies_data = []  # Reset the data list after saving
            except pyodbc.IntegrityError:
                # Catch error if encountering duplicate key
                print(f"Movie {movie['Title']} already exists in the database. Skipping.")
            except pyodbc.OperationalError as e:
                print(f"Connection error: {e}. Retrying connection...")
                conn, cursor = reconnect()

        # Close the popup after getting information
        try:
            close_button = popup_container.find_element(By.CSS_SELECTOR, 'button[title="Close Prompt"]')
            close_button.click()
            WebDriverWait(driver, 3).until(EC.invisibility_of_element(popup_container))
        except Exception as e:
            print(f"Error closing popup: {e}")
            continue

        i += 1
        time.sleep(random.uniform(0.5, 2))

    except (ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error clicking element: {e}")
        continue

driver.quit()
print("Data crawling completed.")
