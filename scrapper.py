from bs4 import BeautifulSoup as bs
import requests
import json
from urllib.parse import quote
import re, time

# GET request
def get_as_soup(url):
    r = requests.get(url)
    if r.status_code == 200:
    	soup = bs(r.text, 'html.parser')
    	return soup
    else:
        return Exception('not found')

# POST Request
def post_as_soup(url, data):
	r = requests.post(url, data=data)
	if r.status_code == 200:
		soup = bs(r.content, 'lxml')
		return soup
	else:
		return Exception('nout found')

def get_metas(metas):
	m = {}
	for meta in metas:
			for i,e in enumerate(meta.select('li')):
				text = e.text.strip()
				if i==0:
					m.update({x.strip(): y.strip() for x, y in [g.strip().split(':') for g in text.split(',')]})
					continue
				m.update({x.strip(): y.strip() for x, y in [text.split(':')]})
	return m

def get_article(id):
    soup = get_as_soup("https://www.asjp.cerist.dz/en/article/{}".format(id))
    info = soup.select('.descarticle > div:nth-child(1) > p:nth-child(1)')
    info = tuple([el.strip() for el in info[0].text.split('\n') if el.strip() != ''])
    revue, nemuro, date = info
    revue_link = soup.select('.full-width-media-text > p > a')[0]['href'].strip()
    title = soup.select(
        '.descarticle > div:nth-child(1) > h2:nth-child(2)')[0].text.strip()
    authors = []
    description = soup.select(
        '.descarticle > div:nth-child(1) > p:nth-child(6)')[0].text.strip()
    for author in soup.select('.descarticle > div:nth-child(1) > p:nth-child(4) > a'):
        authors.append(author.text.strip())
    link = soup.select('.col-lg-offset-8 > a:nth-child(1)')[0]['href']
    image = soup.select('.col-center > img:nth-child(1)')[0]['src'].strip()
    tags = re.split('،|؛|-', soup.select(
        '.descarticle > div:nth-child(1) > p:nth-child(8)')[0].text)
    tags = [tag.strip() for tag in tags if tag.strip() != '']

    return {'id': id, 'revue': revue,'revue_link': revue_link, 'title': title, 'description': description,
    		'nemuro': nemuro, 'date': date, 'authors': authors, 'link': link, 'image': image, 'tags': tags}

def get_revue(id):
	print(id)
	soup = get_as_soup('https://www.asjp.cerist.dz/en/PresentationRevue/{}'.format(id))
	title= soup.select('.intitule_revue > h4')[0].text.strip()
	metas = get_metas(soup.select('.meta-search'))
	description = soup.select('.intitule_revue > p')[0].text.strip()
	image = soup.select('.col-center > img:nth-child(1)')[0]['src'].strip()

	stats_arr = [x.text.lower() for x in [y for y in soup.select('.row.NVA > div > div > p')]]
	stats_arr.reverse()
	if len(stats_arr)>6:
		stats_arr = stats_arr[0:6]
	print(stats_arr)
	stats = dict(stats_arr[i:i+2] for i in range(0, len(stats_arr), 2))

	articles = {}
	for x in soup.find_all("a", attrs={"class": "list-group-item"}):
		article = [y.strip() for y in x.get_text('*').split('*') if y.strip() != '']
		article = {article[1]: {'total': article[0], 'link': x['href'].strip()}}
		articles.update(article)

	res = {'title': title, 'meta': metas, 'description': description, 'image': image, 'most_viewed': articles}
	res.update(stats)
	return res

