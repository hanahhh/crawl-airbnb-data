import json
import collections
from scrapy.spiders import CrawlSpider
from scrapy_splash import SplashRequest
import csv

class Airbnb(CrawlSpider):

    name = "airbnb"

    def __init__(self, city='', price_lb='', price_ub='', *args, **kwargs):
        super(Airbnb, self).__init__(*args, **kwargs)
        self.city = city
        self.price_lb = price_lb
        self.price_ub = price_ub
        self.export_data = collections.defaultdict(dict)
        self.header = {'room_id', 'url', 'avgRatingLocalized', 'city', 'contextualPicturesCount', 'coordinate', 'listingObjType', 'pdpUrlType', 'name', 'roomTypeCategory', 'isSuperHost', 'isVerified', 'reviewCount', 'yearHosting', 'canInstantBook', 'weeklyPriceFactor', 'structuredStayDisplayPrice', 'price', 'maxGuestCapacity'}

    def start_requests(self):
        url = f"https://www.airbnb.com.vn/s/{self.city}/homes?locale=vi&query={self.city}&price_min={self.price_lb}&price_max={self.price_ub}&cursor=eyJzZWN0aW9uX29mZnNldCI6MywiaXRlbX"
        yield SplashRequest(url=url, callback=self.parse,
                                endpoint="render.html",
                                args={'wait': '0.5'})

    def parse(self, response, **kwargs):
        path = response.xpath("//script[@id='data-deferred-state']/text()").get()
        path = json.loads(path)
        data = path['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['searchResults']
        pagination_info = path['niobeMinimalClientData'][0][1]['data']['presentation']['explore']['sections']['sectionIndependentData']['staysSearch']['paginationInfo']['nextPageCursor']
        data_dict = collections.defaultdict(dict)

        base_url = 'https://www.airbnb.com.vn/rooms/'

        for index, home in enumerate(data):
            if index > 1:
                room_id = home.get('listing').get('id')
                primary_host_passport = None
                if home.get('listing').get('primaryHostPassport'):
                    primary_host_passport = home.get('listing').get('primaryHostPassport')

                url = base_url + home.get('listing').get('id')

                data_dict[room_id]['room_id'] = str(room_id)
                data_dict[room_id]['url'] = str(url)
                data_dict[room_id]['avgRatingLocalized'] = str(home.get('listing').get('avgRatingLocalized'))
                data_dict[room_id]['city'] = str(home.get('listing').get('city'))
                data_dict[room_id]['contextualPicturesCount'] = str(home.get('listing').get('contextualPicturesCount'))
                data_dict[room_id]['coordinate'] = str(home.get('listing').get('coordinate'))
                data_dict[room_id]['listingObjType'] = str(home.get('listing').get('listingObjType'))
                data_dict[room_id]['pdpUrlType'] = str(home.get('pdpUrlType'))
                data_dict[room_id]['name'] = str(home.get('listing').get('name'))
                data_dict[room_id]['roomTypeCategory'] = str(home.get('listing').get('roomTypeCategory'))
                if primary_host_passport:
                    data_dict[room_id]['isSuperHost'] = str(primary_host_passport.get('isSuperhost'))
                    data_dict[room_id]['isVerified'] = str(primary_host_passport.get('isVerified'))
                    stats = primary_host_passport.get('stats')

                    if len(stats) > 0:
                        data_dict[room_id]['reviewCount'] = str(stats[0].get('value'))
                    if len(stats) > 2:
                        data_dict[room_id]['yearHosting'] = str(stats[2].get('value'))

                data_dict[room_id]['canInstantBook'] = str(home.get('pricingQuote').get('canInstantBook'))
                data_dict[room_id]['weeklyPriceFactor'] = str(home.get('pricingQuote').get('weeklyPriceFactor'))
                data_dict[room_id]['structuredStayDisplayPrice'] = str(home.get('pricingQuote').get('structuredStayDisplayPrice').get('primaryLine').get('qualifier'))
                data_dict[room_id]['price'] = str(home.get('pricingQuote').get('structuredStayDisplayPrice').get('primaryLine').get('price'))

                self.export_data.update(data_dict)

        for room_id in data_dict:
            yield SplashRequest(url=f"{base_url+room_id}?locale=vi", callback=self.parse_details,
                                meta={'id': room_id},
                                endpoint="render.html",
                                args={'wait': '0.5'})

        if pagination_info:
            new_url = f"https://www.airbnb.com.vn/s/{self.city}/homes?locale=vi&query={self.city}&price_min={self.price_lb}&price_max={self.price_ub}&cursor={pagination_info}"
            yield SplashRequest(url=new_url, callback=self.parse,
                                endpoint="render.html",
                                args={'wait': '0.5'})

    def close(self, spider, reason):
        with open("out.csv", "w", newline="", encoding='UTF-8') as f:
            fieldnames = ['1', '2', '5']
            writer = csv.DictWriter(f, delimiter="\t", fieldnames=self.header)
            writer.writeheader()
            for record in self.export_data:
                print({'SYSTEM_WORKSPACE': 'Value 1', 'price': 1, 'name': "true"}, self.export_data[record])

                writer.writerow(self.export_data[record])

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
            room['maxGuestCapacity'] = str(max_guest_capacity)
            for amenity in list_amenities:
                room[amenity['icon']] = str(amenity['available'])
                self.header.add(amenity['icon'])
        self.export_data[id] = room


