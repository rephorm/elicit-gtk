import gobject
import gtk
from gtk import gdk

from palette import Palette

class PaletteView(gtk.Widget):
  def __init__(self):
    super(PaletteView, self).__init__()

    self.palette = None
    self.direction = gtk.DIR_RIGHT
    self.padding = 2

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

    if self.direction == gtk.DIR_RIGHT or self.direction == gtk.DIR_LEFT:
      size = self.allocation.height - 2 * self.padding
      hor = True
    elif self.direction == gtk.DIR_UP or self.direction == gtk.DIR_DOWN:
      size = self.allocation.width - 2 * self.padding
      hor = False
    else:
      return

    rect = gdk.Rectangle(self.padding, self.padding, size, size)

    for color in self.palette.colors:
      col = self.gc.get_colormap().alloc_color(color.r * 257, color.g * 257, color.b * 257)
      self.gc.set_foreground(col)

      r = rect.intersect(event.area)
      self.window.draw_rectangle(self.gc, True, *r)

      if hor: rect.x += rect.width + 2 * self.padding
      else: rect.y += rect.height + 2 * self.padding

gobject.type_register(PaletteView)      
