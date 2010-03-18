import gtk
from color import Color
import struct

class ColorDndHelper:
  TARGET_TYPE_COLOR = 1
  TARGET_TYPE_TEXT  = 2

  drag_targets = [
      ("application/x-color", 0, TARGET_TYPE_COLOR),
      ("text/plain", 0, TARGET_TYPE_TEXT),
  ]

  def __init__(self, widget, cb_set_color):
    self.widget = widget
    self.cb_set_color = cb_set_color

    self.widget.drag_dest_set(0, self.drag_targets, gtk.gdk.ACTION_COPY)
    self.widget.connect('drag-motion', self.cb_drag_motion)
    self.widget.connect('drag-leave', self.cb_drag_leave)
    self.widget.connect('drag-drop', self.cb_drag_drop)
    self.widget.connect('drag-data-received', self.cb_drag_data_received)


  def cb_drag_motion(self, wid, context, x, y, time):
    for target in self.drag_targets:
      if target[0] in context.targets:
        print "Found target: %s" % target[0]
        context.drag_status(gtk.gdk.ACTION_COPY, time)
        self.widget.drag_highlight()
        return True

  def cb_drag_drop(self, wid, context, x, y, time):
    for target in self.drag_targets:
      if target[0] in context.targets:
        self.widget.drag_get_data(context, target[0], time)

  def cb_drag_leave(self, wid, context, time):
    self.widget.drag_unhighlight()

  def cb_drag_data_received(self, widget, context, x, y, selection, target_type, time):
    success = False
    valid = False
    color = Color()

    try:
      if target_type == self.TARGET_TYPE_COLOR:
        col = struct.unpack("HHHH", selection.data)
        print col
        color.set_rgb16(*col[0:3])
        valid = True
      elif target_type == self.TARGET_TYPE_TEXT:
        color.set_hex(selection.data)
        valid = True
        print("The text dropped does not represent a color")
    except ValueError, struct.error:
      print("Invalid data dropped")


    if valid:
      success = self.cb_set_color(color)

    context.finish(success, False, time)

    print("Success: {0}".format(success))
    return success

  
