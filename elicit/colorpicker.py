import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import os

from color import Color
from color_dnd_helper import ColorDndHelper

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

class ColorPicker(gtk.Widget):
  """
  A widget to select colors from the screen

  This displays the currently selected color and handles grabbing a color
  from anywhere on screen.

  It also allows dragging and dropping of colors from and onto the widget.

  Signals:
    'save-color' - save the current color
  """
  data_path = os.path.join(os.path.dirname(__file__), 'data')
  icon_path = os.path.join(data_path, 'icons')

  __gsignals__ = {
      'save-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
  }

  def __init__(self):
    """ Initialize color picker """
    super(ColorPicker, self).__init__()
    self.pick_rate = 60
    self.color = Color()
    self.picking = 0
    self.pick_timeout = None
    self.save_on_release = False

  def set_color(self, color):
    """
    Set the color object to store selected colors in

    This color object is updated when a new color is selected or dropped
    on the widget.

    To explicitly change the selected color, do not use this function, but
    instead call set_rgb() or set_hsv() on the current color object.
    """
    self.color = color
    self.color.connect('changed', self.color_changed)

  def color_changed(self, color):
    """ Callback for color changes """
    if not self.flags() & gtk.REALIZED: return

    r,g,b = self.color.rgb16()
    col = self.gc.get_colormap().alloc_color(r, g, b, False, False)
    self.gc.set_foreground(col)
    self.queue_draw()

  def pick_immediate(self, x, y):
    """
    Select the color at the specified pixel

    The coordinates are relative to the screen.
    """

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
    """ Callback for pick timeout """
    # repeat time until we've realized the widget
    if self.flags() & gtk.REALIZED == False:
      return True

    # widget is realized, so grab data and end timer
    self.pick_immediate(self.pick_x, self.pick_y)
    self.pick_timeout = None
    return False

  def cb_drag_set_color(self, color, x, y):
    """ Drag set color callback """
    self.color.set_rgb(*color.rgb())
    return True

  def cb_drag_get_color(self):
    """ Drag get color callback """
    return self.color

  def pick(self, x, y):
    """
    Select the color at the specified location

    This does not immediately select the color, but instead sets a timeout
    so that the color selection occurs at most self.pick_rate times per
    second.
    """
    self.pick_x, self.pick_y = int(x), int(y)

    if (self.pick_timeout == None):
      self.pick_timeout = glib.timeout_add(1000 / self.pick_rate, self.cb_pick_timeout)


  def pick_start(self):
    self.picking = True
    gdk.pointer_grab(self.window, True, gdk.POINTER_MOTION_MASK | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK, None, None, 0L)
    self.grab_add()

  def pick_stop(self):
    self.picking = False
    gdk.pointer_ungrab()
    self.grab_remove()

  def cb_button_press(self, widget, event):
    """ Callback for mouse button press events """
    if (event.button == 1):
      self.pick_start
      self.picking = True
    elif (event.button == 3):
      self.save_on_release = True

  def cb_button_release(self, widget, event):
    """ Callback for mouse button release events """
    if (event.button == 1):
      if self.picking:
        self.pick_stop()
    elif (event.button == 3 and self.save_on_release):
      self.save_on_release = False
      self.emit('save-color')

  def cb_drag_begin(self, widget, event):
    """ Callback for mouse drag begin events """
    self.save_on_release = False

  def cb_motion_notify(self, widget, event):
    """ Callback from mouse motion notify events """
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
    """ Realize the widget """
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

    pbuf = gdk.pixbuf_new_from_file(os.path.join(self.icon_path, "dropper.png"))
    if pbuf:
      self.cursor = gdk.Cursor(self.window.get_display(), pbuf, 8, 21);
      self.window.set_cursor(self.cursor)

    self.set_tooltip_text('Click and drag:\n  Left: select color\n  Right: DnD color\n\nRight click: add to palette')

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("drag-begin", self.cb_drag_begin)

    self.dnd_helper = ColorDndHelper(self, self.cb_drag_set_color, self.cb_drag_get_color, gtk.gdk.BUTTON3_MASK)

    self.raw_width = 1
    self.raw_height = 1
    self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

  def do_unrealize(self):
    """ Unrealize widget """
    self.window.destroy()

  def do_size_request(self, requisition):
    """ Set default size """
    requisition.height = 40
    requisition.width = 40

  def do_size_allocation(self, allocation):
    """ Handle size changes """
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    """
    Draw the widget

    Just a big rectangle of the currently selected color
    """
    self.window.draw_rectangle(self.gc, True, 
        event.area.x, event.area.y,
        event.area.width, event.area.height)

gobject.type_register(ColorPicker)


