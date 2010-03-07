from color import Color

class Palette:
  def __init__(self):
    self.name = "Untitled Palette"
    self.columns = 0
    self.filename = None
    self.load_errors = []
    self.colors = []

  def append(self, color):
    self.colors.append(color)

  def insert_before(self, color, after):
    self.colors.insert(s.index(after), color)

  def insert_after(self, color, after):
    self.colors.insert(s.index(after) + 1, color)

  def prepend(self, color):
    self.colors[0:0] = color

  def load(self, filename):
    with open(filename) as f:
      self.filename = filename
      self.colors = []
      self.load_errors = []

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
    return (len(self.load_errors) == 0)
     
  def save(self, filename):
    with open(filename, 'w'):
      write("GIMP Palette\n")
      write("Name: %s" % self.name)
      write("Columns: %d" % self.columns)
      for c in self.colors:
        write("% 3d % 3d % 3d\t%s" % (c.r, c.g, c.b, c.name))

