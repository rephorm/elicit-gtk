import math
import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk
import os

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit


class Magnifier(gtk.Widget):
  """
  Magnifier Widget

  A widget to handle magnification of regions of the screen.

  Parameters:
    zoom: the magnification level
    show_grid: whether to draw a pixel grid or not
    grab_rate: the rate at which to update the magnified image

  Emits the following signals:
    'zoom-changed'
    'grid-toggled'
    'measure-changed'
    'location-changed'
  """
  TARGET_TYPE_IMAGE = 81

  data_path = os.path.join(os.path.dirname(__file__), 'data')
  icon_path = os.path.join(data_path, 'icons')

  __gsignals__ = {
      'zoom-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
      'grid-toggled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
      'measure-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
      'location-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
  }

  tooltip = 'Click and drag:\n  Left: drag-n-drop image\n  Middle: pan\n  Right: measure\n\nScroll: zoom'

  def __init__(self):
    """Initialized the widget"""
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

    self.cursors = {}
    self.cursor = None

    self.set_flags(self.flags() |  gtk.CAN_FOCUS)

    self.set_tooltip_text(self.tooltip)

  def grab_immediate(self, x, y, w, h):
    """
    Copy pixels from the region specified by (x,y,w,h) into internal pixbuf

    The coordinates are relative to the screen in units of pixels.

    The grabbed image data is stored in raw_pixbuf.

    This involves copying image data from the server to the client and thus
    is not the quickest of operations.
    Do not call more often than necessary.
    """


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

    self.emit('location-changed')
    self.has_data = True

    self.scale()

  def scale(self):
    """
    Scale grabbed image data by zoom factor

    The image data in raw_pixbuf is scaled by the zoom factor and the scaled
    image data is stored in pixbuf.

    This queues the widget to be redrawn.
    """
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
    """Set whether to show pixel grid or not"""
    if (self.show_grid != show_grid):
      self.show_grid = show_grid
      self.emit("grid-toggled")
      self.queue_draw()

  def set_zoom(self, zoom):
    """Set zoom factor"""
    zoom = int(zoom)
    if (zoom <= 0): zoom = 1
    if (self.zoom != zoom):
      self.zoom = zoom
      self.emit("zoom-changed")
      self.scale()

  def pan(self, pan_x, pan_y):
    """
    Set current pan

    The pan is specified as a pixel offset in the x and y directions.

    At 0 pan, the magnified image is centered within the widget allocation.
    A positive pan moves the image right / down.
    """
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
    """
    Set the maximum rate at which to grab pixel data

    The grab rate is specified in grabs per second.
    This is ignored when using grab_immediate()
    """
    grab_rate = int(grab_rate)
    if grab_rate <= 0: return
    if self.grab_rate != grab_rate:
      self.grab_rate = grab_rate

  def cb_grab_timeout(self):
    """
    The timeout callback for grab()

    This calls grab_immediate unless the widget is not yet realized.
    """
    # repeat time until we've realized the widget
    if self.flags() & gtk.REALIZED == False:
      return True

    # widget is realized, so grab data and end timer
    self.grab_immediate(*self.grab_rect)
    self.grab_timeout = None
    return False

  def grab(self, x, y, w, h):
    """
    Grab a region of the screen specified by (x,y,w,h)

    The region is in screen coordinates.
    After storing the region, a timeout is added so that the grunt work
    of actually grabbing the screen data occurs at most every
    1/grab_rate seconds.
    """
    self.grab_rect = gdk.Rectangle(int(x), int(y), int(w), int(h))

    if (self.grab_timeout == None):
      self.grab_timeout = glib.timeout_add(1000 / self.grab_rate, self.cb_grab_timeout)

  def set_cursor(self, type):
    """
    Set the cursor to display when over the widget

    There are currently two types:
      'magnify' - a magnifying glass
      'measure' - a ruler
    """
    if (type == None):
      self.cursor = None
    else:
      if self.cursor == self.cursors[type]: return
      self.cursor = self.cursors[type]

    self.window.set_cursor(self.cursor)


  def origin(self):
    """
    Calculate the origin of the magnified image

    The origin (top left corner) is returned as a tuple (x0,y0) relative
    to the widget.
    """
    x0 = (self.allocation.width - self.pixbuf_width)/2 + self.pan_x
    y0 = (self.allocation.height - self.pixbuf_height)/2 + self.pan_y
    return (x0,y0)

  def coord_widget_to_pixbuf(self, x, y):
    """
    Convert widget coordinates to pixbuf coordinates

    This finds the pixel of raw_pixbuf that is displayed at the provided
    coordinate.
    """
    x0,y0 = self.origin()
    return (int((x - x0) / self.zoom), int((y - y0) / self.zoom))

  def coord_pixbuf_to_widget(self, x, y):
    """
    Convert pixbuf coordinates to widget coordinates

    This finds the location relative to the widget at which the provided
    pixel of raw_pixbuf is displayed.
    """
    x0,y0 = self.origin()
    return (x * self.zoom + x0, y * self.zoom + y0)

  def grab_start(self):
    self.grabbing = True
    gdk.pointer_grab(self.window, False, gdk.POINTER_MOTION_MASK | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK, None, self.cursors['magnify'], 0L)
    self.grab_add()

  def grab_stop(self):
    self.grabbing = False
    gdk.pointer_ungrab()
    self.grab_remove()

  def cb_button_press(self, widget, event):
    """
    Callback for mouse button press events

    The left button starts magnification
    Ctrl-left starts measuring on the magnified image
    The middle button starts panning
    """
    if self.grabbing:
      return

    self.set_tooltip_text("")

    if event.button == 3:
      if not self.has_data: return
      self.measuring = True
      self.set_cursor('measure')
      self.measure_start = (event.x, event.y)
      self.measure_rect = None
      self.emit('measure-changed')
      self.queue_draw()
    elif event.button == 2:
      self.panning = True
      self.pan_start_x = event.x - self.pan_x
      self.pan_start_y = event.y - self.pan_y

  def cb_scroll(self, widget, event):
    """
    Callback for mouse wheel scroll events

    Changes the zoom factor by one in the direction scrolled.
    Scroll up zooms in, down zooms out.

    The pan value is also updated so that the pixel of the raw_pixbuf
    that is under the mouse when the event is received remains under
    the mouse. This allows one to zoom in on a specific region by moving
    the mouse there before scrolling.
    """
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
    """
    Callback for mouse button release events

    Stops magnifying, measuring or panning.
    """
    if self.grabbing:
      self.grab_stop()
    else:
      if event.button == 3:
        self.measuring = False
        self.set_cursor(None)
      elif event.button == 2:
        self.panning = False

    self.set_tooltip_text(self.tooltip)

  def cb_motion_notify(self, widget, event):
    """
    Callback for mouse motion notify events

    If magnifying, calculates the size of a region centered on the
    mouse cursor that is just large enough to fill the widget when
    scaled up by the zoom factor. Then queues a grab of this region.

    If measuring, updates measurement rectangle.

    If panning, updates pan.
    """
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
        self.emit('measure-changed')
        self.queue_draw()

  def do_realize(self):
    """
    Realize the widget

    This creates the server resources (gdk window, cursors, pixbufs, etc)
    and sets up drag and drop handlers
    """
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

    pbuf = gdk.pixbuf_new_from_file(os.path.join(self.icon_path,"magnify.png"))
    self.cursors['magnify'] = gdk.Cursor(self.window.get_display(), pbuf, 6, 6);

    pbuf = gdk.pixbuf_new_from_file(os.path.join(self.icon_path,"measure.png"))
    self.cursors['measure'] = gdk.Cursor(self.window.get_display(), pbuf, 6, 6);

    #self.set_cursor('magnify')

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
    self.measure_gc.set_foreground(self.measure_gc.get_colormap().alloc_color("#fff"))
    self.measure_gc.set_background(self.measure_gc.get_colormap().alloc_color("#000"))
    self.measure_gc.set_dashes(0,(4,4))
    self.measure_gc.set_line_attributes(1, gdk.LINE_DOUBLE_DASH, gdk.CAP_BUTT, gdk.JOIN_MITER)

    self.grid_gc = gdk.GC(self.window)
    self.grid_gc.set_foreground(self.measure_gc.get_colormap().alloc_color("#777"))

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("scroll-event", self.cb_scroll)

    self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.pixbuf_width, self.pixbuf_height)
    self.raw_pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8, self.raw_width, self.raw_height)

    target_list = gtk.target_list_add_image_targets(None, self.TARGET_TYPE_IMAGE, True)
    self.drag_source_set(gtk.gdk.BUTTON1_MASK, target_list, gtk.gdk.ACTION_COPY)
    self.connect("drag-data-get", self.cb_drag_data_get)


  def cb_drag_data_get(self, widget, context, selection, target_type, time):
    if not self.has_data:
      return

    if target_type == self.TARGET_TYPE_IMAGE:
      selection.set_pixbuf(self.raw_pixbuf)

  def do_unrealize(self):
    self.window.destroy()

  def do_size_request(self, requisition):
    """
    Specify default size
    """
    requisition.height = 200
    requisition.width = 220

  def do_size_allocation(self, allocation):
    """
    Handle size changes
    """
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    """
    Draw the widget

    The scaled pixbuf is initially centered within the widget, and then
    offset by the current pan value.

    On top of this, a grid indicating the pixel size is drawn if draw_grid is true.

    Finally, a dashed box is drawn if a measurement is currently active.
    """
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

    # the pixel grid is not drawn if zoom is 1, since it would fill the
    # entire image area
    if self.show_grid and self.zoom != 1:
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


