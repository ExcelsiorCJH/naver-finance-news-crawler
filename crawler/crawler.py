import os
import re
import time
import random
import dill
import requests

from datetime import datetime, timedelta
from typing import List, Dict

from bs4 import BeautifulSoup
from bs4.element import NavigableString

from tqdm import tqdm
from .utils import clean_text


class MainNewsCrawler:
    """
    MainNewsCrawler Class
    =====================

    Arguments
    ---------
    start_date: str, default = '2013-08-06'
            start date for crawling news related to kospi
    end_date: str, default = None
        end date for crawling news related to kospi
        if end is None, end will set be today
    save_dir: str, default = None
        directory for saving crawled news data
    stopwords: list of str, default = None
        stopwords, ex. ['무단', '재배포', ...]
    """

    def __init__(
        self,
        start_date: str,
        end_date: str = None,
        save_dir: str = None,
        stopwords: List[str] = None,
    ):
        self.root_url = "https://finance.naver.com"
        self.main_url = "https://finance.naver.com/news/mainnews.nhn?date="
        self.start_date = start_date
        self.end_date = end_date
        self.save_dir = save_dir
        if stopwords:
            self.stopwords = stopwords
        else:
            self.stopwords = ["무단", "재배포", "배포", "article_split"]

        self.news_data = []

    def crawl_news(self) -> List[Dict]:
        """
        Crawl News method
        =================

        Returns
        -------
        news_data: list of dict
            [{'press': press(str),
            'date': publish date(str),
            'time': publish time(str),
            'title': news title(str),
            'link': news url(str),
            'text': origin text(str),
            'cleaned_text': cleaned text(str)},...]
        """
        self.date_list = self._date_range(self.start_date, self.end_date)

        cnt = 1
        progress_bar = tqdm(self.date_list)
        for idx, date in enumerate(progress_bar, start=1):
            progress_bar.set_description(f"Crawling {date}")
            page_links = self.get_page_links(date)
            data = self.get_metadata(page_links)
            for news in data:
                url = news["link"]
                text, cleaned_text = self.get_article(url)
                news["text"] = text
                news["cleaned_text"] = cleaned_text
                time.sleep(random.uniform(0.2, 0.8))

            self.news_data.extend(data)

            if self.save_dir:
                if idx % 7 == 0:
                    save_path = os.path.join(self.save_dir, f"news_data_{cnt}.pkl")
                    with open(save_path, "wb") as f:
                        dill.dump(self.news_data, f)

                    cnt += 1
                    self.news_data.clear()

                if idx % 7 != 0 and idx == len(self.date_list):
                    save_path = os.path.join(self.save_dir, f"news_data_{cnt}_last.pkl")
                    with open(save_path, "wb") as f:
                        dill.dump(self.news_data, f)
                    self.news_data.clear()

            time.sleep(random.uniform(0.5, 0.9))
        return self.news_data

    def get_article(self, url: str) -> str:
        """
        Get Article method
        ==================
        function to crawl the article

        Arguments
        ---------
        url: str
            url to crawl the article

        Returns
        -------
        text: str
            original article text
        cleaned_text: str
            cleaned article text
        """
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")

        sents = soup.find("div", {"class": "articleCont"})
        sents = [sent for sent in sents if isinstance(sent, NavigableString)]

        origin_text = "".join(sents)

        if self.stopwords:
            sents = [sent for sent in sents if not any(word in sent for word in self.stopwords)]

        text = "".join(sents)
        cleaned_text = clean_text(text)

        return origin_text, cleaned_text

    def get_metadata(self, url_list: List[str]) -> List[Dict]:
        """
        Metadata method
        ================
        function to get meta data of news

        Arguments
        ---------
        url_list: list of str
            url to crawl metadata

        Returns
        -------
        metadata: list of dict
            [{'press': press(str),
            'date': publish date(str),
            'time': publish time(str),
            'title': news title(str),
            'link': news url(str)},...]
        """
        metadata = []
        for url in url_list:
            # bs4
            req = requests.get(self.root_url + url)  # HTTP GET Request
            soup = BeautifulSoup(req.text, "html.parser")
            # 언론사
            press_list = soup.find_all("span", {"class": "press"})
            press_list = [press.text.strip() for press in press_list]

            # 발간일
            p_datetime_list = soup.find_all("span", {"class": "wdate"})
            p_datetime_list = [p_datetime.text for p_datetime in p_datetime_list]

            # 제목 및 링크
            news_links = soup.findChild("div", {"class": "mainNewsList"})
            news_links = news_links.find_all("a")
            news_titles = [link.text for link in news_links if link.text]
            news_links = [link["href"] for link in news_links]

            for press, p_datetime, title, link in zip(
                press_list, p_datetime_list, news_titles, news_links
            ):
                p_date, p_time = p_datetime.split()
                meta_dict = {
                    "press": press,
                    "date": p_date,
                    "time": p_time,
                    "title": title,
                    "link": f"{self.root_url}{link}",
                }
                metadata.append(meta_dict)

        return metadata

    def get_page_links(self, date: str) -> List[str]:
        """
        Page Links method
        =================
        function to get the page link for date

        Arguments
        ---------
        date: str
            date such as "%Y-%m-%d"("2021-05-03")

        Returns
        -------
        page_links: list of str
            ex. ['url1', 'url2', ...]
        """
        req = requests.get(self.main_url + date)  # HTTP GET Request
        soup = BeautifulSoup(req.text, "html.parser")

        page_links = soup.findChild("table", {"class": "Nnavi"})
        page_links = page_links.find_all("a")
        page_links = [link["href"] for link in page_links]
        page_links = list(set(page_links))
        page_links.sort()

        return page_links

    def _date_range(self, start_date: str = "2013-08-06", end_date: str = None) -> List[str]:
        """
        Date Range method
        ==================
        function to set period for crawling

        Arguments
        ---------
        start_date: str, default = '2013-08-06'
            start date for crawling news related to kospi
        end_date: str, default = None
            end date for crawling news related to kospi
            if end is None, end will set be today

        Returns
        -------
        date_list: reversed list of str
            ex. ['2021-05-03', '2021-05-02', ...]
        """
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_date = datetime.today()

        self.end_date = end_date

        date_list = [
            start_date + timedelta(days=day) for day in range(0, (end_date - start_date).days + 1)
        ]
        date_list = [day.strftime("%Y-%m-%d") for day in date_list]
        return date_list[::-1]
