import MySQLdb
from datetime import datetime

import socket

agent = MySQLdb.connect(	host='127.0.0.1',
							port=33060,
							user='homestead',
							passwd='secret',
							db='csgo',
							charset='utf8',
							use_unicode=True )
agent.autocommit(True)
cursor = agent.cursor()


def is_group_exist(link):
	global cursor
	sql = "SELECT EXISTS( SELECT 1 FROM groups WHERE link = %s )"
	cursor.execute(sql, link)
	return cursor.fetchone()[0]

def set_time_zone(time_zone_str):
	global cursor
	agent.time_zone = time_zone_str

def add_group(name, link):
	global agent
	values = (name, link)
	sql = 	u"INSERT INTO groups (name,link,created_at,updated_at) "\
			"VALUES (%s,%s,now(),now())"

	cursor.execute(sql, values)
	return cursor.lastrowid

def add_weapon(name, link, img_link, group_id):
	global cursor
	values = ( unicode(name), unicode(link), unicode(img_link), group_id)
	sql = 	u"INSERT INTO weapons (name,link,img_link,group_id,created_at,updated_at) "\
			"VALUES (%s,%s,%s,%s,now(),now())"

	cursor.execute(sql, values)
	return cursor.lastrowid

def get_config():
	global cursor

	sql = "SELECT name, value, type FROM configs"
	cursor.execute(sql)
	results = cursor.fetchall()

	config = {}

	for row in results:
		name = row[0]
		value = row[1]
		datatype = row[2]

		if datatype == 'int':
			converted_value = int(value)
		elif datatype == 'decimal':
			converted_value = float(value)
		elif datatype == 'string':
			converted_value = value
		elif datatype == 'boolean':
			converted_value = bool(int(value))

		config[name] = converted_value

	return config

def get_group_link(group_id):
	global cursor
	sql = 	"SELECT link FROM groups WHERE id = %s"

	cursor.execute(sql, group_id)
	result = cursor.fetchone()
	if result and len(result) > 0:
		return result[0]
	else:
		return None

def get_weapon(weapon_id):
	global cursor
	sql =	"SELECT name, link, group_id, last_price, avg_price"\
			" FROM weapons WHERE id = %s"
	cursor.execute(sql, weapon_id)
	row = cursor.fetchone()
	weapon = {}
	if row and len(row) > 0:
		weapon['name'] = row[0]
		weapon['link'] = row[1]
		group_id = row[2]
		weapon['group_link'] = get_group_link(group_id)
		weapon['last_price'] = row[3]
		weapon['avg_price'] = row[4]
		return weapon
	else:
		return None

def update_prices(weapon_id, last_price, avg_price):
	global cursor
	sql = "UPDATE weapons SET last_price = %s, avg_price = %s, updated_at=now() WHERE id = %s"
	values = (last_price, avg_price, weapon_id)
	cursor.execute(sql, values)

def get_weapons():
	global cursor
	sql =	"SELECT name, link, group_id, last_price, avg_price, alert_price, id, "\
			"is_alert_price_active, is_alert_percentage_active, is_monitored "\
			" FROM weapons"
	cursor.execute(sql)
	results = cursor.fetchall()
	return [{'name':w[0],'link':w[1],'group_id':w[2],
			'last_price':w[3],'avg_price':w[4],'alert_price':w[5], 'id':w[6],
			'is_alert_price_active':w[7], 'is_alert_percentage_active':w[8],
			'is_monitored':w[9]}
			for w in results]

def alert_percentage(weapon, price):
	global cursor
	drop_percent = (weapon['avg_price'] - price)*100/weapon['avg_price']

	message = "%s drops %0.2f %%. avg: $%0.2f price: $%0.2f" % (
		weapon['name'],
		drop_percent,
		weapon['avg_price'], 
		price )

	set_alert_status(weapon['id'], 'percentage', True)
	add_notification(weapon['id'], message)

def alert_price(weapon, price):
	global cursor
	message = "%s drops lower than alert price $%0.2f. avg: $%0.2f price: $%0.2f" % (
		weapon['name'],
		weapon['alert_price'],
		weapon['avg_price'], 
		price )

	set_alert_status(weapon['id'], 'price', True)
	add_notification(weapon['id'], message)


def add_notification(weapon_id, content):
	global cursor
	values = (	unicode(content), 
				weapon_id )
	sql = 	u"INSERT INTO notifications (content,weapon_id,created_at,updated_at) "\
			"VALUES (%s,%s,now(),now())"

	cursor.execute(sql, values)
	return cursor.lastrowid

def set_alert_status(weapon_id, alert_name, is_active):
	global cursor
	alert_column_name = "is_alert_%s_active" % alert_name
	sql = "UPDATE weapons SET "+alert_column_name+" = %s WHERE id = %s"
	values = (is_active, weapon_id)
	cursor.execute(sql, values)


if __name__ == '__main__':

	agent.time_zone = "+8:00"
	w=get_weapon(1)