def get_revue_articles(id, volume):
	soup = get_as_soup('https://www.asjp.cerist.dz/en/Articles/{}'.format(id))
	start_time = time.perf_counter()


	def process_articles(x):
		articles = {}
		for article in x.select('h4'):
			article_dict = {}
			article_text = [g.replace('\n', '').strip() for g in article.get_text('*').split('*') if g.strip()!= '']
			articles[article_text[0]] = {} 
			link = article.select('a')[0]['href'].strip()
			authors = [a.strip() for a in article_text[1].replace(',', '').split('\xa0')]
			if len(article_text) <= 5:
				date = article_text[3].replace(',', '')
				page = article_text[4].replace(',', '')
			else:
				date = article_text[5].replace(',', '')
				page = article_text[6].replace(',', '')

			articles[article_text[0]] = {'link': link, 'authors': authors, 'date': date, 'page': page} 
		return articles

	Volumes = {}
	for t, g in zip(soup.select('.opened-for-codepen')[1:], soup.select('h2')):
		volumes_arr = [re.sub(r'\s+', ' ', k.replace('\n', '').strip()) for k in g.text.split('\xa0') if k.strip()!='']
		Volumes[volumes_arr[0]] = {'date': volumes_arr[1]}
		Nemuros = {}
		for i, c in enumerate(t.select('h3')):
			nemuro_arr = [" ".join(k.replace('\n', '').strip().split()) for k in c.text.split('\xa0') if k.strip()!='']
			Nemuros[nemuro_arr[0]] = {'date': nemuro_arr[1], 'special': True if len(nemuro_arr)>2 else False}
			
			if volume != -1: 
				Nemuros[nemuro_arr[0]].update({'articles': process_articles(t)})
			else:
				Nemuros[nemuro_arr[0]].update({'articles': {}})
		
		Volumes[volumes_arr[0]].update({'numéros': Nemuros})

	total_time = time.perf_counter() - start_time
	time_in_ms = int(total_time * 1000)
	print(time_in_ms)
	if volume > 0:
		try:
			return Volumes['Volume {}'.format(volume)]
		except KeyError:
			return {'error': 'no volume {}'.format(volume)}
	else:
		return Volumes
	

def searchRevue(query, issn, acronyme, page=1):
	soup = get_as_soup("https://www.asjp.cerist.dz/en/researchRevue?titreRevue={}&issn={}&acronyme{}=&clas=A%2CB%2CC%2CNC&domaine=2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28%2C29%2C30&page={}".format(query, issn, acronyme, page))
	articles = soup.select(".search-result.row")
	revues = {}
	titles = []
	metas_revue = []
	classes = []
	links = []
	images = []
	for article in articles:
		titles.append(article.select("a.lien")[0].text.strip())
		metas = article.select('.meta-search')
		metas_revue.append(get_metas(metas))
		classes.append(re.findall(r'(A|B|C|Non Classé)',article.select('span.class')[0].text.strip())[0])
		links.append(article.select('a.lien')[0]['href'].strip())
		images.append(article.select('img')[0]['src'].strip())


	for i in range(len(articles)):
		revues[i] = {}
		try:
			revues[i] = {'title': titles[i], 'link': links[i], 'classes': classes[i], 'meta': metas_revue[i],
							'image': images[i]}
		except KeyError:
			continue

	return revues

def search(query, page=1):
	soup = get_as_soup("https://www.asjp.cerist.dz/en/getRechercheGeneral/" + quote("{}_tous_{}".format(query, page)))
	results = soup.select('div.full-width-media-text')
	titles = []
	links = []
	descriptions = []
	authors = []
	dates = []
	articles = {}
	for result in results:
		titles.append(result.select('table > thead > tr > th > h4 > a')[0].text.strip())
		links.append(result.select('table > thead > tr > th > h4 > a')[0]['href'])
		descriptions.append(result.select('table > tbody > tr > td > p')[0].text.strip())
		for el in result.select('table > tbody:nth-child(2) > tr:nth-child(3) > td:nth-child(2) > p:nth-child(1)'):
			el = [x.strip() for x in el.text.split(',') if x.strip() != '']
			authors.append(el)
		article_dates = result.select('div.full-width-media-text > table > tbody > tr > td > a > class')

		try:
			if len(article_dates) > 1:
				dates.append(article_dates[1].text.strip())
			else:
				dates.append(article_dates[0].text.strip())
		except:
			pass

	for i in range(len(results)):
		articles[i] = {}
		try:
			articles[i] = {'title': titles[i], 'link': links[i], 'authors': authors[i], 'date': dates[i],
							'description': descriptions[i]}
		except KeyError:
			continue

	return articles
