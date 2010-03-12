import gobject
from color import Color
import os

class Palette(gobject.GObject):
  __gsignals__ = {
    'changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }
  def __init__(self):
    super(Palette, self).__init__()
    self.name = "Untitled Palette"
    self.columns = 0
    self.filename = None
    self.load_errors = []
    self.colors = []

  def append(self, color):
    self.colors.append(color)
    self.emit('changed')

  def insert_before(self, color, after):
    self.colors.insert(s.index(after), color)
    self.emit('changed')

  def insert_after(self, color, after):
    self.colors.insert(s.index(after) + 1, color)
    self.emit('changed')

  def prepend(self, color):
    self.colors[0:0] = color
    self.emit('changed')

  def remove(self, color):
    self.colors.remove(color)
    self.emit('changed')

  def load(self, filename):
    self.colors = []
    self.load_errors = []
    self.filename = filename

    try:
      with open(filename) as f:
        # Check that file is a palette file
        if f.readline().strip() != 'GIMP Palette':
          self.load_errors.append("Invalid file format.".format(filename))
          return False

        lineno = 0
        for line in f:
          lineno += 1
          if line[0] == '#': continue
          elif line[0:5] == 'Name:':
            self.name = line[5:].strip()
          elif line[0:8] == 'Columns:':
            try:
              self.columns = int(line[8:].strip())
            except ValueError:
              self.load_errors.append("Columns value (line {0}) must be integer. Using default value.".format(lineno))
              self.columns = 0
          else:
            try:
              r = int(line[0:3])
              g = int(line[4:7])
              b = int(line[8:11])
              cname = line[12:].strip()

              c = Color()
              c.name = cname
              c.set_rgb(r,g,b)
              self.colors.append(c)
            except:
              self.load_errors.append("Invalid color entry on line {0}. Skipping.\n".format(lineno))
      self.emit('changed')
    except IOError:
        #if nonexistant filename is passed in, assume we want to save to that in the future
      pass
    return (len(self.load_errors) == 0)
     
  def save(self, filename = None):
    if filename:
      self.filename = filename
    if self.filename == None:
      raise "No filename specified."

    dir = os.path.dirname(self.filename)
    if not os.path.exists(dir):
      os.makedirs(dir)

    with open(self.filename, 'w') as f:
      f.write("GIMP Palette\n")
      f.write("Name: %s\n" % self.name)
      f.write("Columns: %d\n" % self.columns)
      f.write("#\n")
      for c in self.colors:
        f.write("%3d %3d %3d\t%s\n" % (c.r, c.g, c.b, c.name))

gobject.type_register(Palette)
