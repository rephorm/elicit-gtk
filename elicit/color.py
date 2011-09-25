import gobject

"""
  Utility functions for converting between different colorspaces (RGB, HSV, CMYK).

  The Color class handles representing a single, optionally named, color value with cached access to values in all color spaces.

  A note about RGB values

  8 bit colors take on values x in [0,255)
  16 bit colors take on values X in [0,65535]

  So, a given 8 bit value x represents the entire 16 bit range [x*256, (x+1)*256]

  Converting from 16->8 bit is straightforward. Just, divide by 256. However, converting the other direction is ambiguous. Which of the 256 possible 16 bit values should be assigned?  It is desirable to have the lowest values map to eachother, as well as the highest values. i.e. 0 <-> 0 and 255 <-> 65535. To obtain this, we multiply the 8 bit value by 257.

  This gives X = x*257 = (x*256) + x.

  Note that the middle value (127) gets mapped to the center of its 16 bit block.

  Converting 16 -> 8 -> 16 causes a downward shift for low values and an upward shift for high values.
"""


def rgb_to_hsv(r, g, b):
  """
  Convert form RGB to HSV

  Returns:
    (h,s,v)
  """

  col = (r, g, b)
  maxc = 0
  minc = 0

  if col[1] > col[maxc]: maxc = 1
  if col[2] > col[maxc]: maxc = 2
  if col[1] < col[minc]: minc = 1
  if col[2] < col[minc]: minc = 2

  # black is easy
  if col[maxc] == 0:
    return (0,0,0)

  v = col[maxc] / 255.0
  s = (1.0 - float(col[minc])/col[maxc])

  if col[maxc] == col[minc]:
    h = 0
  else:
    h = 60 * ( (maxc * 2) +
        (float(col[(maxc + 1)%3] - col[(maxc+2)%3])) / (col[maxc] - col[minc]) )
  if (h < 0): h += 360

  return (h,s,v)

def hsv_to_rgb(h,s,v):
  """
  Convert form HSV to RGB

  Returns:
    (r,g,b)
  """
  if (s == 0):
    r = g = b = int(255*v)
    return (r,g,b)

  h = h / 60.0
  v = int(255 * v)
  i = int(h)
  f = h - i
  p = int(v * (1 - s))
  q = int(v * (1 - s * f))
  t = int(v * (1 - s * (1 - f)))

  if i == 0:
    r, g, b = v, t, p
  elif i == 1:
    r, g, b = q, v, p
  elif i == 2:
    r, g, b = p, v, t
  elif i == 3:
    r, g, b = p, q, v
  elif i == 4:
    r, g, b = t, p, v
  elif i == 5:
    r, g, b = v, p, q
  else: # i == 6, same as i == 0
    r, g, b = v, t, p

  return (r,g,b)


def rgb_to_cmyk(r,g,b):
  r = r / 255.
  g = g / 255.
  b = b / 255.

  c = 1. - r
  m = 1. - g
  y = 1. - b
  k = min(c, m, y)

  if k < 1.:
    c = round((c - k) / (1. - k) * 100, 0)
    m = round((m - k) / (1. - k) * 100, 0)
    y = round((y - k) / (1. - k) * 100, 0)
    k = round(k * 100, 0)
  else:
    c = m = y = 0
    k = 100

  return (c,m,y,k)

def cmyk_to_rgb(c, m, y, k):
  c = c / 100.
  m = m / 100.
  y = y / 100.
  k = k / 100.

  c = min(1, c * (1 - k) + k)
  m = min(1, m * (1 - k) + k)
  y = min(1, y * (1 - k) + k)

  r = round((1. - c) * 255., 0)
  g = round((1. - m) * 255., 0)
  b = round((1. - y) * 255., 0)

  return (r,g,b)

def hex_to_rgb(hex):
  """
  Convert a hexidecimal string to RGB values

  The string may start with an optional hash "#", which is ignored.
  The remaining characters are RRGGBB, where RR is the hexidecimal red
  value between 00 and FF inclusive, and likewise for GG and BB.

  The hex values may be given as upper or lower case.
  """
  tmp = hex
  if tmp[0] == '#': tmp = tmp[1:]
  if len(tmp) != 6: raise ValueError("Invalid Hex format")
  r = int(tmp[0:2],16)
  g = int(tmp[2:4],16)
  b = int(tmp[4:6],16)

  return (r,g,b)

def rgb_to_hex(r, g, b, uppercase=False, hash=True):
  """
  Return the color value as a hexidecimal RGB string.

  Parameters:
    r, g, b:   red, green and bluee color values (0 to 255) 
    uppercase: boolean specifying whether hex letters should be uppercase
               or not
    hash:      boolean specifying whether preceding # should be included
  """
  if uppercase:
    format = "%02X%02X%02X"
  else:
    format = "%02x%02x%02x"
  if hash: format = "#" + format

  return format % (r, g, b)

