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

    self.button = gtk.Button("Button")
    vbox.add(self.button)



if __name__ == "__main__":
  gobject.type_register(Magnifier) #XXX where should this go in general?

  el = Elicit();
  el.show()
  el.main()
