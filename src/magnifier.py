import gobject
import gtk
import gtk.gdk as gdk
import glib
import pygtk

if gtk.pygtk_version < (2,0):
  print "PyGtk 2.0 is required."
  raise SystemExit

class Magnifier(gtk.Widget):
  def __init__(self):
    super(Magnifier, self).__init__()

    self.zoom = 5
    self.grab_rate = 60
    self.grab_timeout = None

    self.grabbing = False

  def grab_immediate(self, x, y, w, h):
    self.screen_rect = gdk.Rectangle(x, y, w, h)

    print("grab:\nscreen: {0}\nraw:{1},{2}\nscaled:{3},{4}\nzoom:{5}".format(self.screen_rect, self.raw_width, self.raw_height, self.pixbuf_width, self.pixbuf_height, self.zoom))

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

    self.scale()

  def scale(self):
    if (self.pixbuf_height != self.raw_height * self.zoom or
        self.pixbuf_width != self.raw_width * self.zoom):
      self.pixbuf_width = self.raw_width * self.zoom
      self.pixbuf_height = self.raw_height * self.zoom
      self.pixbuf = gdk.Pixbuf(gdk.COLORSPACE_RGB, False, 8,
          self.pixbuf_width, self.pixbuf_height)

    # scale up by zoom factor
    self.raw_pixbuf.scale(self.pixbuf, 0, 0,
        self.pixbuf_width, self.pixbuf_height,
        0, 0,
        self.zoom, self.zoom,
        gdk.INTERP_NEAREST)
    self.queue_draw()

  def cb_grab_timeout(self):
    # repeat time until we've realized the widget
    if self.flags() & gtk.REALIZED == False:
      return True

    # widget is realized, so grab data and end timer
    self.grab_immediate(*self.grab_rect)
    self.grab_timeout = None
    return False
    

  def grab(self, x, y, w, h):
    self.grab_rect = gdk.Rectangle(x, y, w, h)

    if (self.grab_timeout == None):
      self.grab_timeout = glib.timeout_add(1000 / self.grab_rate, self.cb_grab_timeout)

  def cb_button_press(self, widget, event):
    if (event.button == 1):
      self.grabbing = True

  def cb_scroll(self, widget, event):
    zoom = self.zoom
    if (event.direction == gdk.SCROLL_UP):
      zoom += 1
    elif (event.direction == gdk.SCROLL_DOWN):
      zoom -= 1

    if (zoom <= 0): zoom = 1
    if (self.zoom != zoom):
      self.zoom = zoom
      self.scale()

  def cb_button_release(self, widget, event):
    if (event.button == 1):
      self.grabbing = False

  def cb_motion_notify(self, widget, event):
    if (self.grabbing):
      root_w, root_h = gdk.get_default_root_window().get_size()
      w = int(self.allocation.width / self.zoom)
      h = int(self.allocation.height / self.zoom)
      x = event.x_root - int(w / 2)
      y = event.y_root - int(h / 2)

      if (x < 0): x = 0
      if (x > root_w - w): x = root_w - w
      if (y < 0): y = 0
      if (y > root_h - h): y = root_h - h

      self.grab(x, y, w, h)

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
    # center image in given space
    r = gdk.Rectangle(
      int((self.allocation.width - self.pixbuf_width) / 2),
      int((self.allocation.height - self.pixbuf_height) / 2),
      self.pixbuf_width,
      self.pixbuf_height)

    r = r.intersect(event.area)

    self.window.draw_pixbuf(self.gc,
      self.pixbuf,
      0, 0, 
      r.x, r.y,
      r.width, r.height,
      gdk.RGB_DITHER_NONE, 0, 0)
