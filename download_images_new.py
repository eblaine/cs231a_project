import requests
from scipy import ndimage, misc
from io import BytesIO, StringIO
import numpy as np
from six.moves import cPickle as pickle
import platform
from sys import stdout 
from PIL import Image 
import gzip

stdout.flush()

# client = pymongo.MongoClient()
# db = client.rijks
n = 10000
currIndex = 0
currBatch = 0
# datadict = {'data': np.zeros(shape=(n, 3, 256, 256)), 'labels': []}
datadict = {'data': [], 'labels': []}
filename_base = 'data/data_batch_'

'''
resize_image

Downsamples and crops img to 256 x 256

params: img - rgb array for the a raw image from Rijksmuseum collection 

returns:
center_crop - img, resized and cropped to 256
resized - original image, resized s.t. the longer side is length 256
'''
def resize_image(img):
	# get shape of image
	W, H = img.size

	# determine whether length or width is smaller
	bigger = max(H, W)
	smaller = min(H, W)
	ratio = float(bigger) / float(smaller)

	# resize to make smaller dimension 256
	if W > H:
		shape = (int(256 * ratio), 256)
	else: 
		shape = (256, int(256 * ratio))

	# resized = misc.imresize(img, shape)
	resized = img.resize(shape, Image.ANTIALIAS)

	# crop larger dimension using middle 256 elements
	# re_H, re_W, re_c = resized.shape
	re_W, re_H = resized.size
	# print 'resized', re_H, re_W

	#row_start_index = re_H/2 - 128
	#col_start_index = re_W/2 - 128
	center_x, center_y = (re_W / 2, re_H / 2)
	# print 'center indices', center_x, center_y
	left_side = center_x - 128
	right_side = center_x + 128
	top = center_y - 128
	bottom = center_y + 128

	cropped_bounding_box = (left_side, top, right_side, bottom)
	center_crop = resized.crop(cropped_bounding_box)

	return center_crop, resized


# utility function for later!
'''
get_rgb:

Downloads image located at url and returns the full rgb array (normalized)

params: url - location of full image 
returns:
1. 256 x 256 crop of image
2. rectangular resized image (one side is length 256)
'''
def get_rgb(url):
	try:	
		# r = requests.get(url)
		r = requests.get(url, stream=True)
	except requests.exceptions.ConnectionError:
		return []
	
	# full image, needs downsampling to 256 x 256
	# full_image = ndimage.imread(BytesIO(r.content))
	full_image = Image.open(r.raw)
	crop, small_image = resize_image(full_image)

	# return crop / 256., small_image / 256.
	return crop, small_image


'''
save_image

Mostly leftover from mongo, but adds data and labels to final data output

currIndex - current data point number
'''
def save_image(cropped, resized, obj_id, currIndex):
	# try: 
	# 	db.images.insert({'obj_id': obj_id, 'cropped': cropped, 'downsampled': resized})
	# except pymongo.errors.DuplicateKeyError:
	# 	return
	# plt.imshow(resized)
	# plt.show()

	# save as N x C x H x W


	# datadict['data'][currIndex, :, :, :] = cropped.transpose(2, 0, 1)
	datadict['data'].append(cropped)
	datadict['labels'].append(obj_id)


'''
load_pickle

Returns saved data in f as a dictionary
'''
def load_pickle(f):
    version = platform.python_version_tuple()
    if version[0] == '2':
        return  pickle.load(f)
    elif version[0] == '3':
        return  pickle.load(f, encoding='latin1')
    raise ValueError("invalid python version: {}".format(version))

'''
pickle_and_next_batch

Saves current datadict to a .pkl (scheme is data/data_batch_<currBatch>.pkl)
'''
def pickle_and_next_batch(currBatch):
	f = gzip.GzipFile(filename_base + str(currBatch) + '.pgz', 'wb')
	pickle.dump(datadict, f)
	f.close()


# JUST A QUICK TEST...not used now
def load_batch_test(filename):
	with open(filename, 'rb') as f:
		datadict = load_pickle(f)
		X = datadict['data']
		Y = datadict['labels']
		X = X.reshape(n, 3, 256, 256).transpose(0,2,3,1).astype("float")
		X = X.transpose(0, 3, 1, 2) # N H W C --> N C H W	
		return X, Y

# loop over file of urls and obj_id's to save RGB arrays
with open('painting_urls.tsv', 'r') as f:
	for line in f:
		obj_id, url = line.strip().split('\t')
		img = get_rgb(url)
		cropped, resized = img 
		if currIndex >= n:
			pickle_and_next_batch(currBatch)
			currBatch += 1
			currIndex = 0


		save_image(cropped, resized, obj_id, currIndex)
		currIndex += 1	
		stdout.flush()	

# leftover from mongo
# for painting_json in db.art.find():
# 	url = painting_json.get('url')
# 	if url != '':
# 		img = get_rgb(url)
# 		if img == []:
# 			continue
# 		cropped, resized = img
# 		if currIndex >= n:
# 			pickle_and_next_batch(currBatch)
# 			currBatch += 1
# 			currIndex = 0
# 			print currBatch

# 		save_image(cropped, resized, painting_json.get('obj_id'), currIndex)
# 		currIndex += 1
		
			