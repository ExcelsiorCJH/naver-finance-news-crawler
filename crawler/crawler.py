import os
import re
import time
import random
import dill
import requests
import urllib
import bs4
import newspaper

from datetime import datetime, timedelta
from typing import List, Dict, Union

from newspaper import Article
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from kss import split_sentences

from tqdm.auto import tqdm
from .utils import clean_text


class QueryNewsCrawler:
    def __init__(self):
        # 네이버 뉴스의 경우 page가 아닌
        # 뉴스 기사 개수 카운팅으로 보여주고 있음
        # 1 ~ 4000개까지 10개 단위로 보여줌
        self.main_url = "https://search.naver.com/search.naver"
        self.query_url = "?where=news&sm=tab_pge&query="
        self.page_url = "&sort=0&photo=0&field=0&pd=0&ds=&de=&cluster_rank=23&mynews=0&office_type=0&"
        self.page_url += (
            "office_section_code=0&news_office_checked=&nso=so:r,p:all,a:all&start="
        )

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
            [{
            "href": str,  # 뉴스 url
            "date": str,  # 게재 날짜
            "press": str,  # 언론사
            "title": str,  # 뉴스 제목
            "short_text": str,  # 뉴스 줄임말
            "text": str,  # 뉴스 기사
            "top_image": str,  # 뉴스 메인 이미지
            "thumb": str,  # 뉴스 썸네일
            },...]
        """

        # TODO: publish time 추가하기
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
                # newspaper3k instance
                try:
                    news_instance = Article(href, language="ko")
                    news_instance.download()
                    news_instance.parse()
                except:
                    news_instance = None

                # 언론사
                press = li.find("a", {"class": "info press"}).text
                # publish date
                publish_date = self._get_datetime(news_instance, li)
                # news short_text
                short_text = li.find("a", {"class": "api_txt_lines dsc_txt_wrap"}).text
                # news text and top_image
                text, top_iamge = self._get_article(news_instance, li)
                # thumb nail if exist
                thumb = ""
                thumb_link = li.find("img", {"class": "thumb api_get"})
                if thumb_link:
                    thumb = thumb_link["src"]

                # update link_title_dict
                news_data.append(
                    {
                        "language": "ko",
                        "url": href,
                        "publishdate": publish_date,
                        "press": press,
                        "title": title,
                        "shortcontent": short_text,
                        "content": text,
                        "topimage": top_iamge,
                        "thumbnail": thumb,
                    }
                )
            time.sleep(random.uniform(0.6, 0.9))
        return news_data

    def _get_article(
        self, article: newspaper.article.Article, li: bs4.element.Tag
    ) -> str:
        text, top_image = None, None
        if article is not None:
            text = article.text
            top_img = article.top_image

        links = li.find_all("a", {"class": "info"})
        naver_news_url = [link for link in links if link.text == "네이버뉴스"]
        if naver_news_url:
            naver_news_url = naver_news_url[0]
            naver_news_url = naver_news_url["href"].replace("&amp;", "&")
        else:
            naver_news_url = None

        if text is None and naver_news_url is not None:
            try:
                a = Article(naver_news_url, language="ko")
                a.download()
                a.parse()

                text = a.text
            except:
                pass
        elif top_image is None and naver_news_url is not None:
            try:
                a = Article(naver_news_url, language="ko")
                a.download()
                a.parse()

                top_image = a.top_image
            except:
                pass
        return text, top_image

    def _get_datetime(
        self,
        article: newspaper.article.Article,
        li: bs4.element.Tag,
    ) -> datetime:
        publish_date = None
        if article is not None:
            publish_date = article.publish_date

        if publish_date is None:
            date_list = li.find_all("span", {"class": "info"})
            date = None
            if len(date_list) > 1:
                date = date_list[-1].text
            else:
                date = li.find("span", {"class": "info"}).text
                date = date.split()[0]

            if "분" in date:
                minutes = re.sub(r"[^\d+]", "", date)
                publish_date = datetime.now() - timedelta(minutes=int(minutes))
            elif "시간" in date:
                hours = re.sub(r"[^\d+]", "", date)
                publish_date = datetime.now() - timedelta(hours=int(hours))
            elif "일" in date:
                days = re.sub(r"[^\d+]", "", date)
                publish_date = datetime.now() - timedelta(days=int(days))
            else:
                try:
                    publish_date = datetime.strptime(date, "%Y.%m.%d.")
                except:
                    pass
        return publish_date


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
        use_split_sentence: bool = False,
    ):
        self.root_url = "https://finance.naver.com"
        self.main_url = "https://finance.naver.com/news/mainnews.nhn?date="
        self.start_date = start_date
        self.end_date = end_date
        self.save_dir = save_dir
        self.use_split_sentence = use_split_sentence
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
                try:
                    url = news["link"]
                    result = self.get_article(url)
                    news["text"] = result["origin_text"]
                    news["summary"] = result["summaries"]
                    news["cleaned_text"] = result["cleaned_sentences"]
                except:
                    continue
                time.sleep(random.uniform(0.2, 0.6))

            self.news_data.extend(data)
            crawl_range.append(date)
            if self.save_dir:
                if idx % 14 == 0:
                    start, end = crawl_range[0], crawl_range[-1]
                    save_path = os.path.join(
                        self.save_dir, f"news_data_{end}_{start}.pkl"
                    )
                    with open(save_path, "wb") as f:
                        dill.dump(self.news_data, f)

                    # cnt += 1
                    self.total_news_data.extend(self.news_data)
                    self.news_data.clear()
                    crawl_range.clear()

                if idx % 7 != 0 and idx == len(self.date_list):
                    start, end = crawl_range[0], crawl_range[-1]
                    save_path = os.path.join(
                        self.save_dir, f"news_data_{end}_{start}.pkl"
                    )
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
        url = re.search(r"href='([^']*)'", req.text).group(1)
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "lxml")
        article = soup.find("article", {"class": "_article_content"})

        text = ""
        contents = []
        summaries = []
        for content in article.contents:
            # summary 부분 처리 - media_end_summary 클래스를 포함하는 경우
            if isinstance(content, bs4.element.Tag) and "media_end_summary" in str(
                content
            ):
                summary_texts = [
                    text for text in content.stripped_strings if isinstance(text, str)
                ]
                summaries.extend(summary_texts)
                continue  # summary는 text와 contents에 포함하지 않음

            # 일반 텍스트 처리
            elif isinstance(content, bs4.element.Tag):
                content_text = content.get_text(strip=True)
                if content_text:  # 빈 문자열이 아닌 경우만 추가
                    text += content_text + " "  # 문자열에는 공백과 함께 추가
                    contents.append(content_text)  # 리스트에는 개별 텍스트로 추가
            # NavigableString인 경우
            elif isinstance(content, NavigableString) and content.strip():
                stripped_text = content.strip()
                text += stripped_text + " "  # 문자열에는 공백과 함께 추가
                contents.append(stripped_text)  # 리스트에는 개별 텍스트로 추가

        origin_text = text.strip()
        if self.use_split_sentence:
            sentences = split_sentences(text)
            cleaned_sentences = [clean_text(sent) for sent in sentences]
            cleaned_sentences = [sent for sent in cleaned_sentences if sent]
            cleaned_sentences = [
                sent
                for sent in cleaned_sentences
                if not any(word in sent for word in self.stopwords)
            ]
        else:
            cleaned_sentences = [clean_text(sent) for sent in contents]
            cleaned_sentences = [sent for sent in cleaned_sentences if sent]
            cleaned_sentences = [
                sent
                for sent in cleaned_sentences
                if not any(word in sent for word in self.stopwords)
            ]

        return {
            "origin_text": origin_text,
            "cleaned_sentences": cleaned_sentences,
            "summaries": summaries,
        }

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
            soup = BeautifulSoup(req.text, "lxml")
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

    def _date_range(
        self, start_date: str = "2013-08-06", end_date: str = None
    ) -> List[str]:
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
            start_date + timedelta(days=day)
            for day in range(0, (end_date - start_date).days + 1)
        ]
        date_list = [day.strftime("%Y-%m-%d") for day in date_list]
        return date_list[::-1]
