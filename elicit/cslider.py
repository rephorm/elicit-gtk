import gobject
import gtk
from gtk import gdk
import glib
import cairo

from color import Color

class CSlider(gtk.Widget):
  """
  A color slider widget

  This displays a gradient giving the slice through color space
  along the slider's axis.

  Signals:
    'select-color' - a color has been selected.
    'delete-color' - a color should be deleted.

  Both of these signal handlers are passed the color as an additional
  parameter.
  """

  __gsignals__ = {
      }

  def __init__(self, color=None, mode=None):
    """
    Initialize color slider

    Parameters:
      color: Color to display in slider
      mode: color value for this slider
            can be 'r', 'g', 'b', 'h', 's' or 'v'
            TODO support CMYK
    
    """
    super(CSlider, self).__init__()

    self.pad = 2
    self.cpad = 1

    self.set_color(color)
    self.mode = mode

    self.selecting = False

  def color_changed(self, color):
    """Specify that the slider needs to be redrawn"""
    self.queue_draw()

  def set_color(self, color):
    """
    Set the color to display
    """
    self.color = color 
    if color:
      self.color.connect('changed', self.color_changed)
    self.queue_draw()

  def do_realize(self):
    """Realize the widget"""
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

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)

  def do_unrealize(self):
    """Unrealize the widget"""
    self.window.destroy()

  def do_size_request(self, requisition):
    """Set the default size"""
    requisition.height = 18
    requisition.width = 75

  def do_size_allocation(self, allocation):
    """Handle size changes"""
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    """
    Draw the widget
    """

    cr = self.window.cairo_create()

    gx,gy,gw,gh = self.gradient_geometry()
    grad = cairo.LinearGradient(gx,gy,gx+gw,gy)

    if self.mode in "rgb":
      r,g,b = [c/255.0 for c in self.color.rgb()]
      r1 = r2 = r
      g1 = g2 = g
      b1 = b2 = b
      if self.mode == 'r':
        f  = r
        r1 = 0
        r2 = 1
      elif self.mode == 'g':
        f  = g
        g1 = 0
        g2 = 1

      elif self.mode == 'b':
        f  = b
        b1 = 0
        b2 = 1

      grad.add_color_stop_rgb(0.0, r1,g1,b1)
      grad.add_color_stop_rgb(1.0, r2,g2,b2)

    elif self.mode in "hsv":
      col = Color()
      h,s,v = self.color.hsv()
      if h == 360: h = 0

      if self.mode == 'h':
        # this one is special...
        f = h/360.

        col.set_hsv(0,s,v)
        max,min,tmp = [c/255. for c in col.rgb()]

        grad.add_color_stop_rgb(0.0,  max, min, min)
        grad.add_color_stop_rgb(1/6., max, max, min)
        grad.add_color_stop_rgb(2/6., min, max, min)
        grad.add_color_stop_rgb(3/6., min, max, max)
        grad.add_color_stop_rgb(4/6., min, min, max)
        grad.add_color_stop_rgb(5/6., max, min, max)
        grad.add_color_stop_rgb(1.0,  max, min, min)
        pass
      elif self.mode == 's':
        f = s
        col.set_hsv(h,0,v)
        r1,g1,b1 = [c/255. for c in col.rgb()]
        col.set_hsv(h,1.0,v)
        r2,g2,b2 = [c/255. for c in col.rgb()]
        grad.add_color_stop_rgb(0.0, r1,g1,b1)
        grad.add_color_stop_rgb(1.0, r2,g2,b2)
      elif self.mode == 'v':
        f = v
        col.set_hsv(h,s,0)
        r1,g1,b1 = [c/255. for c in col.rgb()]
        col.set_hsv(h,s,1)
        r2,g2,b2 = [c/255. for c in col.rgb()]
        grad.add_color_stop_rgb(0.0, r1,g1,b1)
        grad.add_color_stop_rgb(1.0, r2,g2,b2)

    elif self.mode in "cmyk":
      col1 = Color()
      col2 = Color()
      c,m,y,k = self.color.cmyk()
      if self.mode == 'c':
        f = c/100.
        col1.set_cmyk(0,m,y,k)
        col2.set_cmyk(100,m,y,k)
      elif self.mode == 'm':
        f = m/100.
        col1.set_cmyk(c,0,y,k)
        col2.set_cmyk(c,100,y,k)
      elif self.mode == 'y':
        f = y/100.
        col1.set_cmyk(c,m,0,k)
        col2.set_cmyk(c,m,100,k)
      elif self.mode == 'k':
        f = k/100.
        col1.set_cmyk(c,m,y,0)
        col2.set_cmyk(c,m,y,100)
      r1,g1,b1 = [c/255. for c in col1.rgb()]
      r2,g2,b2 = [c/255. for c in col2.rgb()]
      grad.add_color_stop_rgb(0.0, r1,g1,b1)
      grad.add_color_stop_rgb(1.0, r2,g2,b2)

    # paint gradient
    cr.set_source(grad)
    cr.rectangle(gx,gy,gw,gh)
    cr.fill()

    # paint marker line
    cr.set_source_rgb(1,1,1)
    cr.move_to(gx+gw*f, gy)
    cr.line_to(gx+gw*f, gy+gh)
    cr.stroke()

    # paint frame
    x,y,w,h = self.pad,self.pad,self.allocation.width-2*self.pad,self.allocation.height-2*self.pad
    self.style.paint_shadow(self.window, gtk.STATE_NORMAL, gtk.SHADOW_IN, event.area, self, "trough-lower", x,y,w,h)

  def cb_button_press(self, widget, event):
    """ Callback for mouse button press events """
    if event.button == 1:
      self.selecting = True
      self.set_value(event)

  def cb_button_release(self, widget, event):
    """ Callback for mouse button release events """
    if event.button == 1:
      self.set_value(event)
      self.selecting = False

  def cb_motion_notify(self, widget, event):
    """ Callback for mouse motion notify events """
    if self.selecting:
      self.set_value(event)

  def gradient_geometry(self):
    return (self.pad+self.cpad, self.pad+self.cpad,
            self.allocation.width - 2*self.pad - 2*self.cpad,
            self.allocation.height - 2*self.pad - 2*self.cpad)

  def set_value(self, event):
    x,y,w,h = self.gradient_geometry()
    val = (event.x - x) / w
    if val < 0: val = 0
    if val > 1: val = 1

    if self.mode in "rgb":
      r,g,b = self.color.rgb()
      if self.mode == 'r':
        r = val * 255
      elif self.mode == 'g':
        g = val * 255
      elif self.mode == 'b':
        b = val * 255
      self.color.set_rgb(r,g,b)
    elif self.mode in "hsv":
      h,s,v = self.color.hsv()
      if self.mode == 'h':
        h = val * 360
      elif self.mode == 's':
        s = val
      elif self.mode == 'v':
        v = val
      self.color.set_hsv(h,s,v)
    elif self.mode in "cmyk":
      c,m,y,k = self.color.cmyk()
      if self.mode == 'c':
        c = val * 100
      elif self.mode == 'm':
        m = val * 100
      elif self.mode == 'y':
        y = val * 100
      elif self.mode == 'k':
        k = val * 100
      self.color.set_cmyk(c,m,y,k)


gobject.type_register(CSlider)      

if __name__ == "__main__":
  win = gtk.Window()
  win.connect('destroy', gtk.main_quit, None)

  color = Color()
  color.set_hex('#427288')

  hbox = gtk.HBox(False, 2)

  vbox = gtk.VBox(False, 2)
  cslider = CSlider(color, 'r')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'g')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'b')
  vbox.pack_start(cslider, False)

  hbox.pack_start(vbox, True)

  vbox = gtk.VBox(False, 2)
  cslider = CSlider(color, 'h')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 's')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'v')
  vbox.pack_start(cslider, False)

  hbox.pack_start(vbox, True)

  vbox = gtk.VBox(False, 2)
  cslider = CSlider(color, 'c')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'm')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'y')
  vbox.pack_start(cslider, False)
  cslider = CSlider(color, 'k')
  vbox.pack_start(cslider, False)

  hbox.pack_start(vbox, True)

  win.add(hbox)

  win.show_all()

  gtk.main()
