import gtk
import gobject
import os
import glob
from palette import Palette


class PaletteList(gtk.ListStore):
  def __init__(self):
    super(PaletteList,self).__init__(gobject.TYPE_STRING, gobject.TYPE_STRING, Palette)

  def load(self, dir):
    for f in glob.glob(os.path.join(dir,'*.gpl')):
      self.append_path(f)

  def append(self, palette):
    super(PaletteList,self).append((palette.name, palette.filename, palette))

  def append_path(self, path):
    p = Palette()
    if p.load(path):
      self.append(p)

  def set_text(self, index, text):
    row = self[index]
    row[0] = row[2].name = text

  def index_of_palette(self, palette):
    index = 0
    for row in self:
      if row[2] == palette:
        return index
      index += 1

  def index_of_file(self, file):
    index = 0
    for row in self:
      if os.path.basename(row[1]) == os.path.basename(file):
        return index
      index += 1

class PaletteCombo(gtk.ComboBoxEntry):
  __gsignals__ = {
    'selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (Palette,))
    }
  def __init__(self):
    super(PaletteCombo,self).__init__()

    self.set_text_column(0)
    self.active = -1

    self.connect('changed', self.changed)

  def select(self, index):
    self.set_active(index)
    if self.active != index:
      self.active = index
      self.emit('selected', self.get_model()[index][2])

  def changed(self,combo):
    index = self.get_active()
    if index == -1:
      row = self.get_model()[self.active]
      self.get_model().set_text(self.active, combo.child.get_text())
      self.select(self.active)
    else:
      self.select(index)

