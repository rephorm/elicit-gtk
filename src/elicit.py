import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import gconf
import os

import xdg.BaseDirectory as base

from magnifier import Magnifier
from colorpicker import ColorPicker

from palette import Palette
from color import Color
from palette_view import PaletteView

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

class Elicit:
  appname = 'elicit'

  def quit(self, widget, data=None):
    self.palette.save()
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
    self.gconf.set_int('/apps/elicit/zoom_level', mag.zoom)

  def grid_check_toggled(self, check):
    self.gconf.set_bool('/apps/elicit/show_grid', check.get_property('active'))

  def zoom_spin_value_changed(self, spin):
    self.gconf.set_int('/apps/elicit/zoom_level', int(spin.get_property('value')))

  def picker_save_color(self, picker):
    c = Color()
    c.set_rgb(*picker.color.rgb())
    self.palette.append(c)

  def palette_view_select_color(self, palette_view, color):
    self.gconf.set_string('/apps/elicit/color', color.hex())

  def palette_view_delete_color(self, palette_view, color):
    self.palette.remove(color)

  def build_gui(self):
    self.win = gtk.Window()
    self.win.set_title("Elicit")
    self.win.connect('destroy', self.quit, None)

    vbox = gtk.VBox(False, 5)
    self.win.add(vbox)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
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
    frame.set_shadow_type(gtk.SHADOW_IN)
    vbox.add(frame)

    self.colorpicker = ColorPicker()
    frame.add(self.colorpicker)
    self.colorpicker.connect('save-color', self.picker_save_color)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    vbox.add(frame)

    self.palette_view = PaletteView()
    self.palette_view.connect('select-color', self.palette_view_select_color)
    self.palette_view.connect('delete-color', self.palette_view_delete_color)
    frame.add(self.palette_view)

  def init_config(self):
    self.gconf = gconf.client_get_default()
    self.gconf.add_dir('/apps/elicit', preload=True)
    self.gconf_id = self.gconf.notify_add("/apps/elicit", self.config_changed)

    color = self.gconf.get_string('/apps/elicit/color')
    if color: self.color.set_hex(color)

    zoom_level = self.gconf.get_int('/apps/elicit/zoom_level')
    self.mag.set_zoom(zoom_level)
    self.zoom_spin.set_property('value', self.mag.zoom)

    grab_rate = self.gconf.get_int('/apps/elicit/grab_rate')
    if grab_rate > 0: self.mag.grab_rate = grab_rate

    show_grid = self.gconf.get_bool('/apps/elicit/show_grid')
    self.mag.set_show_grid(show_grid)
    self.grid_check.set_property('active', self.mag.show_grid)

    palette = self.gconf.get_string('/apps/elicit/palette')
    if not palette: palette = 'elicit.gpl'

    self.palette.load(os.path.join(self.palette_dir, palette))

  def config_changed(self, client, gconf_id, entry, user_data):
    key = entry.key[13:]

    if key == 'color':
      hex = entry.value.get_string()
      self.color.set_hex(hex)
    elif key == 'zoom_level':
      self.mag.set_zoom(entry.value.get_int())
      self.zoom_spin.set_property('value', self.mag.zoom)
    elif key == 'show_grid':
      self.mag.set_show_grid(entry.value.get_bool())
      self.grid_check.set_property('active', self.mag.show_grid)
    elif key == 'palette':
      palette = entry.value.get_string()
      if not palette: palette = 'elicit.gpl'
      self.palette.load(os.path.join(self.palette_dir, palette))
    elif key == 'grab_rate':
      self.mag.set_grab_rate(entry.value.get_int())

  def __init__(self):
    self.palette = Palette()
    self.color = Color()
    self.build_gui()

    self.palette_view.set_palette(self.palette)
    self.colorpicker.set_color(self.color)

    self.palette_dir = os.path.join(base.save_config_path(self.appname), 'palettes')

    self.init_config()
    #self.load_config()
    #self.palette.load(path)

if __name__ == "__main__":
  el = Elicit();
  el.show()
  el.main()

