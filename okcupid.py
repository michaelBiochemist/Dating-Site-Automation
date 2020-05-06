#!/usr/bin/python3

import selenium
from selenium.webdriver import Firefox, ActionChains
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import traceback
import json
import yaml

main_site = 'https://www.okcupid.com'
driver = Firefox()
message_error_count = 0
profile_iterator = 0
exclude_list = load_exclude_list()
action_options = load_action_options()
opener = 'Are you a sheep cause your body is unbaaaaalievable\n\nOk, that was cheesy. I saw your profile and thought "She must get 20 messages a day. Come up with something original and see if there\'s a fun person behind all the pretty."'
# may want to add "has kid(s)"

def load_exclude_list():
	filepath = './exclusion_keywords.yaml'
	with open(filepath) as f:
		exclude_list = yaml.safe_load(f)
	return exclude_list

def load_action_options():
	filepath = './action_options.json'
	with open(filepath) as f:
		action_options = json.load(f)
	return action_options

def sleepy():
	time.sleep(6)

def expect_all(*args):
	global driver
	xpath = args[0]
	seconds_waited = 0
	if len(args) != 1:
		seconds_waited = args[1]
	elems = driver.find_elements_by_xpath(xpath)
	if len(elems) == 0:
		time.sleep(1)
		if seconds_waited == 20:
			print('waited 20 seconds, returning false')
			return False
		else:
			return(expect_all(xpath,seconds_waited+1))
	else:
		return elems

def expect_first(*args):
	elems = expect_all(*args)
	if not elems:
		return False
	return(elems[0])

def login(account_name):
	global main_site
	global driver
	account_file = open('accounts.json')
	account  = account_file.read()
	account_file.close()
	account = json.loads(account)

	driver.get(main_site)
	a = expect_first('.//a')
	if a.get_attribute('href') == 'https://www.okcupid.com/login':
		#a.click()
		driver.get(a.get_attribute('href'))
		sleepy()
		email = driver.find_element_by_id('username')
		password = driver.find_element_by_id('password')
		email.send_keys(account[account_name]['uname'])
		password.send_keys(account[account_name]['passw'])
		password.send_keys(Keys.RETURN)
		sleepy()

	print('closing react modal')
	j = expect_first(".//button[@class='reactmodal-header-close']",17)
	if j:
		j.click()

	print('closing accept cookies bar')
	take_cookie = expect_first(".//button[@id='onetrust-accept-btn-handler']")
	if take_cookie:
		take_cookie.click()
	sleepy()

def extract_profile_data():
	profile = {}
	profile['id'] =  driver.current_url.split('/')[-1:][0].split('?')[0]
	profile['date grabbed'] = datetime.now().isoformat()
	profile['details'] = []
	profile['essays'] = []
	profile['username'] = expect_first(".//div[@class='profile-basics-username']").get_attribute('innerText')
	profile['age'] = expect_first(".//span[@class='profile-basics-asl-age']").get_attribute('innerText')
	profile['location'] = expect_first(".//span[@class='profile-basics-asl-location']").get_attribute('innerText')
	profile['match'] = expect_first(".//span[@class='profile-basics-asl-match']").get_attribute('innerText')
	details = expect_all(".//div[@class='matchprofile-details-text']",18)
	essays = expect_all(".//div[@class='profile-essay']",18)
	for det in details:
		profile['details'].append(det.get_attribute('innerText'))
		if essays:
			for essay in essays:
				profile['essays'].append(essay.get_attribute('innerText'))
	intro = driver.find_elements_by_xpath(".//div[starts-with(@class,'firstmessage') and contains(@class,'body-text')]")
	if len(intro) != 0:
		profile['intro message'] = intro[0].get_attribute('innerHTML')
	return profile
	#intro = fun.driver.find_elements_by_xpath(".//div[starts-with(@class,'firstmessage') and contains(@class,'body-text')]")

def filter_profile(profile):
	global exclude_list
	try:
		for exclude in exclude_list:
			for detail in profile['details']:
				if exclude.lower() in detail.lower():
					return False
	except:
		print('there was an error filtering for profile '+profile['username']+' id: '+profile['id'])
	return True

def grab_pictures(profile):
	global driver
	thumb = expect_first(".//div[@class='profile-thumb']")
	thumb.click()
	time.sleep(2)
	images = driver.find_elements_by_xpath(".//img[@class='photo-overlay-image-content']")
	i = 0
	for img in images:
		driver.save_screenshot('images/'+profile['id']+'_'+str(i)+'.png')
		i+=1
		try:
			time.sleep(1)
			img.click()
		except:
			time.sleep(3)
			img.click()
	driver.back()

def navigate(locus):
	global driver
	navbar = expect_all(".//div[@class='navbar-link-icon-container']")
	if locus == 'search':
		navbar[2].click()
	elif locus == 'matches':
		navbar[3].click()
		tabs = expect_all(".//section/div/div/span")
		tabs[2].click()
	elif locus == 'intros':
		navbar[3].click()
		tabs = expect_all(".//section/div/div/span")
		tabs[1].click()
	elif locus == 'doubletake':
		navbar[0].click()
	else:
		driver.get('https://www.okcupid.com/home')

