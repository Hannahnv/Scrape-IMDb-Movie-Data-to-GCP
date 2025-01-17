# Scrape IMDb Movie Data to GCP 🚀
This project focuses on extracting movie data from IMDb using Selenium and seamlessly storing it in Google Cloud Platform (GCP) for further analysis and processing.

## 📋 Project Overview
The primary goal is to automate the process of scraping movie data, ensuring efficient data extraction and storage in GCP. This setup is ideal for building pipelines for movie-related analytics or projects.

## 📂 Data Source
Extract data from [IMDb website](https://www.imdb.com/search/title/?title_type=feature&release_date=2013-01-01%2C2024-12-31&user_rating=6.5%2C10&languages=en). The data includes essential information such as:
* Title
* Year
* Duration
* MPAA
* Genres
* IMDb_Rating
* Director
* Stars
* Plot_Summary

## 📖 Tutorial
For a detailed guide on implementing this project, refer to the [tutorial article here](https://medium.com/ai-advances/how-i-scraped-10k-imdb-movies-and-stored-them-on-gcp-effortlessly-246d348360f0)

## 📜 Prerequisites
Before running the project, ensure you have the following set up:

1. Google Cloud Platform (GCP):
* A GCP account with proper billing enabled.
* Access to Cloud SQL Server to store data.
2. Local Environment:
* Python installed (>= 3.10).
* Required libraries: Selenium, pyodbc, random, and time.
* A compatible web driver (e.g., ChromeDriver) is installed for Selenium.
## 📊 Flowchart: Scraping IMDb Movies and Storing in GCP
![image](https://github.com/user-attachments/assets/605710a3-bea2-4182-a9ef-2ea8e5997b10)
