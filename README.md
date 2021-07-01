# Naver-Finance-News-Crawler

- Code for Naver Finance (Main) News Crawling([link](https://finance.naver.com/news/mainnews.nhn))



## Usage

```
python main.py --start-date "2021-06-30" --end-date "2021-07-01" --save-dir "data"
```



## Directories

```
crawler
  ├── __init__.py    
  ├── crawler.py  # MainNewsClawer class 
  └── utils.py    # util for crawling

examples
  └── 01-main_news_crawling.ipynb  # tutorial notebook
  
 
main.py  # main python file
requirements.txt
README.md
```



## Result Example

- Result is list of dictionary

```
[
	{'press': 언론사,
	 'date': 업로드 날짜,
	 'time': 업로드 시간,
	 'title': 기사제목,
	 'link': 기사 링크,
	 'text': 기사 내용(원문),
	 'cleaned_text': 전처리된 기사 내용}
]
```

```
{'press': '연합뉴스',
 'date': '2021-06-30',
 'time': '02:00:12',
 'title': '[유럽증시] 경기회복 기대감에 상승',
 'link': 'https://finance.naver.com/news/news_read.nhn?article_id=0012492807&office_id=001&mode=mainnews&type=&date=2021-06-30&page=1',
 'text': '\n    (런던=연합뉴스) 최윤정 특파원 = 29일(현지시간) 유럽 주요국 증시는 경기 회복 기대감에 반등했다.    프랑스 파리 증시의 CAC40 지수는 전 거래일 종가 대비 0.14% 오른 6,567.43으로, 영국 런던 증시의 FTSE 100 지수는 0.21% 상승한 7,087.55로 거래를 마쳤다.     범유럽 지수인 유로 Stoxx 50 지수는 0.43% 높은 4,107.51로, 독일 프랑크푸르트 증시의 DAX30 지수도 0.88% 오른 15,690.59로 마감했다.    백신 접종으로 몇몇 국가에서 규제가 완화되고 경제 활동이 재개되면서 6월 유로존 경제 심리가 21년 만에 최고를 찍었다.     로이터통신에 따르면 ING 애널리스트는 투자의견 메모에서 "체감경기가 지금보다 좋았을 때는 2000년 5월에 닷컴 거품이 정점이었을 때다"라고 말했다.    독일의 6월 물가 상승세도 다소 둔화하면서 우려를 덜었다.    merciel@yna.co.kr\n',
 'cleaned_text': ['최윤정 특파원  29일 유럽 주요국 증시는 경기 회복 기대감에 반등했다.',
  '프랑스 파리 증시의 40 지수는 전 거래일 종가 대비 0.14% 오른 6567.43으로 영국 런던 증시의  100 지수는 0.21% 상승한 7087.55로 거래를 마쳤다.',
  '범유럽 지수인 유로  50 지수는 0.43% 높은 4107.51로 독일 프랑크푸르트 증시의 30 지수도 0.88% 오른 15690.59로 마감했다.',
  '백신 접종으로 몇몇 국가에서 규제가 완화되고 경제 활동이 재개되면서 6월 유로존 경제 심리가 21년 만에 최고를 찍었다.',
  '로이터통신에 따르면  애널리스트는 투자의견 메모에서 체감경기가 지금보다 좋았을 때는 2000년 5월에 닷컴 거품이 정점이었을 때다라고 말했다.',
  '독일의 6월 물가 상승세도 다소 둔화하면서 우려를 덜었다.']}
```

