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

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def SetHex(self, hex):
      self.elicit.color.set_hex(hex)

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def GetHex(self):
      return self.elicit.color.hex()

    @dbus.service.signal(dbus_interface=ELICIT_INTERFACE)
    def ColorChanged(self, hex):
      pass

  class VimBridgeService(dbus.service.Object):
    def __init__(self, bus, object_path, elicit, name):
      dbus.service.Object.__init__(self,bus,object_path)
      self.bus = bus
      self.name = name
      self.elicit = elicit
      self._connection_id = None

      self.servers = []

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def StartSignalling(self, servername):
      self.servers.append(str(servername))
      if not self._connection_id:
        self._connect_signal()

    @dbus.service.method(dbus_interface=ELICIT_INTERFACE)
    def StopSignalling(self, servername):
      self.servers.remove(str(servername))
      if len(self.servers) == 0:
        self._disconnect_signal()


    def _connect_signal(self):
      self._connection_id = self.elicit.color.connect('changed', self._on_color_changed)

    def _disconnect_signal(self):
      if not self._connection_id:
        return
      self.elicit.color.disconnect(self._connection_id)
      self._connection_id = None

    def _on_color_changed(self, color):
      for server in self.servers:
        self._notify_server(server, color)

    def _notify_server(self, server, color):
      import subprocess
      command = ':call elicit#Elicit_NotifyChange("{hex}")<cr>'.format(hex=color.hex())
      args = ['vim','--servername', server, '--remote-send', command]
      ret = subprocess.call(args)
      # if the call failed, disconnect so we don't continuously call
      if ret:
        self._disconnect_signal()

def init(elicit):
  if not HAS_DBUS: return None

  DBusGMainLoop(set_as_default=True)
  bus = dbus.SessionBus()

  print "STARTING BUS: ", ELICIT_BUSNAME
  name = dbus.service.BusName(ELICIT_BUSNAME, bus)
  svc = ElicitService(bus, '/com/rephorm/Elicit', elicit, name)
  # connect color changed signal to dbus service
  elicit.color.connect('changed', lambda color: svc.ColorChanged(color.hex()))

  vsvc = VimBridgeService(bus, '/com/rephorm/Elicit/Vim', elicit, name)

  return svc, vsvc
