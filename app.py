from flask import Flask, render_template, request, send_file
from selenium import webdriver # type: ignore
from selenium.webdriver.chrome.service import Service # type: ignore
from selenium.webdriver.chrome.options import Options # type: ignore
from bs4 import BeautifulSoup
from fpdf import FPDF # type: ignore
import pandas as pd
import os
from requests.exceptions import ConnectionError, Timeout, RequestException

app = Flask(__name__)

# Set up Selenium WebDriver (with headless option)
def init_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Path to ChromeDriver (update this to the correct path)
    webdriver_service = Service('/path/to/chromedriver')  # Update this to the path where you downloaded chromedriver
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return driver

# Function to scrape the webpage using Selenium and BeautifulSoup
def scrape_url(url):
    driver = init_webdriver()

    try:
        driver.get(url)
        # Wait for the page to load completely (if needed, you can add explicit waits for elements)
        page_source = driver.page_source
        driver.quit()  # Close the driver after getting the page source

        # Use BeautifulSoup to parse the page source
        soup = BeautifulSoup(page_source, 'html.parser')

        data = []
        # Scrape headings, paragraphs, links, and images
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            data.append([header.name, header.text.strip()])

        for paragraph in soup.find_all('p'):
            data.append(['Paragraph', paragraph.text.strip()])

        for link in soup.find_all('a', href=True):
            data.append(['Link', link.text.strip(), link['href']])

        for img in soup.find_all('img', src=True):
            data.append(['Image', img.get('alt', 'No alt text'), img['src']])

        if data:
            df = pd.DataFrame(data, columns=['Type', 'Content', 'Additional Info'])
            return df, None
        else:
            return None, "No data found on the webpage."

    except Exception as e:
        driver.quit()  # Ensure driver is closed in case of any error
        return None, f"An error occurred: {e}"

@app.route('/')
def index():
    return render_template('index.html', error=None)

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    file_type = request.form['file_type']

    df, error = scrape_url(url)

    if error:
        return render_template('index.html', error=error)

    if df is not None:
        filename = 'scraped_data.' + file_type

        if file_type == 'csv':
            df.to_csv(filename, index=False)
        elif file_type == 'pdf':
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            col_width = pdf.w / (len(df.columns) + 1)

            for header in df.columns:
                pdf.cell(col_width, 10, header, border=1)
            pdf.ln()

            for index, row in df.iterrows():
                for item in row:
                    pdf.cell(col_width, 10, str(item), border=1)
                pdf.ln()

            pdf.output(filename)

        return send_file(filename, as_attachment=True)

    return render_template('index.html', error="No data found to scrape!")

if __name__ == '__main__':
    app.run(debug=True)
