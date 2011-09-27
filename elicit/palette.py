import gobject
from color import Color
import os

class Palette(gobject.GObject):
  """
  A palette is a collection of colors

  Palettes are stored on disk in the GIMP palette format (.gpl).

  Parameters:
    colors: the list of colors
    name: the name of the palette
    columns: the number of columns to display (ignored, but saved in file)
    filename: the full path to the palette file
    load_errors: a list of errors encountered on load

  Signals:
    'changed' - emitted when a color is added or removed
  """
  __gsignals__ = {
    'changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

  PaletteDir = None

  def __init__(self):
    """Initialize an empty palette"""
    super(Palette, self).__init__()
    self.name = "Untitled Palette"
    self.columns = 0
    self.filename = None
    self.load_errors = []
    self.colors = []

  def append(self, color):
    """Ad a color to the end of the color list"""
    self.colors.append(color)
    self.emit('changed')

  def insert_before(self, color, before):
    """Insert a color before another color"""
    self.colors.insert(s.index(before), color)
    self.emit('changed')

  def insert_after(self, color, after):
    """Insert a color after another one"""
    self.colors.insert(s.index(after) + 1, color)
    self.emit('changed')

  def insert_at_index(self, color, index):
    """Insert a color at a specified location in the color list"""
    self.colors.insert(index, color)
    self.emit('changed')

  def prepend(self, color):
    """Add a color to the beginning of the color list"""
    self.colors[0:0] = color
    self.emit('changed')

  def remove(self, color):
    """Remove a color from the color list"""
    self.colors.remove(color)
    self.emit('changed')

  def load(self, filename):
    """
    Load the palette from a file

    The filename should be given as a the full path.
    """
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
            except: #XXX handle specific exceptions only
              self.load_errors.append("Invalid color entry on line {0}. Skipping.\n".format(lineno))
      self.emit('changed')
    except IOError:
        #if nonexistant filename is passed in, assume we want to save to that in the future
      pass
    return (len(self.load_errors) == 0)
     
  def save(self, filename = None):
    """
    Save a palette to disk

    If the filename specified is not a full path, the file is saved in the
    default palette dir.

    If the filename is not specified, a new file is formed from the palette
    name by converting spaces to dashes and lowercasing. If a file of this
    name already exists (in the default dir), a number is appended and
    incremented until a unique filename is found.

    self.filename is updated with the full path to the file.
    """
    if filename:
      if filename == os.path.basename(filename):
        filename = os.path.join(self.PaletteDir, filename)
      self.filename = filename

    rename_palette_file = False
    delete_palette_file = None
    if self.filename and os.path.basename(self.filename).startswith('untitled-palette') and self.name and self.name != 'Untitled Palette':
      delete_palette_file = self.filename
      rename_palette_file = True

    if self.filename == None or rename_palette_file:
      if self.PaletteDir:
        base = '-'.join(self.name.lower().split(' '))
        self.filename = os.path.join(self.PaletteDir, base + '.gpl')
        index = 0
        while os.path.exists(self.filename):
          index += 1
          self.filename = os.path.join(self.PaletteDir, '%s-%d.gpl'%(base,index))
        self.emit('changed')
      else:
        raise "No filename or default palette directory specified."

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

    if delete_palette_file and delete_palette_file != self.filename:
      # if we've gotten this far, then palette is successfully saved to new file, so delete old one.
      os.unlink(delete_palette_file)


  def delete(self):
    """Delete the palette file on disk"""
    if self.filename and os.path.exists(self.filename):
      os.unlink(self.filename)

gobject.type_register(Palette)
