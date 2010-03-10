import gobject
import gtk
from gtk import gdk

from palette import Palette
from color import Color

#XXX BUGS: deleting color should update pan value if needed
#    TODO: allow drag reordering of colors
#          dnd of colors to other applications?

class PaletteView(gtk.Widget):
  HORIZONTAL = 1
  VERTICAL = 2

  __gsignals__ = {
      'select-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
      'delete-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
      }

  def __init__(self):
    super(PaletteView, self).__init__()

    self.palette = None
    self.direction = self.HORIZONTAL
    self.padding = 3

    self.pan = 0

    self.selected = None

  def select(self, color):
    self.selected = color
    self.pan_to_color(color)
    self.queue_draw()
    self.emit('select-color', color)

  def set_pan(self, pan):
    if pan < 0: pan = 0

    if self.direction == self.HORIZONTAL:
      pan_max = len(self.palette.colors) * self.allocation.height - self.allocation.width
    else:
      pan_max = len(self.palette.colors) * self.allocation.width - self.allocation.height

    if pan_max < 0: pan_max = 0
    if pan > pan_max: pan = pan_max

    if pan != self.pan:
      self.pan = pan
      self.queue_draw()

  def pan_to_color(self, color):
    i = self.palette.colors.index(color)

    if self.direction == self.HORIZONTAL:
      pan = self.allocation.height * i
      if pan < self.pan or pan > self.pan + self.allocation.width - self.allocation.height:
        self.set_pan(pan)
    else:
      if pan < self.pan or pan > self.pan + self.allocation.height - self.allocation.width:
        self.set_pan(pan)
      pan = self.allocation.width * i


  def color_at(self, x, y):
    if self.direction == self.HORIZONTAL:
      if y < self.padding or y > self.allocation.height - self.padding:
        return None
      size = int(self.allocation.height)
      i = int(x + self.pan) / size
      off = int(x + self.pan) % size
      if off < self.padding or off > size - self.padding:
        return None

    else:
      if x < self.padding or x > self.allocation.width - self.padding:
        return None
      size = int(self.allocation.width)
      i = int(y + self.pan) / size
      off = int(y + self.pan) % size
      if off < self.padding or off > size - self.padding:
        return None

    if i >= 0 and i < len(self.palette.colors):
      return self.palette.colors[i]

    return None

  def palette_changed(self, palette):
    self.queue_draw()

  def set_palette(self, palette):
    self.palette = palette
    self.palette.connect('changed', self.palette_changed)

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

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("scroll-event", self.cb_scroll)

  def do_unrealize(self):
    self.window.destroy()

  def do_size_request(self, requisition):
    requisition.height = 25
    requisition.width = 25

  def do_size_allocation(self, allocation):
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    if not self.palette:
      return

    white_col = self.gc.get_colormap().alloc_color(255*257,255*257,255*257)
    self.gc.set_foreground(white_col)
    rect = gdk.Rectangle(0, 0, self.allocation.width, self.allocation.height)
    self.window.draw_rectangle(self.gc, True, *rect.intersect(event.area))

    if self.direction == self.HORIZONTAL:
      size = self.allocation.height - 2 * self.padding
      x = self.padding - self.pan
      y = self.padding
    else:
      size = self.allocation.width - 2 * self.padding
      x = self.padding
      y = self.padding - self.pan

    rect = gdk.Rectangle(x, y, size, size)

    shadow_col = self.gc.get_colormap().alloc_color(214*257,214*257,214*257)
    black_col = self.gc.get_colormap().alloc_color(0,0,0)
    for color in self.palette.colors:
      fg_col = self.gc.get_colormap().alloc_color(color.r * 257, color.g * 257, color.b * 257)

      r = rect.intersect(event.area)

      #draw shadow
      self.gc.set_foreground(shadow_col)
      self.window.draw_rectangle(self.gc, True, r.x+1, r.y+1, r.width, r.height)
      #draw swatch
      self.gc.set_foreground(fg_col)
      self.window.draw_rectangle(self.gc, True, *r)

      if self.selected == color:
        self.gc.set_foreground(black_col)
        self.window.draw_rectangle(self.gc, False, r.x,r.y,r.width-1,r.height-1)

      if self.direction == self.HORIZONTAL: rect.x += rect.width + 2 * self.padding
      else: rect.y += rect.height + 2 * self.padding

  def cb_button_press(self, widget, event):
    if event.button == 1:
      pass
    elif event.button == 2:
      pass
    elif event.button == 3:
      pass
    pass

  def cb_button_release(self, widget, event):
    if event.button == 1:
      col = self.color_at(event.x, event.y)
      if col:
        self.select(col)
    elif event.button == 2:
      pass
    elif event.button == 3:
      col = self.color_at(event.x, event.y)
      if col:
        if self.selected == col:
          self.select(None)

        self.emit('delete-color', col)

  def cb_motion_notify(self, widget, event):
    pass

  def cb_scroll(self, widget, event):
    if event.direction == gtk.gdk.SCROLL_DOWN or event.direction == gtk.gdk.SCROLL_RIGHT:
      self.set_pan(self.pan + 5)
    if event.direction == gtk.gdk.SCROLL_UP or event.direction == gtk.gdk.SCROLL_LEFT:
      self.set_pan(self.pan - 5)

gobject.type_register(PaletteView)      
