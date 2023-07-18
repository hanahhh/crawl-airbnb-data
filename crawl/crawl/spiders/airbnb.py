import json
import collections
from scrapy.spiders import CrawlSpider
from scrapy_splash import SplashRequest
import pandas as pd
import re
import numpy as np
class Airbnb(CrawlSpider):

    name = "airbnb"

    def __init__(self, city='', price_lb='', price_ub='', *args, **kwargs):
        super(Airbnb, self).__init__(*args, **kwargs)
        self.city = city
        self.price_lb = price_lb
        self.price_ub = price_ub
        self.export_data = collections.defaultdict(dict)

    def start_requests(self):
        url = f"https://www.airbnb.com.vn/s/{self.city}/homes?locale=vi&price_min={self.price_lb}&price_max={self.price_ub}&cursor=eyJzZWN0aW9uX29mZnNldCI6MywiaXRlbX&currency=VND"
        yield SplashRequest(url=url, callback=self.parse,
                                endpoint="render.html",
                                args={'wait': '0.5'})

    def extract_first_number(self, text):
        match = re.search(r'₫([\d.,]+)', text)
        if match:
            number_str = match.group(1)
            number_str = number_str.replace('.', '')
            return number_str.split(",")[0]
        else:
            return None

    def parse(self, response, **kwargs):
        path = response.xpath("//script[@id='data-deferred-state']/text()").get()
        path = json.loads(path)
        data = path['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['searchResults']
        pagination_info = path['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['paginationInfo']['nextPageCursor']
        data_dict = collections.defaultdict(dict)

        base_url = 'https://www.airbnb.com.vn/rooms/'

        for index, home in enumerate(data):
            if index > 1:
                if home.get('listing'):
                    room_id = home.get('listing').get('id')
                    primary_host_passport = None
                    if home.get('listing').get('primaryHostPassport'):
                        primary_host_passport = home.get('listing').get('primaryHostPassport')

                    url = base_url + home.get('listing').get('id')

                    data_dict[room_id]['room_id'] = room_id
                    data_dict[room_id]['url'] = url
                    review_count = ''
                    data_dict[room_id]['rating'] = '0'
                    if home.get('listing').get('avgRatingLocalized'):
                        match_rating = re.match(r'(\d+,\d+)\s+\((\d+)\)', home.get('listing').get('avgRatingLocalized'))
                        if match_rating:
                            data_dict[room_id]['rating'] = match_rating.group(1)
                            review_count = match_rating.group(2)

                    data_dict[room_id]['city'] = self.city
                    data_dict[room_id]['contextualPicturesCount'] = home.get('listing').get('contextualPicturesCount')
                    data_dict[room_id]['lat'] = home.get('listing').get('coordinate').get('latitude')
                    data_dict[room_id]['long'] = home.get('listing').get('coordinate').get('longitude')
                    data_dict[room_id]['listingObjType'] = home.get('listing').get('listingObjType')
                    data_dict[room_id]['pdpUrlType'] = home.get('pdpUrlType')
                    data_dict[room_id]['name'] = home.get('listing').get('name')
                    data_dict[room_id]['roomTypeCategory'] = home.get('listing').get('roomTypeCategory')
                    if len(review_count) > 0:
                        data_dict[room_id]['reviewCount'] = review_count
                    if primary_host_passport:
                        data_dict[room_id]['isSuperHost'] = primary_host_passport.get('isSuperhost')
                        data_dict[room_id]['isVerified'] = primary_host_passport.get('isVerified')
                        stats = primary_host_passport.get('stats')

                        if len(stats) > 0:
                            if 'reviewCount' not in data_dict[room_id]:
                                data_dict[room_id]['reviewCount'] = stats[0].get('value')
                        if len(stats) > 2:
                            data_dict[room_id]['yearHosting'] = stats[2].get('value')
                            data_dict[room_id]['yearHostingLabel'] = stats[2].get('label')

                    data_dict[room_id]['canInstantBook'] = home.get('pricingQuote').get('canInstantBook')
                    data_dict[room_id]['weeklyPriceFactor'] = home.get('pricingQuote').get('weeklyPriceFactor')
                    data_dict[room_id]['structuredStayDisplayPrice'] = home.get('pricingQuote').get('structuredStayDisplayPrice').get('primaryLine').get('qualifier')
                    data_dict[room_id]['price'] = self.extract_first_number(home.get('pricingQuote').get('structuredStayDisplayPrice').get('primaryLine').get('accessibilityLabel'))#re.sub(r'[^\d]', '', home.get('pricingQuote').get('structuredStayDisplayPrice').get('primaryLine').get('accessibilityLabel'))


                    self.export_data.update(data_dict)

        for room_id in data_dict:
            yield SplashRequest(url=f"{base_url+room_id}?locale=vi&currency=VND", callback=self.parse_details,
                                meta={'id': room_id},
                                endpoint="render.html",
                                args={'wait': '0.5'})

        if pagination_info:
            new_url = f"https://www.airbnb.com.vn/s/{self.city}/homes?locale=vi&price_min={self.price_lb}&price_max={self.price_ub}&cursor={pagination_info}&currency=VND"
            yield SplashRequest(url=new_url, callback=self.parse,
                                endpoint="render.html",
                                args={'wait': '0.5'})

    def close(self, spider, reason):
        df = pd.DataFrame.from_dict(self.export_data, orient='index')
        df_filled = df.replace({None: pd.NA})
        csv_file_path = f"crawl/{self.city}.csv"
        print(df_filled.head())
        df_filled.to_csv(csv_file_path, index=False, na_rep='NaN')

    def parse_details(self, response, **kwargs):
        id = response.meta['id']
        room = self.export_data[id]
        path = response.xpath("//script[@id='data-deferred-state']/text()").get()
        path = json.loads(path)
        data = path['niobeMinimalClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']
        max_guest_capacity = None
        list_amenities = None
        for index, section in enumerate(data):
            if section['sectionId'] == 'BOOK_IT_SIDEBAR':
                max_guest_capacity = data[index]['section']['maxGuestCapacity']
            if section['sectionId'] == 'AMENITIES_DEFAULT':
                list_amenities = data[index]['section']['previewAmenitiesGroups'][0]['amenities']
        if len(self.export_data[id]) > 0:
            room['maxGuestCapacity'] = max_guest_capacity
            for amenity in list_amenities:
                room[amenity['icon']] = amenity['available']
        self.export_data[id] = room


