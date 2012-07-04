#dr3mro@gmail.com
#nautilus Mass Rename
#v 0.1

from gi.repository import Nautilus, GObject
import os
import subprocess
import urllib
import sys
import gettext

APP = 'nautilus-renamer'
gettext.bindtextdomain(APP)
gettext.textdomain(APP)
lang = gettext.translation (APP, None, fallback=True)
_ = lang.gettext

class MassRename(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        pass

    def url2path(self,url):
        fileuri= url.get_activation_uri()
        arg_uri=fileuri[7:]
        path=urllib.url2pathname(arg_uri)
        return path

    def rename_run(self,menu,files):
        rename_path=[os.path.join (sys.prefix, 'share', 'nautilus-renamer', 'nautilus-renamer.py')]
        print rename_path
        for file in files:
            path=self.url2path(file)
            rename_path.append(os.path.basename(path))
        dirname=os.path.dirname(path)
        os.chdir(dirname)
        subprocess.Popen(rename_path)
        return

    def get_file_items(self, window, files):
        if len(files) < 2:
            return

        RenameMenuItem = Nautilus.MenuItem(
            name="RenameMenuItem::Rename",
            label=_("Mass Rename"),
            tip=_("Mass Rename")
        )
        RenameMenuItem.connect('activate', self.rename_run, files)

        return [RenameMenuItem]
