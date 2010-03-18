import gobject
import gtk
from gtk import gdk
import glib

from palette import Palette
from color import Color

from color_dnd_helper import ColorDndHelper

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
    self.colors = {}

    self.pan = 0

    self.selected = None

    self.panning = False
    self.dragging = False

    self.drag_start = None
    self.drag_color = None
    self.drag_loc = None

  def select(self, color):
    self.selected = color

    if color: self.pan_to_color(color)

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
      if pan < self.pan:
        self.set_pan(pan)
      elif  pan > self.pan + self.allocation.width - self.allocation.height:
        self.set_pan(pan - self.allocation.width + self.allocation.height)
    else:
      if pan < self.pan or pan > self.pan + self.allocation.height - self.allocation.width:
        self.set_pan(pan)


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
    self.set_pan(self.pan)
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

    self.window.set_user_data(self)
    self.style.attach(self.window)
    self.style.set_background(self.window, gtk.STATE_NORMAL)
    self.window.move_resize(*self.allocation)

    self.gc = self.window.new_gc()

    self.gc_shadow = self.window.new_gc()
    col = self.gc_shadow.get_colormap().alloc_color(214*257,214*257,214*257)
    self.gc_shadow.set_foreground(col)

    self.gc_border = self.window.new_gc()
    col = self.gc_border.get_colormap().alloc_color(0,0,0)
    self.gc_border.set_foreground(col)

    self.connect("motion-notify-event", self.cb_motion_notify)
    self.connect("button-press-event", self.cb_button_press)
    self.connect("button-release-event", self.cb_button_release)
    self.connect("scroll-event", self.cb_scroll)

    self.dnd_helper = ColorDndHelper(self, self.cb_drag_add_color)

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
      x = self.padding - int(self.pan)
      y = self.padding
    else:
      size = self.allocation.width - 2 * self.padding
      x = self.padding
      y = self.padding - int(self.pan)

    rect = gdk.Rectangle(x, y, size, size)

    for color in self.palette.colors:
      #skip color being dragged
      if color == self.drag_color: continue

      # leave room for dragged color
      if (self.direction == self.HORIZONTAL and self.dragging and
          self.drag_loc[0] >= rect.x - self.padding and
          self.drag_loc[0] < rect.x + rect.width + self.padding):
        rect.x += rect.width + 2 * self.padding

      elif (self.direction == self.VERTICAL and self.dragging and
            self.drag_loc[1] >= rect.y - self.padding and
            self.drag_loc[1] < rect.y + rect.height + self.padding):
        rect.y += rect.height + 2 * self.padding

      self.draw_swatch(color, rect, event.area, self.selected == color)

      if self.direction == self.HORIZONTAL:
        rect.x += rect.width + 2 * self.padding
      else:
        rect.y += rect.height + 2 * self.padding

    if self.dragging:
      rect.x = self.drag_loc[0] - rect.width / 2
      rect.y = self.drag_loc[1] - rect.height / 2
      self.draw_swatch(self.drag_color, rect, event.area, self.drag_color == self.selected)

  def draw_swatch(self, color, rect, clip_rect, selected = False):
    fg_col = self.gc.get_colormap().alloc_color(*color.rgb16())

    r = rect.intersect(clip_rect)

    # if interesection vanishes, don't draw anything
    if r.width > 0 and r.height > 0:
      #draw shadow
      self.window.draw_rectangle(self.gc_shadow, True, r.x+1, r.y+1, r.width, r.height)
      #draw swatch
      self.gc.set_foreground(fg_col)
      self.window.draw_rectangle(self.gc, True, *r)

      if selected:
        self.window.draw_rectangle(self.gc_border, False, rect.x,rect.y,rect.width-1,rect.height-1)

  def cb_button_press(self, widget, event):
    if event.button == 1:
      self.drag_start = (event.x, event.y)
      pass
    elif event.button == 2:
      self.panning = True
      self.pan_start = (event.x, event.y)
      self.pan_start_pan = self.pan
      pass
    elif event.button == 3:
      pass
    pass

  def cb_button_release(self, widget, event):
    if event.button == 1:
      self.drag_start = None
      if self.dragging:
        self.drag_stop()
      else:
        col = self.color_at(event.x, event.y)
        if col:
          self.select(col)
    elif event.button == 2:
      self.panning = False
    elif event.button == 3:
      col = self.color_at(event.x, event.y)
      if col:
        if self.selected == col:
          self.select(None)

        self.emit('delete-color', col)
        self.set_pan(self.pan)

  def cb_motion_notify(self, widget, event):
    if self.panning:
      if self.direction == self.HORIZONTAL:
        pan_frac = 2 * (event.x - self.pan_start[0])/ self.allocation.width
        pan = pan_frac * (len(self.palette.colors) * self.allocation.height - self.allocation.width)
      else:
        pan_frac = 2 * (event.y - self.pan_start[1]) / self.allocation.height
        pan = pan_frac * (len(self.palette.colors) * self.allocation.width - self.allocation.height)

      self.set_pan(self.pan_start_pan + pan)

    elif self.dragging:
      loc = (event.x, event.y)
      if self.drag_loc != loc:
        self.drag_loc = loc
        self.queue_draw()
      else:
        pass
    elif self.drag_start:
      diff = max(abs(event.x - self.drag_start[0]), abs(event.y - self.drag_start[1]))
      if diff > 5:
        self.drag_color = self.color_at(*self.drag_start)
        self.dragging = True

  def drag_stop(self):
    self.palette.remove(self.drag_color)

    if self.direction == self.HORIZONTAL:
      size = int(self.allocation.height)
      i = int(self.drag_loc[0] + self.pan) / size
    else:
      size = int(self.allocation.width)
      i = int(self.drag_loc[1] + self.pan ) / size

    if i < 0:
      self.palette.prepend(self.drag_color)
    elif i >= len(self.palette.colors):
      self.palette.append(self.drag_color)
    else:
      self.palette.insert_at_index(self.drag_color, i)
    
    self.dragging = False
    self.drag_color = None
    self.drag_start = None
    self.drag_loc = None

    self.queue_draw()


  def cb_scroll(self, widget, event):
    if event.direction == gtk.gdk.SCROLL_DOWN or event.direction == gtk.gdk.SCROLL_RIGHT:
      self.set_pan(self.pan + 10)
    if event.direction == gtk.gdk.SCROLL_UP or event.direction == gtk.gdk.SCROLL_LEFT:
      self.set_pan(self.pan - 10)

  def cb_drag_add_color(self, color):
    self.palette.append(color)
    return True

gobject.type_register(PaletteView)      
