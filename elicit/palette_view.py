import gobject
import gtk
from gtk import gdk
import glib

from palette import Palette
from color import Color

from color_dnd_helper import ColorDndHelper

class PaletteView(gtk.Widget):
  """
  A widget to display a palette

  The palette is displayed as either a horizontal or vertical list of
  swatches.

  Signals:
    'select-color' - a color has been selected.
    'delete-color' - a color should be deleted.

  Both of these signal handlers are passed the color as an additional
  parameter.
  """
  HORIZONTAL = 1
  VERTICAL = 2

  __gsignals__ = {
      'select-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
      'delete-color': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
      }

  def __init__(self):
    """Initialize empty palette view"""
    super(PaletteView, self).__init__()

    self.palette = None
    self.direction = self.HORIZONTAL
    self.padding = 3
    self.colors = {}

    self.pan = 0

    self.selected = None

    self.panning = False

    self.drag_color = None
    self.drag_start = None
    self.drag_loc = None
    self.drag_is_move = False
    self.drag_removed = False

    self.color_to_delete = None

  def select(self, color):
    """
    Select a color

    Sets the currently selected color and pans so that the swatch is
    entirely within view.
    """

    self.selected = color

    if color: self.pan_to_color(color)

    self.queue_draw()
    self.emit('select-color', color)

  def set_pan(self, pan):
    """
    Set the pan

    The pan is specified in pixels. A positive value moves the swatches
    left or up depending on the direction.
    """

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
    """
    Pan so that the swatch corresponding to color is in view
    """
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

  def color_location(self, color):
    """
    Find the top left corner of a color swatch relative to the widget

    The value is returned as a tuple (x,y)
    """
    i = self.palette.colors.index(color)

    if self.direction == self.HORIZONTAL:
      x = self.allocation.height * i + self.padding
      y = self.padding
    else:
      x = self.padding
      y = self.allocation.width * i + self.padding

    return (x,y)


  def color_at(self, x, y):
    """
    Find the color swatch displayed at a given coordinate

    If a swatch is displayed at this coordinate, the corresponding color is
    returned. Otherwise None is returned.
    """
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
    """Specify that the palette needs to be redrawn"""
    self.queue_draw()

  def set_palette(self, palette):
    """
    Set the palette to display
    """
    self.palette = palette
    self.palette.connect('changed', self.palette_changed)
    self.set_pan(self.pan)
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

    self.connect("drag-motion", self.cb_drag_motion)
    self.connect("drag-leave", self.cb_drag_leave)
    self.connect("drag-data-delete", self.cb_drag_data_delete)
    self.connect("drag-end", self.cb_drag_end)

    self.dnd_helper = ColorDndHelper(self, self.cb_drag_add_color, self.cb_drag_get_color)
    self.drag_source_unset() #we will manually start drags

    self.set_tooltip_text("Click and drag:\n  Left: DnD color\n  Middle: pan\n\nScroll: pan\nRight click: Remove color")

  def do_unrealize(self):
    """Unrealize the widget"""
    self.window.destroy()

  def do_size_request(self, requisition):
    """Set the default size"""
    requisition.height = 25
    requisition.width = 25

  def do_size_allocation(self, allocation):
    """Handle size changes"""
    if self.flags() & gtk.REALIZED:
      self.window.move_resize(*allocation)

  def do_expose_event(self, event):
    """
    Draw the widget

    Each swatch is centered in a square the size of the widget height for a
    horizontal palette or width for a vertical palette. The swatch is
    smaller than this size by twice the current padding.

    A simple shadow is drawn behind the swatch and the currently selected
    swatch is outlined.

    When dragging a color over the palette, an empty space is left to
    indicate where the new swatch would be added if dropped.
    """
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

    self.dnd_helper.set_swatch_size(size+4)

    for color in self.palette.colors:
      # skip color being dragged
      if self.drag_is_move and color == self.drag_color: continue

      # leave room for dragged color
      if (self.direction == self.HORIZONTAL and self.drag_loc and
          self.drag_loc[0] >= rect.x - self.padding and
          self.drag_loc[0] < rect.x + rect.width + self.padding):
        rect.x += rect.width + 2 * self.padding

      elif (self.direction == self.VERTICAL and self.drag_loc and
            self.drag_loc[1] >= rect.y - self.padding and
            self.drag_loc[1] < rect.y + rect.height + self.padding):
        rect.y += rect.height + 2 * self.padding

      self.draw_swatch(color, rect, event.area, self.selected == color)

      if self.direction == self.HORIZONTAL:
        rect.x += rect.width + 2 * self.padding
      else:
        rect.y += rect.height + 2 * self.padding

  def draw_swatch(self, color, rect, clip_rect, selected = False):
    """
    Draw a swatch in the specified rectangle
    """
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
    """ Callback for mouse button press events """
    #XXX this should be "whichever button dragging is hooked up to",
    #    rather than 1
    if event.button == 1:
      self.drag_color = self.color_at(event.x, event.y)
      if self.drag_color:
        self.drag_start = (event.x, event.y)
    elif event.button == 2:
      self.panning = True
      self.pan_start = (event.x, event.y)
      self.pan_start_pan = self.pan
    elif event.button == 3:
      self.color_to_delete = self.color_at(event.x, event.y)

  def cb_button_release(self, widget, event):
    """ Callback for mouse button release events """
    if event.button == 1:
      col = self.color_at(event.x, event.y)
      if col:
        self.select(col)
      self.drag_start = None
    elif event.button == 2:
      self.panning = False
    elif event.button == 3:
      col = self.color_at(event.x, event.y)
      if col and col == self.color_to_delete:
        if self.selected == col:
          self.select(None)

        self.emit('delete-color', col)
        self.set_pan(self.pan)
      self.color_to_delete = None

  def cb_motion_notify(self, widget, event):
    """ Callback for mouse motion notify events """
    if self.panning:
      if self.direction == self.HORIZONTAL:
        pan_frac = 2 * (event.x - self.pan_start[0])/ self.allocation.width
        pan = pan_frac * (len(self.palette.colors) * self.allocation.height - self.allocation.width)
      else:
        pan_frac = 2 * (event.y - self.pan_start[1]) / self.allocation.height
        pan = pan_frac * (len(self.palette.colors) * self.allocation.width - self.allocation.height)

      self.set_pan(self.pan_start_pan + pan)

    elif self.drag_start:
      if (max(abs(event.x - self.drag_start[0]), abs(event.y - self.drag_start[1])) > 5):
        loc = self.color_location(self.drag_color)
        #self.dnd_helper.set_hot_spot(self.drag_start[0] - loc[0], self.drag_start[1] - loc[1])
        self.drag_begin(self.dnd_helper.drag_targets, gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE, 1, event)

  def cb_scroll(self, widget, event):
    """ Callback for mouse wheel scroll events """
    if event.direction == gtk.gdk.SCROLL_DOWN or event.direction == gtk.gdk.SCROLL_RIGHT:
      self.set_pan(self.pan + 10)
    if event.direction == gtk.gdk.SCROLL_UP or event.direction == gtk.gdk.SCROLL_LEFT:
      self.set_pan(self.pan - 10)

  def cb_drag_add_color(self, color, x, y):
    """ Callback to handle a color dropped on the palette view """
    if self.direction == self.HORIZONTAL:
      size = int(self.allocation.height)
      i = int(x + self.pan) / size
    else:
      size = int(self.allocation.width)
      i = int(y + self.pan ) / size

    if self.drag_color:
      # we're moving the color w/in the palette
      color = self.drag_color
      self.palette.remove(self.drag_color)
      self.drag_removed = True

    if i < 0:
      self.palette.prepend(color)
    elif i >= len(self.palette.colors):
      self.palette.append(color)
    else:
      self.palette.insert_at_index(color, i)
    return True

  def cb_drag_get_color(self):
    """ Callback to return the color being dragged """
    return self.drag_color

  def cb_drag_motion(self, wid, context, x, y, time):
    """ Callback for mouse motion over widget while dragging """
    self.drag_loc = (x,y)

    if context.get_source_widget() == self:
      self.drag_is_move = True

    return False

  def cb_drag_leave(self, wid, context, time):
    """ Callback for mouse leaving widget while dragging """
    self.drag_loc = None
    self.drag_is_move = False

  def cb_drag_data_delete(self, widget, context):
    """ Callback for drag delete events (when moving a color via dnd) """
    if not self.drag_removed:
      self.palette.remove(self.drag_color)

  def cb_drag_end(self, widget, context):
    """ Callback for a drag ending """
    self.drag_color = None
    self.drag_removed = False

gobject.type_register(PaletteView)      
