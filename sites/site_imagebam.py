#!/usr/bin/python

from basesite  import basesite
from threading import Thread
import time, os

"""
	Downloads imagebam albums
"""
class imagebam(basesite):
	
	"""
		Ensure URL is relevant to this ripper.
		Return 'sanitized' URL (if needed).
	"""
	def sanitize_url(self, url):
		if not 'imagebam.com/' in url: 
			raise Exception('')
		if 'imagebam.com/image/' in url:
			r = self.web.get(url)
			galleries = self.web.between(r, "class='gallery_title'><a href='", "'")
			if len(galleries) == 0 or '/gallery/' not in galleries[0]:
				raise Exception("Required '/gallery/' not found")
			url = galleries[0]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
		while u.endswith('/'): u = u[:-1]
		name = u[u.rfind('/')+1:]
		return 'imagebam_%s' % name

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, "href='http://www.imagebam.com/image/", "'")
		for index, link in enumerate(links):
			link = "http://www.imagebam.com/image/%s" % link
			self.download_image(link, index + 1, total=len(links)) 
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			time.sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	def download_image_thread(self, url, index, total):
		r = self.web.get(url)
		imgs = self.web.between(r, ';" src="', '"')
		if len(imgs) == 0:
			self.log('unable to find image - %s' % url)
			self.thread_count -= 1
			return
		img = imgs[0]
		if self.urls_only:
			self.add_url(index, img, total)
			self.thread_count -= 1
			return
		filename = img[img.rfind('/')+1:]
		saveas = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
		if os.path.exists(saveas):
			self.image_count += 1
			self.log('download (%d/%d) exists - %s' % (index, total, saveas))
		elif self.web.download(img, saveas):
			self.image_count += 1
			self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(saveas), img))
		else:
			self.log('download (%d/%d) failed - %s' % (index, total, img))
		self.thread_count -= 1

