import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import os

import xdg.BaseDirectory as base

from magnifier import Magnifier
from colorpicker import ColorPicker

from palette import Palette
from color import Color

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

class Elicit:
  appname = 'elicit'

  def quit(self, widget, data=None):
    self.save_config()
    gtk.main_quit()

  def main(self):
    gtk.main()

  def show(self):
    self.win.show_all()

  def hide(self):
    self.win.hide()

  def grab(self, x, y, w ,h):
    self.mag.grab(x,y,w,h)

  def mag_grid_toggled(self, mag):
    self.grid_check.set_property('active', mag.show_grid)

  def mag_zoom_changed(self, mag):
    self.zoom_spin.set_property('value', mag.zoom)

  def grid_check_toggled(self, check):
    self.mag.set_show_grid(check.get_property('active'))

  def zoom_spin_value_changed(self, spin):
    self.mag.set_zoom(spin.get_property('value'))

  def load_config(self):
    self.conf = {
        'palette_columns': 1,
        'zoom_level': 6,
        'grab_rate': 60,
        'show_grid': 1,
        'palette': None,
        'color': '#000000'
      }

    for path in base.load_config_paths(self.appname):
      file = os.path.join(path, 'elicit.cfg')
      if os.path.exists(file):
        with open(file) as f:
          for line in f:
            if line[0] == '#' or line[0] == '\n':
              continue
            key,val = line.split(':')
            self.conf[key.strip()] = val.strip()
        return

  def save_config(self):
    self.conf['zoom_level'] = self.mag.zoom
    self.conf['show_grid'] = self.mag.show_grid
    self.conf['grab_rate'] = self.mag.grab_rate
    self.conf['palette'] = self.palette.filename
    self.conf['color'] = self.color.hex

    path = base.save_config_path(self.appname)
    file = os.path.join(path, 'elicit.cfg')

    with open(file, 'w') as f:
      for key in self.conf:
        f.write("%s: %s\n" % (key, self.conf[key]))

  def build_gui(self):
    self.win = gtk.Window()
    self.win.set_title("Elicit")
    self.win.connect('destroy', self.quit, None)

    vbox = gtk.VBox(False, 5)
    self.win.add(vbox)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    vbox.add(frame)

    self.mag = Magnifier()
    frame.add(self.mag)
    self.mag.connect('zoom-changed', self.mag_zoom_changed)
    self.mag.connect('grid-toggled', self.mag_grid_toggled)

    hbox = gtk.HBox(False, 5)
    vbox.add(hbox)

    check = gtk.CheckButton("Show Grid")
    check.set_property('active', self.mag.show_grid)
    check.connect('toggled', self.grid_check_toggled)
    hbox.add(check)
    self.grid_check = check

    spin = gtk.SpinButton()
    spin.set_range(1,50)
    spin.set_increments(1,10)
    spin.set_property('value', self.mag.zoom)
    spin.connect('value-changed', self.zoom_spin_value_changed)
    hbox.add(spin)
    self.zoom_spin = spin

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
    vbox.add(frame)

    self.colorpicker = ColorPicker()
    frame.add(self.colorpicker)

  def __init__(self):
    self.palette = Palette()
    self.color = Color()
    self.build_gui()

    self.load_config()

    #XXX do this in load_config?
    if (self.conf['color']):
      self.color.set_hex(self.conf['color'])
    if (self.conf['zoom_level']):
      self.mag.set_zoom(int(self.conf['zoom_level']))
    if (self.conf['show_grid']):
      self.mag.set_show_grid(int(self.conf['show_grid']))
    if (self.conf['grab_rate']):
      self.mag.grab_rate = int(self.conf['grab_rate'])
    if (self.conf['palette']):
      path = os.path.join(base.save_config_dir(), 'palettes', self.conf['palette'])
      self.palette.load(path)
    else:
      self.palette.filename = 'elicit.gpl'

if __name__ == "__main__":
  el = Elicit();
  el.show()
  el.main()

