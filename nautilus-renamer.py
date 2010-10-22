#! /usr/bin/python
#  -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2010 Thura Hlaing <trhura@gmail.com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

"""

import os
import sys
import re
import time
import mmap
import string
import random

import pygtk
pygtk.require ('2.0')
import locale, gettext

import gtk
import glib
import pango
import gobject
import pynotify

# Configuration
DEFAULT_WIDTH   = 450                   # Dialog's default width at startup
DEFAULT_HEIGHT  = 320                   # Dialog's default height at startup
PREVIEW_HEIGHT  = 150                   # Height of preview area
UNDO_LOG_FILE   = '.rlog'               # Name used for Log file
DATA_DIR        = '.rdata/'             # 
LOG_SEP         =  ' is converted to '  # Log file separator
REC_PATS        = 5                     # Remember up to 5 recent patterns
REC_FILE        = 'recent_patterns'     # filename for recent patterns
NOTIFICATION_TIMEOUT =  -1              # notification timeout, pynotify.EXPIRES_DEFAULT

# Fake Enums
PATTERNIZE, SUBSTITUTE, CASING, UNDO = range (4)
ALL_CAP, ALL_LOW, FIRST_CAP, EACH_CAP, CAP_AFTER = range (5)

# dir to store application state, recent patterns ... 
CONFIG_DIR = os.path.join (glib.get_user_data_dir (), "nautilus-renamer")

APP = 'nautilus-renamer'

not_installed_dir = os.path.dirname(os.path.realpath(__file__)) 
if os.path.exists(not_installed_dir + '/po'):
    # po dir, when it is not installed yet
    PO_DIR = not_installed_dir + '/po'
    
elif os.path.exists(os.path.expanduser('~/.gnome2/nautilus-scripts/.rdata/po')):
    # po dir, when it is installed as a user script 
    PO_DIR = os.path.expanduser('~/.gnome2/nautilus-scripts/.rdata/po')

else:
    PO_DIR = None

class Application():

    def __init__(self):

        self.case_opt = ALL_CAP
        self.recur    = False
        self.ext      = False
        self.pattern  = None
        self.logFile  = None
        self.num = 0
        self.num_pat = re.compile(r'\/num\d+(\+\d+)?\/')
        self.ran_pat = re.compile (r'\/rand\d+-\d+\/')
        self.name_slice = re.compile (r'\/name:-?\d+(:-?\d+)?\/')
        self.filename_slice = re.compile (r'\/filename:-?\d+(:-?\d+)?\/') 
        self.filename_delete = re.compile (r'\/filename-.*/')
        self.a_pattern = re.compile (r'\/.*\/') #used to check invalid patterns
        self.ran_seq = []
        self.filesRenamed = 0
        self.pmodel = gtk.ListStore (gobject.TYPE_STRING, gobject.TYPE_STRING)

        ubox    = gtk.Table (2, 2, True)     # Upper Box
        lframe  = gtk.Frame (_("Options"))
        lalign  = gtk.Alignment ( 0.1, 0.2, 1.0, 0.0)
        self.lbox   = gtk.VBox  (False, 5)  # Lower Box

        # Upper Box Radio Buttons
        pat_rb  = gtk.RadioButton (None,  _("_Patternize"), True)
        sub_rb  = gtk.RadioButton (pat_rb, _("_Substitute"), True)
        cas_rb  = gtk.RadioButton (pat_rb, _("C_ase"), True)
        und_rb  = gtk.RadioButton (pat_rb, _("_Undo"), True)

        self.prepare_pat_options (pat_rb)

        lalign.add (self.lbox)
        lalign.set_padding (5, 5, 5, 5)
        lframe.add (lalign)
        lframe.set_size_request (-1, 120)

        #Popup Menu for available patterns
        self.pat_popup  = gtk.Menu ()
        pat_fname   = gtk.MenuItem ('/filename/')
        pat_dir     = gtk.MenuItem ('/dir/')
        pat_name    = gtk.MenuItem ('/name/')
        pat_ext     = gtk.MenuItem ('/ext/')
        pat_day     = gtk.MenuItem ('/day/')
        pat_date    = gtk.MenuItem ('/date/')
        pat_month   = gtk.MenuItem ('/month/')
        pat_year    = gtk.MenuItem ('/year/')
        pat_dname   = gtk.MenuItem ('/dayname/')
        pat_dsimp   = gtk.MenuItem ('/daysimp/')
        pat_mname   = gtk.MenuItem ('/monthname/')
        pat_msimp   = gtk.MenuItem ('/monthsimp/')
        pat_num1    = gtk.MenuItem ('/num2/')
        pat_num2    = gtk.MenuItem ('/num3+0/')
        pat_rand    = gtk.MenuItem ('/rand10-99/')
        
        pat_fname.set_tooltip_text  (_("Original filename"))
        pat_dir.set_tooltip_text    (_("Parent directory"))
        pat_name.set_tooltip_text   (_("Filename without extenstion"))
        pat_ext.set_tooltip_text    (_("File extension"))
        pat_day.set_tooltip_text    (_("Day of month"))
        pat_date.set_tooltip_text   (_("Full date, e.g., 24Sep2008"))
        pat_month.set_tooltip_text  (_("Numerical month of year"))
        pat_year.set_tooltip_text   (_("Year, e.g., 1990"))
        pat_mname.set_tooltip_text  (_("Full month name, e.g., August"))
        pat_msimp.set_tooltip_text  (_("Simple month name, e.g., Aug"))
        pat_dname.set_tooltip_text  (_("Full day name, e.g., Monday"))
        pat_dsimp.set_tooltip_text  (_("Simple dayname, e.g., Mon"))
        pat_num1.set_tooltip_text   (_("{num5} => 00001, 00002, 00003 , ..."))
        pat_num2.set_tooltip_text   (_("{num5+5} => 00005, 00006, 00007 , ..."))
        pat_rand.set_tooltip_text (_("A random number from 10 to 99"))
        
        self.pat_popup.attach (pat_fname,   0, 1, 0, 1)
        self.pat_popup.attach (pat_dir,     1, 2, 0, 1)
        self.pat_popup.attach (pat_name,    0, 1, 1, 2)
        self.pat_popup.attach (pat_ext,     1, 2, 1, 2)
        self.pat_popup.attach (pat_day,     0, 1, 2, 3)
        self.pat_popup.attach (pat_date,    1, 2, 2, 3)
        self.pat_popup.attach (pat_month,   0, 1, 3, 4)
        self.pat_popup.attach (pat_year,    1, 2, 3, 4)
        self.pat_popup.attach (pat_dname,   0, 1, 4, 5)
        self.pat_popup.attach (pat_dsimp,   1, 2, 4, 5)
        self.pat_popup.attach (pat_mname,   0, 1, 5, 6)
        self.pat_popup.attach (pat_msimp,   1, 2, 5, 6)
        self.pat_popup.attach (pat_num1,    0, 1, 6, 7)
        self.pat_popup.attach (pat_num2,    1, 2, 6, 7)
        self.pat_popup.attach (pat_rand,     0, 1, 7, 8)

        self.pat_popup.show_all ()

        ubox.attach (pat_rb, 0, 1, 0, 1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 0)
        ubox.attach (sub_rb, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 0)
        ubox.attach (cas_rb, 0, 1, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 0)
        ubox.attach (und_rb, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 0)

        self.dialog = gtk.Dialog ("Renamer", None, gtk.DIALOG_NO_SEPARATOR,
                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))

        self.ext_cb   = gtk.CheckButton (_("_Extension"), True)
        self.recur_cb = gtk.CheckButton (_("_Recursive"), True)
        self.ext_cb.set_tooltip_text (_("Also operate on extensions"))
        self.recur_cb.set_tooltip_text (_("Also operate on subfolders and files"))

        refresh       = gtk.Button (_("Refresh Previe_w"))

        brbox   = gtk.HBox (False, 5);
        brbox.pack_end (self.recur_cb, False, False, 0)
        brbox.pack_end (self.ext_cb, False, False, 0)

        ralign = gtk.Alignment (1.0, 0.5, 0.0, 0.0)
        ralign.add (brbox)
        
        bbox    = gtk.HBox (False, 5)
        bbox.pack_start (refresh, False, False, 0)
        bbox.pack_end (ralign, False, False, 0)
        
        # Preview
        pbox    = gtk.HBox (False, 5)
        view    = gtk.TreeView (self.pmodel)
        view.set_rules_hint (True)
        view.set_size_request ( -1, PREVIEW_HEIGHT)
        
        cell    = gtk.CellRendererText ()
        cell.set_property ('scale', 0.8)
        cell.set_property ('width', DEFAULT_WIDTH/2)
        cell.set_property ('ellipsize', pango.ELLIPSIZE_MIDDLE)
        column  = gtk.TreeViewColumn (_("Original Name"), cell, text=0)
        column.set_property ('sizing', gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_property ('resizable', True)
        view.append_column (column)
        
        
        cell    = gtk.CellRendererText ()
        cell.set_property ('scale', 0.8)
        cell.set_property ('width', DEFAULT_WIDTH/2 )
        cell.set_property ('ellipsize', pango.ELLIPSIZE_MIDDLE)
        column  = gtk.TreeViewColumn (_("New Name"), cell, text=1)
        column.set_property ('sizing', gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column.set_property ('resizable', True)
        view.append_column (column) 
        
        scrollwin   = gtk.ScrolledWindow ()
        scrollwin.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwin.add (view)
        
        expander = gtk.Expander (_("Pre_view"))
        expander.set_use_underline (True)        
        expander.add (scrollwin)
        
        mbox    = gtk.VBox ( False, 10)
        mbox.pack_start (ubox, False, False, 0)
        mbox.pack_start (lframe, True, True, 0)
        mbox.pack_start (expander, True, True, 0)
        mbox.pack_start (gtk.HSeparator(), False, False, 0)
        mbox.pack_end   (bbox, False, False, 0)

        malign = gtk.Alignment (0.0, 0.0, 1.0, 0.0)
        malign.set_padding (10, 10, 10, 10)

        malign.add (mbox)
        self.dialog.vbox.add (malign)

        self.dialog.set_default_size (DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.dialog.set_icon_name (gtk.STOCK_EDIT)
        self.dialog.show_all ()
                
        pat_rb.connect ('toggled', self.prepare_pat_options)
        sub_rb.connect ('toggled', self.prepare_sub_options)
        cas_rb.connect ('toggled', self.prepare_cas_options)
        und_rb.connect ('toggled', self.prepare_und_options)

        pat_dir.connect   ('activate', self.on_popup_activate)
        pat_ext.connect   ('activate', self.on_popup_activate)
        pat_day.connect   ('activate', self.on_popup_activate)
        pat_date.connect  ('activate', self.on_popup_activate)
        pat_name.connect  ('activate', self.on_popup_activate)
        pat_year.connect  ('activate', self.on_popup_activate)
        pat_fname.connect ('activate', self.on_popup_activate)
        pat_month.connect ('activate', self.on_popup_activate)
        pat_dname.connect ('activate', self.on_popup_activate)
        pat_dsimp.connect ('activate', self.on_popup_activate)
        pat_mname.connect ('activate', self.on_popup_activate)
        pat_msimp.connect ('activate', self.on_popup_activate)
        pat_num1.connect ('activate', self.on_popup_activate)
        pat_num2.connect ('activate', self.on_popup_activate)
        pat_rand.connect ('activate', self.on_popup_activate)
        
        expander.connect ('notify::expanded', self.expander_cb)        
        refresh.connect ('clicked', self.prepare_preview)

    def prepare_pat_options (self, button, data=None):

        if not button.get_active():
            return

        self.lbox.foreach (self.remove)
        self._read_recent_pats ()

        hbox    = gtk.HBox (False, 5)

        combo   = gtk.ComboBoxEntry (self.pats, 0)
        self.pat_entry  = combo.child
        button  = gtk.Button (" _?", None, True)
        
        label   = gtk.Label ()
        label.set_line_wrap (True)
        label.set_alignment ( 0.1, -1)
        label.set_markup (_("<span size='small'>Rename files, based on a pattern. Click on <b>?</b> for available pattens.</span>"))        

        self.pat_entry.label = _("Enter the pattern here ... ")
        self.prepare_entry (self.pat_entry)

        hbox.pack_start (combo, True, True, 0)
        hbox.pack_start (button, False, False, 0)

        button.connect ('button-press-event', lambda button, event:
                            self.pat_popup.popup (None, None, None, event.button, event.time))

        combo.connect ('changed', self.combo_box_changed )
                              
        self.pat_entry.connect ('activate', self.pat_entry_activate)

        self.lbox.pack_start (label, True, True, 0)
        self.lbox.pack_start (hbox, True, True, 0)
        self.lbox.show_all ()

        self.action = PATTERNIZE

    def prepare_sub_options (self, button, data=None):

        if not button.get_active():
            return

        self.lbox.foreach (self.remove)

        self.sub_replee = gtk.Entry ()
        self.sub_replee.label =  _("Words to be replaced separated by \"/\", e.g., 1/2 ...")
        self.prepare_entry (self.sub_replee)

        self.sub_repler = gtk.Entry ()
        self.sub_repler.label = _("Corresponding words to replace with, e.g., one/two ...")
        self.prepare_entry (self.sub_repler)

        self.sub_replee.set_tooltip_text (_("Enter the words (regular expressions) to be replaced, separated by '/'"))
        self.sub_repler.set_tooltip_text (_("Enter the corresponding words to replace with"))

        self.lbox.pack_start (self.sub_replee, True, True, 0)
        self.lbox.pack_start (self.sub_repler, True, True, 0)

        self.lbox.show_all ()

        self.action = SUBSTITUTE         

    def prepare_cas_options (self, button, data=None):

        if not button.get_active ():
            return

        self.lbox.foreach (self.remove)

        store   = gtk.ListStore ('gboolean', str, int)

        store.append([True,  _("ALL IN CAPITALS"), ALL_CAP])
        store.append([False, _("all in lower case"), ALL_LOW])
        store.append([False, _("First letter upper case"), FIRST_CAP])
        store.append([False, _("Title Case"), EACH_CAP])
        store.append([False, _("Capital Case After ..."), CAP_AFTER])

        self.view   = gtk.TreeView (store)
        self.view.set_rules_hint (True)

        cell    = gtk.CellRendererToggle ()
        cell.set_radio (True)
        cell.set_property ('xalign', 0.1)

        column  = gtk.TreeViewColumn ()
        column.pack_start (cell, False)
        column.set_sizing (gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width (40)
        column.add_attribute (cell, 'active', 0)

        self.view.append_column (column)

        cell    = gtk.CellRendererText ()
        cell.set_property ('scale', 0.8)

        column  = gtk.TreeViewColumn(_("Choose One"))
        column.pack_start (cell, True)
        column.add_attribute (cell, 'text', 1)

        self.view.append_column (column)

        self.scroll_win  = gtk.ScrolledWindow()
        self.scroll_win.set_policy (gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll_win.add(self.view)

        self.view.connect ('cursor-changed', self.cursor_changed)
        self.lbox.pack_start (self.scroll_win, True, True, 0)
        self.lbox.show_all ()

        self.action  = CASING        

    def prepare_und_options (self, button, data=None):

        if not button.get_active ():
            return

        self.lbox.foreach (self.remove)

        und_label = gtk.Label ()
        und_label.set_line_wrap (True)
        und_label.set_alignment (0.1, -1)        
        
        if self.log_file_p():
            und_label.set_markup (_("<b>Undo the last operation inside this folder.</b>\n\n <span color='grey' size='small'>Note: You cannot undo an undo. ;)</span>"))
        else: 
            und_label.set_markup (_("<span color='red' weight='bold'>No log file is found in this folder.</span>\n\n<span color='grey' size='small'>Note: When it renames files, Renamer writes a log file, in the folder it was launched, which is used for Undo.</span>"))

        self.lbox.pack_start (und_label, True, True, 0)
        self.lbox.show_all ()

        self.action = UNDO
    
    def prepare_cap_after_options (self):
        
        self.scroll_win.remove (self.view)
        self.lbox.remove (self.scroll_win)

        cap_label = gtk.Label (_("Capitalize after: "))

        self.cap_entry = gtk.Entry ()
        self.cap_entry.set_text (' /-/_/[/(')
        self.cap_first = gtk.CheckButton (_("_First Letter"), True)        
        self.cap_first.set_active (False)
        
        cbox    = gtk.Table (3, 2, False)
        cbox.attach (cap_label, 0, 1, 0, 1, 0)
        cbox.attach (self.cap_entry, 1, 2, 0, 1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 2, 5)
        cbox.attach (self.cap_first, 1, 2, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)

        self.lbox.pack_start (cbox, True, True, 0)

        self.cap_entry.set_tooltip_text (_("Enter the list of sequences, to capitalize the letter after each of it, separated by '/'"))
        self.cap_first.set_tooltip_text (_("Capitalize the first letter"))
        self.lbox.show_all ()
        
    def prepare_entry (self, entry):
        """ Helper function for preparing entries in our dialog """
        entry.set_text (entry.label)
        entry.clr_on_focus = True   # Clear current text when the entry is focused
        self.modify_entry_style_grey_italic (entry)
                        
        entry.connect ('focus-in-event',  self.entry_focus_in)
        entry.connect ('focus-out-event', self.entry_focus_out)

    def modify_entry_style_grey_italic (self, entry):
        """ Make the text in entry grey and italic"""        
        desc	= entry.get_pango_context().get_font_description()
        desc.set_style (pango.STYLE_ITALIC)
        entry.modify_font (desc)
        entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('grey'))        
    
    def restore_entry_style (self, entry):
        """ Make the text in entry back to black and normal style"""        
        desc	= entry.get_pango_context().get_font_description()
        desc.set_style (pango.STYLE_NORMAL)
        entry.modify_font (desc)
        entry.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color('black'))        
        
    def entry_focus_in (self, widget, event, data=None):
        """ When the entriy is focused for the first time, clear the label text, and reset text style."""
        if widget.clr_on_focus:
            widget.set_text ("")
            widget.clr_on_focus = False            
            self.restore_entry_style (widget)
        
    def entry_focus_out (self, widget, event, data=None):
        """ When the entry focus is out without any changes, restore label text and color."""
        if widget.get_text () == "":
            widget.set_text (widget.label)
            widget.clr_on_focus = True   # Clear current text when the entry is focused            
            self.modify_entry_style_grey_italic (widget)

    def combo_box_changed (self, combo, data=None):
        "When patten combo box entry is changed, restore text style"
        self.pat_entry.clr_on_focus = False
        self.restore_entry_style (combo.child)

    def pat_entry_activate (self, entry, data=None):
        "When Return is pressed on pattern entry"
        self.rename (files)
        self.dialog.destroy ()
                        
    def expander_cb (self, widget, data):
        """ When expander state is changed """
        if widget.get_expanded ():
            # When preview is expanded, resize the dialog a litter bigger.
            self.dialog.resize (DEFAULT_WIDTH + 150 , DEFAULT_HEIGHT + PREVIEW_HEIGHT)
            self.prepare_preview (widget)
        else:
            # When preview is hidden, restore normal size
            self.dialog.set_size_request (DEFAULT_WIDTH, DEFAULT_HEIGHT)
            self.dialog.resize (DEFAULT_WIDTH, DEFAULT_HEIGHT)

    def on_popup_activate (self, item, data=None):
        """ When a menutitem on patterns popup menu is clicked, append the label to pattern entry. """
        self.entry_focus_in (self.pat_entry, None, None)
        self.pat_entry.set_text (self.pat_entry.get_text() + item.get_property('label'))

    def cursor_changed (self, treeview, data=None):
        """ When selected row in CASE tree view is changed, update the tree model. """
        model, iter = treeview.get_selection().get_selected ()
        model.foreach (lambda model, path, iter: model.set (iter, 0, False))
        model.set (iter, 0, True)
        self.case_opt = model.get_value (iter, 2)
        
        if self.case_opt == CAP_AFTER:
            self.prepare_cap_after_options ()
    
    def remove (self, child):
        """ callback to remove a child from lbox """
        self.lbox.remove (child)

    def build_preview_model (self, path, vpath=''):
        " Base function for building list store for preview "        
        parent, name = os.path.split (path)
        newName = self._get_new_name(name)
        
        if not newName:
            # If there is any error getting new name, return False
            print "build preview error ...."
            return False
        
        newPath = os.path.join (os.path.split(vpath)[0],newName)
        
        if not path == newPath:
            self.pmodel.append ([path, newPath])
        
        if  os.path.isdir(path) and self.recur:
            for subdir in os.listdir (path):
                if not self.build_preview_model (os.path.join(path, subdir), os.path.join(newPath, subdir)):
                    # If there is any error
                    return False
        
        return True
        
    def prepare_preview (self, widget):
        " Wrapper around build_preview_model. Prepare and validate settings."
        self.pmodel.clear ()
        
        if self.action == UNDO and self.log_file_p():
            logFile = open (UNDO_LOG_FILE, 'rb')
            
            for i in xrange(5): logFile.readline () #Skip 5 lines of header
            
            for line in logFile:
                oldpath, newpath = line.split('\n')[0].split(LOG_SEP)
                oldp = os.path.join(os.path.dirname(oldpath), os.path.basename(newpath))
                newp = os.path.join(os.path.dirname(newpath), os.path.basename(oldpath))
                self.pmodel.append ([newpath, oldpath])
                
            logFile.close ()
            return
            
        if not self.prepare_data_from_dialog():
        # if there is any error, return
            return
                
        for file in files:
            if not self.build_preview_model (file):
                # if there is any error
                return
        
    def prepare_data_from_dialog (self):
        """ Initialize data require for rename and preview from dailog
            Report and return False.on errors"""

        self.recur = self.recur_cb.get_active ()
        self.ext   = self.ext_cb.get_active ()

        if self.action != UNDO and not files:
            # If it is not undo, and no selected files
            return False
        
        if self.action == PATTERNIZE:
            # prepare patternize related options, and check for possible errors
            self.pattern = self.pat_entry.get_text ()
            self.num = 0

            if self.pattern == '' or self.pattern == self.pat_entry.label:
                show_error (_("Empty Pattern"), _("Please, enter a valid pattern."))
                return False
            
            if self.num_pat.search(self.pattern):
                #if the pattern contains /num*/ or /num*+*/, disable recursion
                self.recur = False
            
            if self.ran_pat.search(self.pattern):
                # If a random pattern is found, prepare sequence of random numbers
                tmp = self.ran_pat.search(self.pattern).group()
                range = tmp[5:-1] # Extract 10-99 from /rand10-99/
                start, end = range.split ('-') # Split 10-99 to 10 and 99                
                self.ran_seq = [x for x in xrange (int(start), int(end))]

        elif self.action == SUBSTITUTE:
            # prepare substitute related options, and check for possible errors
            replee = self.sub_replee.get_text ()
            repler = self.sub_repler.get_text ()

            if replee == self.sub_replee.label or replee == '':
                show_error (_("Empty Word"), _("Please enter a valid word to be replaced."))
                return False

            if repler == self.sub_repler.label:
               repler = ''

            self.replees = replee.split ('/')
            self.replers = repler.split ('/')
                
        return True
    
    def rename (self, files):
        """ Wrapper around _rename (). Prepare and validate settings, and write logs."""
        if self.action == UNDO:
            self.undo ()
            return True

        if not files:
            # No files to rename
            show_error (_("No file selected"), _("Please, select some files first."))
            self.exit ()
            
        if not self.prepare_data_from_dialog():
            # if there is any error, return
            return False

        self.start_log ()

        for file in files:
            app._rename(file)

        self.close_log ()
        
        if self.action == PATTERNIZE:
            self._write_recent_pats ()

        self.notify(_("Rename successful"),\
                    _("renamed %d files successfully.") % self.filesRenamed,\
                     gtk.STOCK_APPLY,NOTIFICATION_TIMEOUT)

        return True

    def _rename (self, path, oldPath=''):
        """ Base function to rename files
            If self.recur is set, also renames file recursively"""
        parent, oldName = os.path.split (path)
        newName = self._get_new_name (oldName)
        
        if not newName:
            self.exit ()
            
        newPath = os.path.join (parent, newName)
        oldPath = os.path.join (oldPath, oldName)

        if not path == newPath:
            # No need to rename if path (old) = newPath
            if os.path.exists (newPath):
                show_error (_("File Already Exists"), newPath + _(" already exists. Use Undo to revert."))
                self.exit()

            os.rename (path, newPath)
            self.logFile.write ('%s%s%s\n' %(oldPath, LOG_SEP,newPath))
            self.filesRenamed = self.filesRenamed + 1

        if  os.path.isdir(newPath) and self.recur:
            for file in os.listdir (newPath):
                self._rename (os.path.join (newPath, file), oldPath)
                
    def _write_recent_pats (self):
        """ Store recent patterns """
        if not os.path.exists(CONFIG_DIR):
            os.makedirs (CONFIG_DIR)

        with open (os.path.join (CONFIG_DIR, REC_FILE), 'w') as file:
            i = 1
            cpat = self.pat_entry.get_text()
            file.write (cpat + '\n' ) 
            for pat in self.pats:
                if i < REC_PATS and not pat[0] == cpat:
                    file.write (pat[0] + '\n')
                    i = i + 1

    def _read_recent_pats (self):
        """ Read recent patterns """
        self.pats = gtk.ListStore (gobject.TYPE_STRING)

        try:
            with open (os.path.join (CONFIG_DIR, REC_FILE), 'r') as file:
                for pat in file:
                    self.pats.append ([pat[:-1]])
        except:
            pass
            
    def _get_new_name (self, oldName):
        """ return a new name, based on the old name, and settings from our dialog. """

        if self.action == SUBSTITUTE:
            if self.ext:
                newName = oldName
            else:
                name, ext = os.path.splitext (oldName)
                newName = name

            for i in xrange (0, len(self.replees)):
                # print self.replees[i], self.replers[i] 
                pattern = re.compile (self.replees[i])
                if i < len (self.replers):
                    newName = pattern.sub (self.replers[i], newName)
                else:
                    # if there is no corresponding word to replace, use the last one
                    newName = pattern.sub (self.replers[-1], newName)

            if self.ext:
                return newName
            else:
                return newName + ext               

        if self.action == CASING:
            if self.ext:
                name = oldName
            else:
                name, ext = os.path.splitext (oldName)

            if self.case_opt == ALL_CAP:
                name = name.upper ()

            elif self.case_opt == ALL_LOW:
                name = name.lower()
                
            elif self.case_opt == FIRST_CAP:
                name = name.capitalize()

            elif self.case_opt == EACH_CAP:
                name = name.title ()
                
            elif self.case_opt == CAP_AFTER:
                
                if self.cap_first.get_active():
                    name = name.capitalize()
            
                seps  = self.cap_entry.get_text ()

                for sep in seps.split ('/'):
                    lst = [ l for l in name.split(sep)]
                    for i in xrange(1, len(lst)):
                        if lst[i] is not '':
                            lst[i] = lst[i][0].upper() + lst[i][1:]
                    name = sep.join (lst)
        
            if self.ext:
                return name
            else:
                return name + ext


        if self.action == PATTERNIZE:
            
            if not self.pattern:
                return oldName

            newName = self.pattern
            
            #for number substiution
            for match in self.num_pat.finditer (newName):
                tmp = match.group()
                #print tmp
                #if /num?/
                if len(tmp)== 6:
                    substitute = str(self.num).zfill(int(tmp[4]))
                    newName    = self.num_pat.sub(substitute, newName, 1)
                    self.num   = self.num + 1
                #if /num?+?/
                elif len(tmp) > 7:
                    substitute = str(self.num+int(tmp[6:(len(tmp)-1)])).zfill(int(tmp[4]))
                    newName    = self.num_pat.sub(substitute, newName, 1)
                    self.num   = self.num + 1
            
            # for random number insertion
            for match in self.ran_pat.finditer (newName):
                if not self.ran_seq:
                    # if random number sequence is None
                    print "Not Enought Random Number Range"
                    show_error (_("Not Enough Random Number Range"), _("Please, use a larger range"))
                    self.exit ()
                    #return False
                    
                randint = random.choice (self.ran_seq)
                self.ran_seq.remove (randint)
                newName = self.ran_pat.sub (str(randint), newName, 1)
                
            dir, file = os.path.split (os.path.abspath(oldName))
            name, ext = os.path.splitext (file)
            dirname = os.path.basename(dir)

            #replace filename related Tags
            newName = newName.replace('/filename/',oldName)
            newName = newName.replace('/dir/', dirname)
            newName = newName.replace('/name/', name)
            newName = newName.replace('/ext/', ext)

            #for /name:offset(:length)/
            for match in self.name_slice.finditer (newName):
                tmp = match.group ()
                tmp = tmp[:-1].split (':')

                if len(tmp) ==  2:
                    tmp, offset = tmp
                    offset = int(offset)
                    substitute = name[offset:] 
                else:
                    tmp, offset, length = tmp
                    offset = int(offset)
                    length = int(length)
                    if length < 0:
                        if offset  == 0:
                            substitute = name[offset+length:]
                        else:
                            substitute = name[offset+length:offset]
                    else:
                        if (len(name[offset:]) > length):
                            substitute = name[offset:offset+length]
                        else:
                            substitute = name[offset:]
                            
                newName    = self.name_slice.sub (substitute, newName, 1)
                
            #for /filename:offset(:length)/
            for match in self.filename_slice.finditer (newName):
                tmp = match.group ()
                tmp = tmp[:-1].split (':')

                if len(tmp) ==  2:
                    tmp, offset = tmp
                    offset = int(offset)
                    substitute = oldName[offset:] 
                else:
                    tmp, offset, length = tmp
                    offset = int(offset)
                    length = int(length)
                    if length < 0:
                        if offset  == 0:
                            substitute = oldName[offset+length:]
                        else:
                            substitute = oldName[offset+length:offset]
                    else:
                        if (len(name[offset:]) > length):
                            substitute = name[offset:offset+length]
                        else:
                            substitute = name[offset:]
                            
                newName    = self.filename_slice.sub(substitute, newName, 1)


            #Some Time/Date Replacements
            newName = newName.replace('/date/', time.strftime('%d%b%Y', time.localtime()))
            newName = newName.replace('/year/', time.strftime('%Y', time.localtime()))
            newName = newName.replace('/month/', time.strftime('%m', time.localtime()))
            newName = newName.replace('/monthname/', time.strftime('%B', time.localtime()))
            newName = newName.replace('/monthsimp/', time.strftime('%b', time.localtime()))
            newName = newName.replace('/day/', time.strftime('%d', time.localtime()))
            newName = newName.replace('/dayname/', time.strftime('%A', time.localtime()))
            newName = newName.replace('/daysimp/', time.strftime('%a', time.localtime()))
            
            return newName

    def undo (self):
        """ Restore previously renamed files back according to the log file. """
        if not self.log_file_p ():
            show_error (_("Undo Failed"), _("Log file not found"))
            self.exit()
        
        logFile = open (UNDO_LOG_FILE, 'rb')    
        for i in range(5): logFile.readline () #Skip 5 lines of header

        for line in logFile:
            oldpath, newpath = line.split('\n')[0].split(LOG_SEP)
            oldpath = os.path.abspath (oldpath)
            #print os.path.join(os.path.dirname(oldpath),os.path.basename(newpath)),oldpath
            os.rename(os.path.join(os.path.dirname(oldpath),os.path.basename(newpath)),oldpath)
            self.filesRenamed = self.filesRenamed + 1

        logFile.close ()

        os.remove (UNDO_LOG_FILE)
        self.notify(_("Undo successful"),\
                    _("%d files restored.") % self.filesRenamed, \
                    gtk.STOCK_APPLY,5000)
        
    def log_file_p (self):
        """ Check for log file in current folder, 
            return True if found, else False """
        return os.path.exists (UNDO_LOG_FILE) and True or False
    
    def start_log (self):
        """ Open log and write header. """
        self.logFile = open (UNDO_LOG_FILE, 'wb', 1)

        self.logFile.write (' Renamer Log '.center (80, '#'))
        self.logFile.write ('\n')

        self.logFile.write ('# File :  files\n')
        self.logFile.write ('# Time : ')
        self.logFile.write (time.strftime('%a, %d %b %Y %H:%M:%S\n'))
        self.logFile.write ('#'.center (80, '#'))
        self.logFile.write ('\n\n')

    def close_log (self):
        """ Close log file, and insert total files renamed."""
        if not self.logFile:
            return
        
        self.logFile.close ()

        with open (UNDO_LOG_FILE, 'r+b') as file:
            m = mmap.mmap(file.fileno(), os.path.getsize(UNDO_LOG_FILE))
            str = '%d' % self.filesRenamed
            l = len(str) #len
            s = m.size() #size
            o = 90       #offset
            m.resize (s + l)
            m[(o+l) : ] = m [o : s]
            m[o : (o+l)] = str
            m.close ()
    
    def exit (self):
        """ Exit Application if there is an error."""
        self.close_log ()
        
        if self.action == PATTERNIZE:
            self._write_recent_pats ()
        
        sys.exit (1)
        
    def notify(self, title,text,iconpath,time):
        """ Wrapper to display notifications with timeout time. """
        if not pynotify.init("Renamer"):
            self.exit ()

        n = pynotify.Notification(title,text,iconpath)
        n.set_timeout(time)

        if not n.show():
            print "Failed to send notification"
            self.exit ()


def show_error (title, message):
    "help function to show an error dialog"
    dialog = gtk.MessageDialog (type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE)
    dialog.set_markup ("<b>%s</b>\n\n%s"%(title, message))
    dialog.run ()
    dialog.destroy ()

def init_gettext ():

	gettext.bindtextdomain(APP, PO_DIR)
	gettext.textdomain(APP) 
	
	lang = gettext.translation (APP, PO_DIR, fallback=True)
	_ = lang.gettext
	gettext.install (APP, PO_DIR)
	
if __name__ == '__main__':
	
	init_gettext ()
	
	files = [file for file in sys.argv[1:]]
            
        app = Application ()
            
        while (app.dialog.run () == gtk.RESPONSE_OK):
            if app.rename (files):
                break
