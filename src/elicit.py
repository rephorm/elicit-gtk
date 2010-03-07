import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk

from magnifier import Magnifier

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit



class Elicit:
  def quit(self, widget, data=None):
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

  def __init__(self):
    self.win = gtk.Window()
    self.win.set_title("test")
    self.win.connect('destroy', gtk.main_quit, None)

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


    self.button = gtk.Button("Button")
    vbox.add(self.button)



if __name__ == "__main__":
  el = Elicit();
  el.show()
  el.main()
