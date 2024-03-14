from bs4 import BeautifulSoup as bs
import datetime
import requests



def get_schedule(url):
	response = requests.get(url)
	html = bs(response.content, features='html5lib')
	tables = html.findAll('table', attrs={'class': 'table table-ekorpen text-light'})
	body_tags = tables[0].findAll('tbody')
	tr_tags = body_tags[0].findAll('tr')
	games = []
	for tr_tag in tr_tags:
		td_tags = tr_tag.findAll('td')
		games.append((td_tags[0].text.strip(), datetime.datetime.strptime(td_tags[1].text.strip(), "%Y-%m-%d %H:%M")))

	print("Games generated at ", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
	return games