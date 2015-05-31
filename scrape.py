import os.path
import pickle
import time
import datetime
import re
import db
import sys
import traceback
from decimal import *

from bs4 import BeautifulSoup
from bs4 import element
from selenium import webdriver

def get_price(link, browser):
	browser.get(link)
	bs = BeautifulSoup(browser.page_source)
	row = bs.find('div', class_='market_listing_row')

	price_str = row.find('span', class_='market_listing_price_with_fee').string.strip()
	while not re.match(r'\$\d+\.\d\d USD',price_str):
		row = row.next_sibling
		while isinstance(row, element.NavigableString):
			row = row.next_sibling

		price_str = row.find('span', class_='market_listing_price_with_fee').string.strip()

	match = re.match(r'\$(\d+\.\d\d) USD',price_str)
	
	return Decimal(match.group(1))

browser = webdriver.Firefox()
cookies = None

if os.path.isfile('cookies.pkl'):
	browser.get('http://steamcommunity.com/market?l=english')
	cookies = pickle.load(open('cookies.pkl', 'rb'))
	for cookie in cookies:
		new_cookie={}
		new_cookie['name']=cookie['name']
		new_cookie['value']=cookie['value']
		browser.add_cookie(new_cookie)

	while(1):
		config = db.get_config()
		for weapon in db.get_weapons():
			if weapon['is_monitored']:
				try:
					price = get_price(weapon['link'], browser)
					avg_price = weapon['avg_price']

					#price alert
					if ( weapon['alert_price'] != 0 
					and not weapon['is_alert_price_active'] 
					and price < weapon['alert_price'] ):
						db.alert_price(weapon, price)

					if avg_price != 0:
						#percentage alert 
						if ( not weapon['is_alert_percentage_active'] 
						and price < (avg_price * config['default_notify_percentage'] / 100) ):
							db.alert_percentage(weapon, price)

						#calculate avg price
						avg_price = round( ( avg_price * ( config['avg_size'] - 1) + price ) 
										/ config['avg_size'] ,2)
					else:
						avg_price = price

					#reset active flag
					if not price < weapon['alert_price']:
						db.set_alert_status(weapon['id'], 'price', False)
					if not ( price < (avg_price * config['default_notify_percentage'] / 100) ):
						db.set_alert_status(weapon['id'], 'percentage', False)

					#update price and avg price
					db.update_prices(weapon['id'], price, avg_price)

				except Exception, err:
					print('id(%d):\n%s' % (weapon['id'], traceback.format_exc() ))

				#sleep	
				time.sleep(config['delay_sec'])


else:
	browser.get('https://steamcommunity.com/login/home/?goto=0')
	browser.find_element_by_name('username').send_keys('xzcvbarwet24fds')
	browser.find_element_by_name('password').send_keys('2dw3xkbn')
	browser.find_element_by_class_name('btn_green_white_innerfade').click()
	time.sleep(25)

	pickle.dump( browser.get_cookies() , open('cookies.pkl','wb'))



