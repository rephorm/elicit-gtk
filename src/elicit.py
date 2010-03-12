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
from palette_tools import PaletteList, PaletteCombo

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
    self.grid_check.set_active(mag.show_grid)

  def mag_zoom_changed(self, mag):
    self.gconf.set_int('/apps/elicit/zoom_level', mag.zoom)

  def grid_check_toggled(self, check):
    self.gconf.set_bool('/apps/elicit/show_grid', check.get_active())

  def zoom_spin_value_changed(self, spin):
    self.gconf.set_int('/apps/elicit/zoom_level', int(spin.get_value()))

  def picker_save_color(self, picker):
    c = Color()
    c.set_rgb(*picker.color.rgb())
    self.palette.append(c)
    self.palette_view.select(c)

  def palette_view_select_color(self, palette_view, color):
    if color == None:
      self.color_name_entry.set_text("")
      self.color_name_entry.set_sensitive(False)
    else:
      self.gconf.set_string('/apps/elicit/color', color.hex())
      self.color_name_entry.set_text(color.name)
      self.color_name_entry.set_sensitive(True)

  def palette_view_delete_color(self, palette_view, color):
    self.palette.remove(color)

  def color_name_entry_changed(self, color_name_entry):
    if self.palette and self.palette_view.selected:
      self.palette_view.selected.name = color_name_entry.get_text()

  def color_changed(self, color):
    self.colorspin['r'].set_value(self.color.r)
    self.colorspin['g'].set_value(self.color.g)
    self.colorspin['b'].set_value(self.color.b)
    self.colorspin['h'].set_value(self.color.h)
    self.colorspin['s'].set_value(self.color.s)
    self.colorspin['v'].set_value(self.color.v)
    self.hex_label.set_label(self.color.hex())
    if self.palette_view.selected and color.hex() != self.palette_view.selected.hex():
      self.palette_view.select(None)

  def color_spin_rgb_changed(self, spin):
    r,g,b = self.color.rgb()
    if spin == self.colorspin['r']:
      r = spin.get_value()
    elif spin == self.colorspin['g']:
      g = spin.get_value()
    elif spin == self.colorspin['b']:
      b = spin.get_value()
    self.color.set_rgb(r,g,b)

  def color_spin_hsv_changed(self, spin):
    h,s,v = self.color.hsv()
    if spin == self.colorspin['h']:
      h = spin.get_value()
    elif spin == self.colorspin['s']:
      s = spin.get_value()
    elif spin == self.colorspin['v']:
      v = spin.get_value()
    self.color.set_hsv(h,s,v)

  def palette_combo_selected(self, combo, palette):
    if (self.palette != palette):
      if (palette.filename):
        self.gconf.set_string('/apps/elicit/palette', os.path.basename(palette.filename))
      if self.palette:
        old_filename = self.palette.filename
        self.palette.save()

        #update palette list with new filename
        if old_filename != self.palette.filename:
          index = self.palette_list.index_of_palette(self.palette)
          self.palette_list[index][1] = self.palette.filename

      self.palette = palette
      self.palette_view.set_palette(self.palette)
      self.color_name_entry.set_sensitive(False)

  def add_palette(self, button):
    p = Palette()
    p.name = "Untitled Palette"
    self.palette_list.append(p)
    self.palette_combo.select(self.palette_list.index_of_palette(p))

  def delete_palette(self, button):
    if not self.palette: return

    d = gtk.MessageDialog(self.win,
        gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
        gtk.BUTTONS_OK_CANCEL, None)

    d.set_markup("Are you sure you want to delete the palette <b>%s</b>? This cannot be undone." % self.palette.name)
    response = d.run()
    d.destroy()
    if response == gtk.RESPONSE_OK:
      p = self.palette
      self.palette_combo.remove(self.palette_list.index_of_palette(p))
      p.delete()

  def build_gui(self):
    self.win = gtk.Window()
    self.win.set_title("Elicit")
    self.win.connect('destroy', self.quit, None)

    vbox = gtk.VBox(False, 5)
    self.win.add(vbox)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    vbox.pack_start(frame, True, True)

    self.mag = Magnifier()
    frame.add(self.mag)
    self.mag.connect('zoom-changed', self.mag_zoom_changed)
    self.mag.connect('grid-toggled', self.mag_grid_toggled)

    hbox = gtk.HBox(False, 5)
    vbox.pack_start(hbox, False)

    check = gtk.CheckButton("Show Grid")
    check.set_active(self.mag.show_grid)
    check.connect('toggled', self.grid_check_toggled)
    hbox.pack_start(check)
    self.grid_check = check

    spin = gtk.SpinButton()
    spin.set_range(1,50)
    spin.set_increments(1,10)
    spin.set_value(self.mag.zoom)
    spin.connect('value-changed', self.zoom_spin_value_changed)
    hbox.pack_end(spin, False)
    self.zoom_spin = spin

    zoom_label = gtk.Label("Zoom:")
    hbox.pack_end(zoom_label, False)


    hbox = gtk.HBox(False, 5)
    vbox.pack_start(hbox, False)

    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    hbox.pack_start(frame, True, True)

    self.colorpicker = ColorPicker()
    frame.add(self.colorpicker)
    self.colorpicker.connect('save-color', self.picker_save_color)

    self.colorspin = {}
    # add RGB spinboxes
    table = gtk.Table(4,4)
    hbox.pack_start(table, False)

    row = 0
    for type in ("r","g","b"):
      label = gtk.Label(type.upper())
      table.attach(label, 0,1,row,row+1,0,0,2,2)
      spin = gtk.SpinButton()
      spin.set_range(0,255)
      spin.set_increments(1,10)
      spin.connect('value-changed', self.color_spin_rgb_changed)
      table.attach(spin, 1,2,row,row+1,gtk.FILL,gtk.EXPAND,2,2)
      self.colorspin[type] = spin
      row += 1

    row = 0
    for type in ("h","s","v"):
      label = gtk.Label(type.upper())
      table.attach(label, 2,3,row,row+1,0,0,2,2)
      spin = gtk.SpinButton()
      if type == 'h':
        spin.set_range(0,360)
        spin.set_increments(1,10)
      else:
        spin.set_digits(2)
        spin.set_range(0,1.0)
        spin.set_increments(.01,.1)
      spin.connect('value-changed', self.color_spin_hsv_changed)
      table.attach(spin, 3,4,row,row+1,gtk.FILL,gtk.EXPAND,2,2)
      self.colorspin[type] = spin
      row += 1

    self.hex_label = gtk.Label()
    self.hex_label.set_selectable(True)
    table.attach(self.hex_label,0,4,3,4,gtk.FILL,gtk.EXPAND,2,2)

    sep = gtk.HSeparator()
    vbox.pack_start(sep, False)

    # palette tools
    hbox = gtk.HBox(False, 5)
    vbox.pack_start(hbox, False)

    # Palette tools
    hbox.pack_start(gtk.Label("Palette:"), False)

    self.palette_combo = PaletteCombo()
    hbox.pack_start(self.palette_combo)
    self.palette_combo.connect('selected', self.palette_combo_selected)

    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD,gtk.ICON_SIZE_BUTTON))
    button.set_relief(gtk.RELIEF_NONE)
    button.connect('clicked', self.add_palette)
    hbox.pack_start(button, False)

    button = gtk.Button()
    button.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE,gtk.ICON_SIZE_BUTTON))
    button.set_relief(gtk.RELIEF_NONE)
    button.connect('clicked', self.delete_palette)
    hbox.pack_start(button, False)


    # palette view
    frame = gtk.Frame()
    frame.set_shadow_type(gtk.SHADOW_IN)
    vbox.pack_start(frame, False)

    self.palette_view = PaletteView()
    self.palette_view.connect('select-color', self.palette_view_select_color)
    self.palette_view.connect('delete-color', self.palette_view_delete_color)
    frame.add(self.palette_view)

    # color name entry / palette tools
    hbox = gtk.HBox(False, 5)
    vbox.pack_start(hbox, False)

    hbox.pack_start(gtk.Label("Color Name:"), False)

    self.color_name_entry = gtk.Entry()
    self.color_name_entry.set_sensitive(False)
    self.color_name_entry.connect('changed', self.color_name_entry_changed)
    hbox.pack_start(self.color_name_entry, False)

  def init_config(self):
    self.gconf = gconf.client_get_default()
    self.gconf.add_dir('/apps/elicit', preload=True)
    self.gconf_id = self.gconf.notify_add("/apps/elicit", self.config_changed)

    color = self.gconf.get_string('/apps/elicit/color')
    if color: self.color.set_hex(color)

    zoom_level = self.gconf.get_int('/apps/elicit/zoom_level')
    self.mag.set_zoom(zoom_level)
    self.zoom_spin.set_value(self.mag.zoom)

    grab_rate = self.gconf.get_int('/apps/elicit/grab_rate')
    if grab_rate > 0: self.mag.grab_rate = grab_rate

    show_grid = self.gconf.get_bool('/apps/elicit/show_grid')
    self.mag.set_show_grid(show_grid)
    self.grid_check.set_active(self.mag.show_grid)

    palette = self.gconf.get_string('/apps/elicit/palette')
    if not palette: palette = 'elicit.gpl'
    index = self.palette_list.index_of_file(palette)
    if index == None:
      index = 0
    self.palette_combo.select(index)

  def config_changed(self, client, gconf_id, entry, user_data):
    key = entry.key[13:]

    if key == 'color':
      hex = entry.value.get_string()
      self.color.set_hex(hex)
    elif key == 'zoom_level':
      self.mag.set_zoom(entry.value.get_int())
      self.zoom_spin.set_value(self.mag.zoom)
    elif key == 'show_grid':
      self.mag.set_show_grid(entry.value.get_bool())
      self.grid_check.set_active(self.mag.show_grid)
    elif key == 'palette':
      palette = entry.value.get_string()
      if not palette: palette = 'elicit.gpl'
      self.palette_combo.select(self.palette_list.index_of_file(palette))
    elif key == 'grab_rate':
      self.mag.set_grab_rate(entry.value.get_int())

  def __init__(self):
    self.palette = None
    self.color = Color()
    self.color.connect('changed', self.color_changed)
    self.build_gui()

    self.palette_dir = os.path.join(base.save_config_path(self.appname), 'palettes')
    Palette.PaletteDir = self.palette_dir

    self.palette_list = PaletteList()
    self.palette_list.load(self.palette_dir)
    self.palette_combo.set_model(self.palette_list)

    self.colorpicker.set_color(self.color)

    self.init_config()

if __name__ == "__main__":
  el = Elicit();
  el.show()
  el.main()

