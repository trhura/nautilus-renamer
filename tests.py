#! /usr/bin/python
#  -*- coding: utf-8 -*-

from gi.repository import Notify
import imp


renamer = imp.load_source ('renamer', 'nautilus-renamer.py')

files = ['a.jpg','b.jpg','c.jpg', 'd.jpg']
Notify.init ("test")
app = renamer.RenameApplication ()

print "=============== Testing Notifications ==============="
#app.notify ("Test Notify", "Testing Notifications", Gtk.STOCK_OK)

print "=============== Testing Patterns  ==============="
app.pattern = '/name//num,5//num,3+5//ext/'
app.substitute_p = False
lst = []
for fil in files:
    p = app._get_new_name (fil)
    print "%s, %s = %s" %(fil, app.pattern, p)
    lst += [p]


