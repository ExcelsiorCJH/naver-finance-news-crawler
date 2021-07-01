import argparse

from crawler import MainNewsCrawler


# Parser
parser = argparse.ArgumentParser(description="Naver Finance News Crawler")
# mode ["main-news", "item-news"]
parser.add_argument("--mode", type=str, default="main-news", help="select the mode to use")
# periods
parser.add_argument("--start-date", type=str, default="2021-06-30", help="start date, YYYY-mm-dd")
parser.add_argument("--end-date", type=str, default=None, help="end date, YYYY-mm-dd")
# save directory
parser.add_argument("--save-dir", type=str, default="data/")

args = parser.parse_args()

if __name__ == "__main__":
    if args.mode == "main-news":
        crawler = MainNewsCrawler(
            start_date=args.start_date,
            end_date=args.end_date,
            save_dir=args.save_dir,
            stopwords=None,
        )

    data = crawler.crawl_news()
