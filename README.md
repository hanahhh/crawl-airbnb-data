# crawl-airbnb-data
This project used for crawling data filter by city and price range from airbnb website.

## Set up
Since Airbnb uses JavaScript to render content, just scrapy on its own cannot suffice sometimes. We need to use Splash as well, which is a plugin created by the Scrapy team that integrates nicely with scrapy.

**To install Splash, we need to do several things:**
1. Run Docker in the background before crawling with Splash
```
docker run -p 8050:8050 scrapinghub/splash
```
2. Install scrapy-splash using pip
```
pip install scrapy-splash
```
3. Setting environment
```
# Create venv
python3.10 -m venv env

# Enable venv
. env/bin/activate
```
## Crawling
Run `scrapy crawl airbnb -a city='{cityname}' -a price_lb='{pricelowerbound}' -a price_ub='{priceupperbound}'`
`cityname` refers to a valid city name

`pricelowerbound` refers to a lower bound for price from 0 to 999

`priceupperbound` refers to upper bound for price from 0 to 999. Spider will close if `priceupperbound` is less than
`pricelowerbound`  
**Note: Airbnb only returns a maximum of ~300 listings per specific filter (price range). To get more listings, I recommend scraping multiple times using small increments in price and concatenating the datasets.**

## -----**-----
Thanks [kailu3](https://github.com/kailu3) for inspired me to create this code.
