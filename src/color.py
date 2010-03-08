import gobject

class Color(gobject.GObject):
  __gsignals__ = {
      'changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
      }

  UNSET = 0
  RGB = 1
  HSV = 2

  def __init__(self):
    super(Color,self).__init__()
    self.type = self.UNSET
    self.name = "Unnamed"
    self.r = self.g = self.b = 0
    self.h = self.s = self.v = 0
    pass

  def __string__(self):
    return self.hex()

  def set_rgb(self, r, g, b):
    if (min(r,g,b) < 0 or max(r,g,b) > 255):
      raise ValueError("Values must be between 0 and 255")

    if self.r == r and self.g == g and self.b == b: return

    self.r, self.g, self.b = r, g, b
    self.type = Color.RGB
    self.rgb_to_hsv()
    self.emit('changed')

  def set_hsv(self, h, s, v):
    if (min(r,g,b) < 0 or max(r,g,b) > 255):
      raise ValueError("Values must be between 0 and 255")

    if self.h == h and self.s == s and self.v == v: return

    self.h, self.s, self.v = h, s, v
    self.type = Color.HSV
    self.hsv_to_rgb()
    self.emit('changed')

  def set_hex(self, hex):
    tmp = hex
    if tmp[0] == '#': tmp = tmp[1:]
    if len(tmp) != 6: raise ValueError("Invalid Hex format")
    r = int(tmp[0:2],16)
    g = int(tmp[2:4],16)
    b = int(tmp[4:6],16)

    self.set_rgb(r,g,b)

  def rgb(self):
    return (self.r, self.g, self.b)

  def rgb16(self):
    return (self.r * 257, self.g * 257, self.b * 257)

  def hsv(self):
    return (self.h, self.s, self.v)

  def hex(self, uppercase=False, hash=True):
    if uppercase:
      format = "%02X%02X%02X"
    else:
      format = "%02x%02x%02x"
    if hash: format = "#" + format

    return format % (self.r, self.g, self.b)

  def rgb_to_hsv(self):
    col = (self.r, self.g, self.b)
    maxc = 0
    minc = 0

    if col[1] > col[maxc]: maxc = 1
    if col[2] > col[maxc]: maxc = 2
    if col[1] < col[minc]: minc = 1
    if col[2] < col[minc]: minc = 2

    # black is easy
    if col[maxc] == 0:
      self.h = self.s = self.v = 0
      return

    self.v = col[maxc] / 255
    self.s = (1.0 - float(col[minc])/col[maxc])
    self.h = 60 * ( (maxc * 2) +
        (col[(maxc + 1)%3] - col[(maxc+2)%3]) / (col[maxc] - col[minc]) )
    if (self.h < 360): self.h += 360
   
  def hsv_to_rgb(self):
    if (self.s == 0):
      self.r = self.g = self.b = self.v
      return

    h = self.h / 60
    i = int(h)
    f = h - i
    p = v * (1 - self.s)
    q = v * (1 - self.s * f)
    t = v * (1 - self.s * (1 - f))

    if i == 0:
      self.r, self.g, self.b = v, t, p
    elif i == 1:
      self.r, self.g, self.b = q, v, p
    elif i == 2:
      self.r, self.g, self.b = p, v, t
    elif i == 3:
      self.r, self.g, self.b = p, q, v
    elif i == 4:
      self.r, self.g, self.b = t, p, v
    elif i == 5:
      self.r, self.g, self.b = v, p, q

gobject.type_register(Color)
