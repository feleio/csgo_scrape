import os.path
import pickle
import time
import datetime
import re
import db
import sys
import traceback

from bs4 import BeautifulSoup
from selenium import webdriver

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

	error_links = []
	with open('weapon_list.txt') as f:
		for group_link in f.readlines():
			if not re.match(r"^\s*$", group_link):
				try:
					group_link = group_link.strip()
					browser.get(group_link)
					bs = BeautifulSoup(browser.page_source)
					group_name = bs.find('span', class_='game_button_contents').input['value']

					if not db.is_group_exist(group_link):
						weapon_as = bs('a',class_='market_listing_row_link')
						if len(weapon_as) == 0:
							raise Exception('parse error')

						group_id = db.add_group(group_name, group_link)

						for weapon_a in weapon_as:
							link = weapon_a['href']
							
							name = weapon_a.find('span',class_='market_listing_item_name').string
							img_link = weapon_a.find('img', class_='market_listing_item_img')['src']
							db.add_weapon(name, link, img_link, group_id)

						print "[successfully scrapped]:\n %s" % group_link
					else:
						print "[already exists]:\n %s" % group_link
				except:
					print "[Unexpected error]:\n", traceback.format_exc()
					error_links.append(group_link)

	#clear text in file except error link
	with open('weapon_list.txt', 'w') as f:
		for error_link in error_links:
			f.write(error_link+'\n')
			

else:
	browser.get('https://steamcommunity.com/login/home/?goto=0')
	browser.find_element_by_name('username').send_keys('xzcvbarwet24fds')
	browser.find_element_by_name('password').send_keys('2dw3xkbn')
	browser.find_element_by_class_name('btn_green_white_innerfade').click()
	time.sleep(25)

	pickle.dump( browser.get_cookies() , open('cookies.pkl','wb'))
