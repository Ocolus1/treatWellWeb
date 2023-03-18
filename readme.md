# Treatwell scraping script

## To get started clone this repo

```
git clone https://github.com/Ocolus1/treatWellWeb.git
```

```
cd treatWellWeb
```

## Create a virtual environment

Linux or Mac

```
python3 -m venv env
source env/bin/acitvate 
```

Windows 

```
python -m venv env
env\scripts\activate
```

## Install dependencies

```
pip install -r requirements.txt
```

## To get your data in an excel file run 

```
cd treatwell
scrapy crawl treatwell -a start_urls=https://example.com
```

## You will see two files generated

1. output.xlsx  - It contains the extracted date and avaliable time slots
2. skipped_list.json -  It contains the list of dats skipped due to unavailability on that date.

