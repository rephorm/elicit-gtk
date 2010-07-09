HAS_DBUS = True
try:
  import dbus, dbus.service
  from dbus.mainloop.glib import DBusGMainLoop
except ImportError:
  HAS_DBUS = False

ELICIT_BUSNAME = 'com.rephorm.elicit'
ELICIT_INTERFACE = 'com.rephorm.Elicit'
if HAS_DBUS:
  class ElicitService(dbus.service.Object):
    def __init__(self, bus, object_path, elicit, name):
      dbus.service.Object.__init__(self,bus,object_path)
      self.bus = bus
      self.name = name
      self.elicit = elicit

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def Magnify(self):
      self.elicit.action_magnify(None)

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def SelectColor(self):
      self.elicit.action_pick_color(None)

def init(elicit):
  if not HAS_DBUS: return None

  DBusGMainLoop(set_as_default=True)
  bus = dbus.SessionBus()
  print "STARTING BUS: ", ELICIT_BUSNAME
  name = dbus.service.BusName(ELICIT_BUSNAME, bus)
  return ElicitService(bus, '/com/rephorm/Elicit', elicit, name)