class Color(gobject.GObject):
  """
  A color value

  Color values can be set using either RGB or HSV representations. Since
  conversion between the two formats is not lossless, the format in
  which the color was set is stored as its type parameter.

  A name can also be set on the color.

  This emits a 'changed' signal when the color is changed (changing the
  name does not currently emit this signal).
  The signal handler has a single parameter, the color object.
  """
  __gsignals__ = {
      'changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
      }

  UNSET, RGB, HSV, CMYK = range(4)

  def __init__(self):
    """
    Initialize a color

    The default value is black, with unspecified type
    """
    super(Color,self).__init__()
    self.type = self.UNSET
    self.name = "Unnamed"
    self.r = self.g = self.b = 0
    self.h = self.s = self.v = 0
    self.c = self.m = self.y = 0
    self.k = 100

  def __string__(self):
    """String representation as hex"""
    return self.hex()

  def set_rgb(self, r, g, b):
    """
    Set the color value using RGB values

    All values are given as integers between 0 and 255 inclusive.
    """
    if (min(r,g,b) < 0 or max(r,g,b) > 255):
      raise ValueError("Values must be between 0 and 255")

    r = int(r)
    g = int(g)
    b = int(b)

    if self.r == r and self.g == g and self.b == b: return
    self.r, self.g, self.b = r, g, b
    self.type = Color.RGB
    self.rgb_to_hsv()
    self.rgb_to_cmyk()
    self.emit('changed')

  def set_rgb16(self, r, g, b):
    """
    Set the color value using 16 bit RGB values

    All values are given as integers between 0 and 65535 inclusive.
    This is currently just converted to 8 bit RGB, losing the additional
    information.
    """
    self.set_rgb(r/256, g/256, b/256)

  def set_hsv(self, h, s, v):
    """
    Set the color value in HSV format

    The hue, h, is an integer between 0 and 360 inclusive.
    The saturation, s, and value, v, are floats between 0 and 1
    inclusive.
    """

    if min(h,s,v) < 0 or max(s,v) > 1 or h > 360:
      raise ValueError("Hue must be between 0 and 360. Sat. and Val. must be between 0 and 1")

    if self.h == h and self.s == s and self.v == v: return

    self.h, self.s, self.v = h, s, v
    self.type = Color.HSV
    self.hsv_to_rgb()
    self.rgb_to_cmyk()
    self.emit('changed')

  def set_cmyk(self, c, m, y, k):
    """
    Set the color value in CMYK format

    All values are between 0 and 100 inclusive
    """

    if min(c, m, y, k) < 0 or max (c, m, y, k) > 100:
      raise ValueError("CMYK values must be between 0 and 100")

    if self.c == c and self.m == m and self.y == y and self.k == k: return

    self.c = c
    self.m = m
    self.y = y
    self.k = k

    self.type = Color.CMYK
    self.cmyk_to_rgb()
    self.rgb_to_hsv()
    self.emit('changed')

  def set_hex(self, hex):
    """
    Set the color value using a hexidecimal string

    See hex_to_rgb for details.
    """
    self.set_rgb(*hex_to_rgb(hex))

  def rgb(self):
    """Return the color as a triple of 8 bit integers, (r,g,b)"""
    return (self.r, self.g, self.b)

  def rgb16(self):
    """Return the color as a triple of 16 bit integers, (r,g,b)"""
    return (self.r * 257, self.g * 257, self.b * 257)

  def hsv(self):
    """Return the color as a triple, (h,s,v)"""
    return (self.h, self.s, self.v)

  def cmyk(self):
    return (self.c, self.m, self.y, self.k)

  def hex(self, uppercase=False, hash=True):
    """
    Return the color value as a hexidecimal RGB string.

    Named parameters:
      uppercase: boolean specifying whether hex letters should be uppercase
                 or not
      hash:      boolean specifying whether preceding # should be included
    """
    return rgb_to_hex(*self.rgb(), uppercase=uppercase, hash=hash)

  def rgb_to_hsv(self):
    """ Update the internal HSV values from the current RGB values."""
    self.h, self.s, self.v = rgb_to_hsv(self.r, self.g, self.b)
   
  def hsv_to_rgb(self):
    """Update the internal RGB values from the current HSV values"""
    self.r, self.g, self.b = hsv_to_rgb(self.h, self.s, self.v)

  def rgb_to_cmyk(self):
    """ Update the internal CMYK values from the current RGB values."""
    self.c, self.m, self.y, self.k = rgb_to_cmyk(self.r, self.g, self.b)

  def cmyk_to_rgb(self):
    """Update the internal RGB values from the current CMYK values"""
    self.r, self.g, self.b = cmyk_to_rgb(self.c, self.m, self.y, self.k)


gobject.type_register(Color)
