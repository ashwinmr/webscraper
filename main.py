import os.path
import sys
import argparse
import pandas as pd
import wordcloud
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
import time

def parse_args():
  """ Parse arguments for program
  """
  parser = argparse.ArgumentParser(description="Program for creating wordcloud of google app reviews")
  parser.add_argument('url', help='Url for google app')
  parser.add_argument('-s','--save_file', default='reviews.csv', help='File to save review data')
  parser.add_argument('-d','--web_driver_path', default='chromedriver.exe', help='Path to chrome web driver')

  return parser.parse_args()

def process_url(url):
    """ Process url to get to correct page
    """
    url += '&showAllReviews=true'
    return url

def get_html_no_js(url):
    """ Get html from url that does not require Javascript
    """
    r = requests.get(url)

    # with open('res.html','w',encoding=r.encoding) as f:
    #     f.write(r.text)

    return r.text

def get_html_with_js(url, web_driver_path):
    """ Get html from url that uses Javascript to load
    """
    driver = Chrome(web_driver_path)
    driver.get(url)

    SCROLL_PAUSE_TIME = 2

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        
    # Get all html and close
    html = driver.page_source
    driver.close()

    # with open('res.html','w',encoding='utf-8') as f:
    #     f.write(html)

    return html

def save_review_data_from_html(html, save_file):
    """ Get the ratings and reviews from html
    """

    soup = BeautifulSoup(html, 'lxml')

    ratings = []
    reviews = []

    review_blocks = soup.find_all('div',class_ = 'd15Mdf bAhLNe')
    for review_block in review_blocks:
        review = review_block.find('span',jsname = 'bN97Pc').find(text=True)
        reviews.append(review)
        rating_string = review_block.find('div', class_ = 'pf5lIe').contents[0]['aria-label']
        rating = int(rating_string[6])
        ratings.append(rating)

    # Save to csv
    df = pd.DataFrame({'rating' : ratings, 'review' : reviews})
    df.to_csv(save_file, index=False)

def plot_wordclouds_from_review_data(review_data_file):
    """ Load the review data and plot wordclouds
    """
    # Load review data
    df = pd.read_csv(review_data_file)

    # Compile text
    text1 = " ".join(review for review in df.loc[df['rating']==1]['review'])
    text5 = " ".join(review for review in df.loc[df['rating']==5]['review'])
    if text1:
        wc1 = wordcloud.WordCloud(background_color="white").generate(text1)
    else:
        wc1 = None
    if text5:
        wc5 = wordcloud.WordCloud(background_color="white").generate(text5)
    else:
        wc5 = None

    # Plot
    plt.subplot(1,2,1)
    if wc1:
        plt.imshow(wc1)
        plt.axis('off')
        plt.title('1 start reviews')

    plt.subplot(1,2,2)
    if wc5:
        plt.imshow(wc5)
        plt.axis('off')
        plt.title('5 start reviews')

    plt.show()

if __name__ == "__main__":
    args = parse_args()

    url = process_url(args.url)

    # Check for webdriver
    if not os.path.exists(args.web_driver_path):
        print('Please downlaod the crome driver from https://chromedriver.chromium.org/ and place chromedriver.exe in the current folder')
        sys.exit()

    html = get_html_with_js(url, args.web_driver_path)

    save_review_data_from_html(html, args.save_file)

    plot_wordclouds_from_review_data(args.save_file)
