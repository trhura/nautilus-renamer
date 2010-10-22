#!/usr/bin/env python

import os;
import re;
import subprocess;

outfile = 'po/nautilus-renamer.pot'
pattern = re.compile('^([a-zA-Z_]+)\.po$')

files = ['nautilus-renamer.py']
common_args = ['-o', outfile, '--copyright-holder=Thura Hlaing <trhura@gmail.com>', '--package-name=nautilus-renamer',
	'--package-version=2.3', '--msgid-bugs-address=trhura@gmail.com']

print 'Updating translation template'
subprocess.call(['xgettext', '--from-code=utf-8', '--language=Python', '--keyword=_', '--add-comments=///'] + common_args + files)

for langfile in sorted(os.listdir('po')):
	matches = pattern.match(langfile)
	
	if matches:
		lang = matches.group(1)
		print 'Updating translation file for language "%s"' % lang
		langfile = 'po/%s' % langfile
		subprocess.call(['msgmerge', '-U', langfile, outfile])
