import os
import re
import time
import random
import dill
import requests
import urllib

from datetime import datetime, timedelta
from typing import List, Dict, Union

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from kss import split_sentences

from tqdm import tqdm
from .utils import clean_text


class QueryNewsCrawler:
    def __init__(self):
        # 네이버 뉴스의 경우 page가 아닌
        # 뉴스 기사 개수 카운팅으로 보여주고 있음
        # 1 ~ 4000개까지 10개 단위로 보여줌
        self.main_url = "https://search.naver.com/search.naver"
        self.query_url = "?where=news&sm=tab_pge&query="
        self.page_url = (
            "&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=23&mynews=0&office_type=0&"
        )
        self.page_url += "office_section_code=0&news_office_checked=&nso=so:r,p:all,a:all&start="

    def crawl_news_by_query(self, query: str, count: int = 200) -> List[Dict]:
        """
        검색어(query)에 따른 뉴스 크롤링 메서드
        =====================================

        Arguments
        ---------
        query: str
            크롤링 하고자 하는 뉴스 검색어
        count: int, default is 200
            가져오고자 하는 뉴스 개수 (10 단위씩 설정해줘야 함)

        Returns
        -------
        news_data: List[Dict]
            [{'href': str, # 뉴스 링크
            'title': str, # 뉴스 제목
            'text': str, # 뉴스 기사(줄임말)
            'thumb': str} # 썸네일
            ,...]
        """
        self.query = query
        parsed_query = urllib.parse.quote(query)

        if count:
            start_range = list(range(1, count, 10))
        else:
            start_range = list(range(1, 4000, 10))

        news_data = []
        for s_idx in tqdm(start_range):
            url = f"{self.main_url}{self.query_url}{parsed_query}{self.page_url}{s_idx}"

            # request and soup
            req = requests.get(url)
            soup = BeautifulSoup(req.text, "html.parser")

            # ul lists and li lists
            ul_lists = soup.find("ul", {"class": "list_news"})
            li_lists = ul_lists.findChildren("li", {"class": "bx"})
            for li in li_lists:
                # news link & title
                link = li.find("a", {"class": "news_tit"})
                href, title = link["href"], link["title"]
                # news text
                text = li.find("a", {"class": "api_txt_lines dsc_txt_wrap"}).text
                # thumb nail if exist
                thumb = ""
                thumb_link = li.find("img", {"class": "thumb api_get"})
                if thumb_link:
                    thumb = thumb_link["src"]

                # update link_title_dict
                news_data.append({"href": href, "title": title, "text": text, "thumb": thumb})
            time.sleep(random.uniform(0.6, 0.9))

        return news_data


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

        # directory check
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        if stopwords:
            self.stopwords = stopwords
        else:
            self.stopwords = [
                "기자",
                "특파원",
                "무단",
                "저작권",
                "저작권자",
                "배포",
                "재배포",
                "article_split",
            ]

        self.total_news_data = []
        self.news_data = []

    def crawl_news(self) -> List[Dict]:
        self.date_list = self._date_range(self.start_date, self.end_date)

        # cnt = 1
        crawl_range = []
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
                time.sleep(random.uniform(0.2, 0.6))

            self.news_data.extend(data)
            crawl_range.append(date)
            if self.save_dir:
                if idx % 14 == 0:
                    start, end = crawl_range[0], crawl_range[-1]
                    save_path = os.path.join(self.save_dir, f"news_data_{end}__{start}.pkl")
                    with open(save_path, "wb") as f:
                        dill.dump(self.news_data, f)

                    # cnt += 1
                    self.total_news_data.extend(self.news_data)
                    self.news_data.clear()
                    crawl_range.clear()

                if idx % 7 != 0 and idx == len(self.date_list):
                    start, end = crawl_range[0], crawl_range[-1]
                    save_path = os.path.join(self.save_dir, f"news_data_{end}__{start}.pkl")
                    with open(save_path, "wb") as f:
                        dill.dump(self.news_data, f)
                    self.total_news_data.extend(self.news_data)
                    self.news_data.clear()
                    crawl_range.clear()

            time.sleep(random.uniform(0.5, 0.9))
        return self.total_news_data

    def get_article(self, url: str) -> Union[str, List[str]]:
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
        cleaned_sentences: list of str
            cleaned article sentences
        """
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")

        sents = soup.find("div", {"class": "articleCont"})
        if sents:
            sents = [sent for sent in sents if isinstance(sent, NavigableString)]
        else:
            sents = []

        origin_text = "".join(sents)

        text = "".join(sents)
        sentences = split_sentences(text)
        cleaned_sentences = [clean_text(sent) for sent in sentences]
        cleaned_sentences = [sent for sent in cleaned_sentences if sent]
        cleaned_sentences = [
            sent for sent in cleaned_sentences if not any(word in sent for word in self.stopwords)
        ]

        return origin_text, cleaned_sentences

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
            news_urls = []
            for news_link in news_links:
                if news_link not in news_urls:
                    news_urls.append(news_link)

            for press, p_datetime, title, link in zip(
                press_list, p_datetime_list, news_titles, news_urls
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