def double_press(buttons):
	try:
		buttons[0].click()
	except:
		buttons[1].click()
	sleepy()

def send_message(message):
	global driver
	try:
		mbox = expect_all(".//textarea[@class='messenger-composer']",18)
		mbox[0].send_keys(message)
		time.sleep(2)
		buttons = driver.find_elements_by_xpath(".//button[@class='messenger-toolbar-send']")
		double_press(buttons)
		retvalue = True
	except:
		retvalue = False
	try:
		buttons = expect_all(".//button[@class='messenger-user-row-close']",18)
		if buttons:
			double_press(buttons)
		buttons = expect_all(".//button[@class='connection-view-container-close-button']",18)
		if buttons:
			double_press(buttons)
	except:
		print('couldn\'t close box')
	return retvalue

def interact_profile(action, profile_data, message):
	global driver
	sleepy()
	print(action)
	pass_button = driver.find_elements_by_xpath(".//button[@id='pass-button']")
	like_button = driver.find_elements_by_xpath(".//button[@id='like-button']")
	unmatch_button = driver.find_elements_by_xpath(".//button[@id='unmatch-button']")
	msg_button = []

	for button in pass_button:
		if button.get_attribute('innerText') == 'MESSAGE':
			msg_button.append(button)

	if not filter_profile(profile_data):
		action = 'unlike'

	if action ==  'like':
		if len(like_button) == 0:
			return 'missing like button'
		return 'liked'
	elif action ==  'like and message':
		print('doing action like and message')
		if len(like_button) == 0:
			return 'missing like button'
		double_press(like_button)
		msg_stat = send_message(message)
		if msg_stat == True:
			return 'liked and messaged'
		else:
			return 'liked'
	elif action ==  'message':
		double_press(msg_button)
		msg_stat = send_message(message)
		if msg_stat == True:
			return 'messaged'
		else:
			return 'failed'
	elif action ==  'unlike':
		if len(unmatch_button) == 0:
			double_press(pass_button)
		else:
			double_press(unmatch_button)
		return 'rejected'
	else:
		return 'no action'

def iterate_error_count():
	global message_error_count
	global profile_iterator
	message_error_count+=1
	if message_error_count == 3: # try 3 times for any one person
		message_error_count = 0
		profile_iterator+=1

def action_list(action):
	global message_error_count
	global profile_iterator
	global action_options
	global opener
	current_action = action_options[action]
	try:
		while True:
			navigate(current_action['location'])
			sleepy()
			logfile = open('okcupid.log','a')
			#Go through list of girls that i like
			profiles = expect_all(".//div[@class='usercard-thumb']")
			if len(profiles) <= profile_iterator:
				logfile.close()
				break
			profiles[profile_iterator].click()
			time.sleep(4)
			pdata = extract_profile_data()
			grab_pictures(pdata)
			pdata['status'] = interact_profile(current_action['action'],pdata,opener)
			pdata['opener'] = opener
			write_status = '|'.join([pdata['username'],pdata['age'],pdata['location'],action,pdata['status'],pdata['date grabbed'],pdata['id']])
			print(pdata['status'])
			logfile.write('\n'+write_status)
			if action == 'collect intros':
				pro_file = open('profiles/men/'+pdata['id'],'w')
			else:
				pro_file = open('profiles/'+pdata['id'], 'w')
			if pdata['status'] in ['no action','failed']:
				iterate_errror_count()
			pro_file.write(json.dumps(pdata, sort_keys=True,indent=4))
			pro_file.close()
			logfile.close()
	except:
		iterate_error_count()
		action_list(action)

def singletake():
	global action_options
	global opener
	global message_error_count
	current_action = action_options['like from search']
	logfile = open('okcupid.log','a')
	navigate('doubletake')
	link = expect_first('.//div[@class="cardsummary-reflux-item cardsummary-reflux-profile-link"]')
	link.click()
	time.sleep(3)
	pdata = extract_profile_data()
	grab_pictures(pdata)
	pdata['status'] = interact_profile(current_action['action'],pdata,opener)
	pdata['opener'] = opener
	write_status = '|'.join([pdata['username'],pdata['age'],pdata['location'],'doubletake',pdata['status'],pdata['date grabbed'],pdata['id']])
	print(pdata['status'])
	logfile.write('\n'+write_status)
	logfile.close()

def doubletake():
	global driver
	while True:
		try:
			singletake()
		except:
			ActionChains(driver).send_keys(Keys.ESCAPE).perform()
			singletake()


if __name__== '__main__':
	login('real')
	#action_list('like from search')
	#doubletake()
	action_list('message likes')
	#login('catfish')
	#action_list('collect intros')
# interact with search page
#navbar = driver.find_elements_by_xpath(".//a[@class='navbar-link']")
#navbar[2].click()
#cards = fun.driver.find_elements_by_xpath(".//div[@class='usercard']")
#cards[0].click()
#like = fun.expect_first(".//button[@id='like-button']")
#if len(like.get_attribute('innerText')) > 5
