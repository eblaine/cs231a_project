import requests
import json
import pymongo
from sys import maxint
from scipy import ndimage
from io import BytesIO

num_pages = maxint
num_per_page = str(10)
client = pymongo.MongoClient()
db = client.rijks


def save_painting(data):
	paint_id = data.get(u'objectNumber')
	title = data.get(u'title')
	colors_norm = data.get(u'colorsWithNormalization')
	desc = data.get(u'description')

	makers = data.get(u'principalMakers')
	artists = [maker.get(u'name') for maker in makers] if makers is not None else []

	plaque_english = data.get(u'plaqueDescriptionEnglish')

	dating = data.get(u'dating')
	date = dating[u'year'] if dating is not None else "0000"

	img = data.get(u'webImage')
	url = ''
	if img is not None:
		url = img.get(u'url') 
	# rgb_array = get_rgb(data[u'webImage'][u'url']) if url != '' else [] 

	obj = {
		'obj_id': paint_id,
		'title': title,
		'colors_norm': colors_norm,
		'description': desc,
		'artists': artists,
		'plaque': plaque_english,
		'date': date,
		'url': url
		# 'rgb_array': rgb_array
	}
	try: 
		db.art.insert(obj)
	except pymongo.errors.DuplicateKeyError:
		return


def get_painting_json():
	# outfile = open('rijks_test.out','w')
	key = 'qm6W62Ae'
	base = 'https://www.rijksmuseum.nl/api/en/'
	url = base + '/collection'

	for i in xrange(num_pages):
		try:
			r = requests.get(url + '?key=' + key + '&format=json&ps=' + num_per_page + '&p=' + str(i))
		except requests.exceptions.ConnectionError:
			continue
		data = json.loads(r.text)
		paintings = data[u'artObjects']
		for painting in paintings:
			detail_url = url + '/' + painting[u'objectNumber'] + '?key=' + key + '&format=json'
			try:
				r_detail = requests.get(detail_url)
			except requests.exceptions.ConnectionError:
				continue
			painting_data = json.loads(r_detail.text)[u'artObject']
			
			save_painting(painting_data)
		# outfile.write(r.text.encode('utf-8'))



get_painting_json()
# save_images()