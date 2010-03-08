import math
import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit


class Magnifier(gtk.Widget):
  __gsignals__ = {
      'zoom-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
      'grid-toggled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
  }

  def __init__(self):
    super(Magnifier, self).__init__()

    self.zoom = 5
    self.grab_rate = 60
    self.grab_timeout = None
    self.show_grid = True
    self.grabbing = False
    self.has_data = False

    self.panning = False
    self.pan_x = 0
    self.pan_y = 0

  def grab_immediate(self, x, y, w, h):
    self.screen_rect = gdk.Rectangle(x, y, w, h)
    self.pan_x = 0
    self.pan_y = 0

    # if we're grabbing a different size, create new pixbuf of correct size
    if (self.screen_rect.width != self.raw_width or self.screen_rect.height != self.raw_height):
      self.raw_width = self.screen_rect.width
      self.raw_height = self.screen_rect.height
      self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

    # grab raw screen data
    self.raw_pixbuf.get_from_drawable(
        gdk.get_default_root_window(),
        gdk.colormap_get_system(),
        self.screen_rect.x, self.screen_rect.y,
        0, 0,
        self.screen_rect.width, self.screen_rect.height)

    self.has_data = True

    self.scale()

  def scale(self):
    if self.has_data == False: return

    if (self.pixbuf_height != self.raw_height * self.zoom or
        self.pixbuf_width != self.raw_width * self.zoom):
      self.pixbuf_width = int(self.raw_width * self.zoom)
      self.pixbuf_height = int(self.raw_height * self.zoom)
      self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8,
          self.pixbuf_width, self.pixbuf_height)

    # scale up by zoom factor
    self.raw_pixbuf.scale(self.pixbuf, 0, 0,
        self.pixbuf_width, self.pixbuf_height,
        0, 0,
        self.zoom, self.zoom,
        gdk.INTERP_NEAREST)
    self.queue_draw()

  def set_show_grid(self, show_grid):
    if (self.show_grid != show_grid):
      self.show_grid = show_grid
      self.emit("grid-toggled")
      self.queue_draw()

  def set_zoom(self, zoom):
    zoom = int(zoom)
    if (zoom <= 0): zoom = 1
    if (self.zoom != zoom):
      self.zoom = zoom
      self.emit("zoom-changed")
      self.scale()

  def pan(self, pan_x, pan_y):
    xmax = (self.pixbuf_width - self.allocation.width) / 2
    ymax = (self.pixbuf_height - self.allocation.height) / 2

    if xmax > 0:
      if pan_x > 0 and pan_x > xmax: pan_x = xmax
      if pan_x < 0 and pan_x < -xmax: pan_x = -xmax
    else:
      pan_x = 0

    if ymax > 0:
      if pan_y > 0 and pan_y > ymax: pan_y = ymax
      if pan_y < 0 and pan_y < -ymax: pan_y = -ymax
    else:
      pan_y = 0

    if self.pan_x == pan_x and self.pan_y == pan_y: return

    self.pan_x = pan_x
    self.pan_y = pan_y
    self.queue_draw()

  def set_grab_rate(self, grab_rate):
    grab_rate = int(grab_rate)
    if grab_rate <= 0: return
    if self.grab_rate != grab_rate:
      self.grab_rate = grab_rate

  def cb_grab_timeout(self):
    # repeat time until we've realized the widget
    if self.flags() & gtk.REALIZED == False:
      return True

    # widget is realized, so grab data and end timer
    self.grab_immediate(*self.grab_rect)
    self.grab_timeout = None
    return False
    

  def grab(self, x, y, w, h):
    self.grab_rect = gdk.Rectangle(int(x), int(y), int(w), int(h))

    if (self.grab_timeout == None):
      self.grab_timeout = glib.timeout_add(1000 / self.grab_rate, self.cb_grab_timeout)

  def cb_button_press(self, widget, event):
    if event.button == 1:
      self.grabbing = True
    elif event.button == 2:
      self.panning = True
      self.pan_start_x = event.x - self.pan_x
      self.pan_start_y = event.y - self.pan_y

  def cb_scroll(self, widget, event):
    old_zoom = zoom = self.zoom

    if (event.direction == gdk.SCROLL_UP):
      zoom += 1
    elif (event.direction == gdk.SCROLL_DOWN):
      zoom -= 1

    # find origin of image
    x0 = (self.allocation.width - self.pixbuf_width)/2 + self.pan_x
    y0 = (self.allocation.height - self.pixbuf_height)/2 + self.pan_y
    # find offset from clicked pixel to origin
    dx = event.x - x0
    dy = event.y - y0

    self.set_zoom(zoom)

    # find new origin, assuming no pan
    x0 = (self.allocation.width - self.pixbuf_width)/2
    y0 = (self.allocation.width - self.pixbuf_width)/2

    # place new location of pixel clicked under mouse
    pan_x = event.x - (dx * zoom / old_zoom + x0)
    pan_y = event.y - (dy * zoom / old_zoom + y0)
    self.pan(pan_x, pan_y)

  def cb_button_release(self, widget, event):
    if event.button == 1:
      self.grabbing = False
    elif event.button == 2:
      self.panning = False

  def cb_motion_notify(self, widget, event):
    if self.grabbing:
      root_w, root_h = gdk.get_default_root_window().get_size()
      w = int(math.ceil(float(self.allocation.width) / self.zoom))
      h = int(math.ceil(float(self.allocation.height) / self.zoom))
      x = event.x_root - int(w / 2)
      y = event.y_root - int(h / 2)

      if (x < 0): x = 0
      if (x > root_w - w): x = root_w - w
      if (y < 0): y = 0
      if (y > root_h - h): y = root_h - h

      self.grab(x, y, w, h)

    elif self.panning:
      pan_x = int(event.x - self.pan_start_x)
      pan_y = int(event.y - self.pan_start_y)

      self.pan(pan_x, pan_y)

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


    self.pixbuf_width = self.allocation.width;
    self.pixbuf_height = self.allocation.height;
    self.raw_width = int(self.allocation.width / self.zoom);
    self.raw_height = int(self.allocation.height / self.zoom);

    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)
    self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("scroll-event", self.cb_scroll)

    self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.pixbuf_width, self.pixbuf_height)
    self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

  def do_unrealize(self):
    self.window.destroy()

  def do_size_request(self, requisition):
    requisition.height = 250
    requisition.width = 250

  def do_size_allocation(self, allocation):
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    if self.has_data == False: return

    # center image in given space
    r = gdk.Rectangle(
      int((self.allocation.width - self.pixbuf_width) / 2) + self.pan_x,
      int((self.allocation.height - self.pixbuf_height) / 2) + self.pan_y,
      self.pixbuf_width,
      self.pixbuf_height)

    r2 = r.intersect(event.area)

    self.window.draw_pixbuf(self.gc,
      self.pixbuf,
      r2.x - r.x, r2.y - r.y, 
      r2.x, r2.y,
      r2.width, r2.height,
      gdk.RGB_DITHER_NONE, 0, 0)

    if (self.show_grid):
      x_off = (r.x - r2.x) % self.zoom
      y_off = (r.y - r2.y) % self.zoom

      xmin = r2.x + x_off
      xmax = r2.x + r.width + 1
      ymin = r2.y + y_off
      ymax = r2.y + r.height + 1

      for x in range(xmin, xmax, self.zoom):
        self.window.draw_line(self.gc, x, r.y, x, r.y + r.height)

      for y in range(ymin, ymax, self.zoom):
        self.window.draw_line(self.gc, r.x, y, r.x + r.width, y)

gobject.type_register(Magnifier)


