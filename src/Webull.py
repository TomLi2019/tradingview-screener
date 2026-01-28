import json
import math
import time
from datetime import datetime

import pandas as pd
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Webull():


	def __init__(self,headless=False):
		if headless == True:
			options = Options()
			options.headless = True
			self.driver = webdriver.Firefox(options=options)

		else:
			self.driver = webdriver.Firefox()



	def quote(self, url = "https://www.webull.com/quote/"):

		self.url = url
		self.driver.get(self.url)

		try:
			WebDriverWait(self.driver, 45).until(EC.element_to_be_clickable((By.CLASS_NAME, "csr218")))
			# time.sleep(5)
			#element = self.driver.find_element("class_name", "csr220").text
			element = self.driver.find_element("xpath", "/html/body/div/div[4]/div[3]/div[1]/div[2]/div[2]").text
			# print(element)

			json_string = json.dumps(element)
			print(json_string)
			return json_string

		except:
			self.driver.quit()
			print("Error. Connection Timed Out.")
		time.sleep(5)


	def get_time(self):

		# Allocating, shorting and covering available 6am to 8pm EST (<--- not ET)

		tz = timezone('US/Eastern')
		now = datetime.now(tz)
		weekday = now.weekday()
		hour    = int(now.strftime("%H"))
		minute  = int(now.strftime("%M"))

		time_now = [weekday, hour, minute]
		return time_now

	def closebrowser(self):
		# self.driver.close()
		self.driver.quit()
