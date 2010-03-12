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

    self.measuring = False
    self.measure_rect = None

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
    pan_x = int(pan_x)
    pan_y = int(pan_y)
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

  def origin(self):
    x0 = (self.allocation.width - self.pixbuf_width)/2 + self.pan_x
    y0 = (self.allocation.height - self.pixbuf_height)/2 + self.pan_y
    return (x0,y0)

  def coord_widget_to_pixbuf(self, x, y):
    x0,y0 = self.origin()
    return (int((x - x0) / self.zoom), int((y - y0) / self.zoom))

  def coord_pixbuf_to_widget(self, x, y):
    x0,y0 = self.origin()
    return (x * self.zoom + x0, y * self.zoom + y0)

  def cb_button_press(self, widget, event):
    if event.button == 1:
      if event.state & gdk.CONTROL_MASK:
        self.measuring = True
        self.measure_start = (event.x, event.y)
        self.measure_rect = None
        self.queue_draw()
      else:
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
    y0 = (self.allocation.height - self.pixbuf_height)/2

    # place new location of pixel clicked under mouse
    pan_x = event.x - (dx * zoom / old_zoom + x0)
    pan_y = event.y - (dy * zoom / old_zoom + y0)
    self.pan(pan_x, pan_y)

  def cb_button_release(self, widget, event):
    if event.button == 1:
      self.measuring = False
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

    elif self.measuring:
      x0, y0 = self.coord_widget_to_pixbuf(*self.measure_start)
      x1, y1 = self.coord_widget_to_pixbuf(event.x, event.y)

      if x0 > x1:
        x0, x1 = x1, x0
      if y0 > y1:
        y0, y1 = y1, y0

      rect = gdk.Rectangle(x0, y0, x1-x0+1 , y1-y0+1)
      if rect != self.measure_rect:
        self.measure_rect = rect
        self.queue_draw()

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


    #XXX install cursor and use config path to load it
    pbuf = gdk.pixbuf_new_from_file("../data/magnify.png")
    if pbuf:
      self.cursor = gdk.Cursor(self.window.get_display(), pbuf, 6, 6);
      self.window.set_cursor(self.cursor)

    self.pixbuf_width = int(self.allocation.width);
    self.pixbuf_height = int(self.allocation.height);
    self.raw_width = int(self.allocation.width / self.zoom);
    self.raw_height = int(self.allocation.height / self.zoom);

    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)
    self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

    self.measure_gc = gdk.GC(self.window)
    self.measure_gc.set_foreground(self.measure_gc.get_colormap().alloc("#fff"))
    self.measure_gc.set_background(self.measure_gc.get_colormap().alloc("#000"))
    self.measure_gc.set_dashes(0,(4,4))
    self.measure_gc.set_line_attributes(1, gdk.LINE_DOUBLE_DASH, gdk.CAP_BUTT, gdk.JOIN_MITER)

    self.grid_gc = gdk.GC(self.window)
    self.grid_gc.set_foreground(self.measure_gc.get_colormap().alloc("#777"))

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("scroll-event", self.cb_scroll)

    self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.pixbuf_width, self.pixbuf_height)
    self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

  def do_unrealize(self):
    self.window.destroy()

  def do_size_request(self, requisition):
    requisition.height = 200
    requisition.width = 220

  def do_size_allocation(self, allocation):
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    if self.has_data == False: return

    # center image in given space
    r = gdk.Rectangle(
      int((self.allocation.width - self.pixbuf_width) / 2 + self.pan_x),
      int((self.allocation.height - self.pixbuf_height) / 2 + self.pan_y),
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
        self.window.draw_line(self.grid_gc, x, r.y, x, r.y + r.height)

      for y in range(ymin, ymax, self.zoom):
        self.window.draw_line(self.grid_gc, r.x, y, r.x + r.width, y)

    if (self.measure_rect):
      x, y = self.coord_pixbuf_to_widget(self.measure_rect.x, self.measure_rect.y)
      w = self.measure_rect.width * self.zoom
      h = self.measure_rect.height * self.zoom
      r = gdk.Rectangle(x,y,w,h)
      r = r.intersect(event.area)
      if (r.width > 0 and r.height > 0):
        self.window.draw_rectangle(self.measure_gc, False, *r)


gobject.type_register(Magnifier)


