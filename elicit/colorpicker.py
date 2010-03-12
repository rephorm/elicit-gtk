import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import os

from color import Color

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

class ColorPicker(gtk.Widget):
  data_path = os.path.join(os.path.dirname(__file__), 'data')
  icon_path = os.path.join(data_path, 'icons')

  __gsignals__ = {
      'save-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
  }

  def __init__(self):
    super(ColorPicker, self).__init__()
    self.pick_rate = 60
    self.color = Color()
    self.picking = 0
    self.pick_timeout = None

  def set_color(self, color):
    self.color = color
    self.color.connect('changed', self.color_changed)

  def color_changed(self, color):
    if not self.flags() & gtk.REALIZED: return

    r,g,b = self.color.rgb16()
    col = self.gc.get_colormap().alloc_color(r, g, b, False, False)
    self.gc.set_foreground(col)
    self.queue_draw()

  def pick_immediate(self, x, y):
    if self.flags() & gtk.REALIZED == False: return

    # grab raw screen data
    self.raw_pixbuf.get_from_drawable(
        gdk.get_default_root_window(),
        gdk.colormap_get_system(),
        x, y,
        0, 0,
        self.raw_width, self.raw_height)

    #pull out rgb value
    #XXX first time this is called generates a warning and doesn't work.
    #    all subsequent times are fine. why?
    r,g,b = self.raw_pixbuf.get_pixels_array()[0,0]
    self.color.set_rgb(r,g,b)

  def cb_pick_timeout(self):
    # repeat time until we've realized the widget
    if self.flags() & gtk.REALIZED == False:
      return True

    # widget is realized, so grab data and end timer
    self.pick_immediate(self.pick_x, self.pick_y)
    self.pick_timeout = None
    return False

  def pick(self, x, y):
    self.pick_x, self.pick_y = int(x), int(y)

    if (self.pick_timeout == None):
      self.pick_timeout = glib.timeout_add(1000 / self.pick_rate, self.cb_pick_timeout)

  def cb_button_press(self, widget, event):
    if (event.button == 1):
      self.picking = True
    if (event.button == 3):
      self.emit('save-color')

  def cb_button_release(self, widget, event):
    if (event.button == 1):
      self.picking = False

  def cb_motion_notify(self, widget, event):
    if (self.picking):
      root_w, root_h = gdk.get_default_root_window().get_size()
      x = event.x_root
      y = event.y_root

      if (x < 0): x = 0
      if (x >= root_w): x = root_w - 1
      if (y < 0): y = 0
      if (y >= root_h): y = root_h - 1

      self.pick(x, y)

  def do_realize(self):
    self.set_flags(self.flags() | gtk.REALIZED)

    self.window = gdk.Window(
        self.get_parent_window(),
        width = self.allocation.width,
        height = self.allocation.height,
        window_type = gdk.WINDOW_CHILD,
        wclass = gdk.INPUT_OUTPUT,
        event_mask = self.get_events()
          | gdk.EXPOSURE_MASK 
          | gdk.BUTTON1_MOTION_MASK
          | gdk.BUTTON_PRESS_MASK
          | gdk.BUTTON_RELEASE_MASK
          | gdk.POINTER_MOTION_MASK
          | gdk.POINTER_MOTION_HINT_MASK)


    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)
    self.gc = self.window.new_gc()
    self.color_changed(self.color)

    #XXX install cursor and use config path to load it
    pbuf = gdk.pixbuf_new_from_file(os.path.join(self.icon_path, "dropper.png"))
    if pbuf:
      self.cursor = gdk.Cursor(self.window.get_display(), pbuf, 8, 21);
      self.window.set_cursor(self.cursor)


    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)

    self.raw_width = 1
    self.raw_height = 1
    self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

  def do_unrealize(self):
    self.window.destroy()

  def do_size_request(self, requisition):
    requisition.height = 40
    requisition.width = 40

  def do_size_allocation(self, allocation):
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    self.window.draw_rectangle(self.gc, True, 
        event.area.x, event.area.y,
        event.area.width, event.area.height)

gobject.type_register(ColorPicker)


