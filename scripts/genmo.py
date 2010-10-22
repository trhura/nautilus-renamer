#!/usr/bin/env python

import os;
import sys;
import re;
import subprocess;

def gen_mo_files (podir, localedir):

	pattern = re.compile('^([a-zA-Z_]+)\.po$')

	for pofile in sorted (os.listdir(podir)):
		matches = pattern.match (pofile)

		if matches:
			poname, ext = os.path.splitext (pofile)
			modir = os.path.join (localedir, poname, 'LC_MESSAGES')

			if not os.path.exists (modir):
				print "Creating directory %s ..." % modir
				os.makedirs (modir)

			popath = os.path.join (podir, pofile)
			mopath = os.path.join (modir, 'nautilus-renamer.mo')

			print "Creating %s ..." % mopath 
			subprocess.call(['msgfmt', '-o', mopath, popath])

if __name__ == "__main__":
	
	if len (sys.argv) != 3:
		print "Usage: %s @podir @localedir" % sys.argv[0]
		sys.exit (1)

	podir = sys.argv[1]
	localedir = sys.argv[2]

	gen_mo_files (podir, localedir) 
