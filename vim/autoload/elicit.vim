
python << endpython
import vim
import dbus

def get_obj(suffix=''):
  """
  Gets a DBUS proxy object
  """
  try:
    bus = dbus.SessionBus()
    obj = bus.get_object('com.rephorm.elicit', '/com/rephorm/Elicit'+suffix)
  except dbus.exceptions.DBusException:
    print "Unable to connect to elicit. Is it installed?"
    obj = None
  return obj

def send_color(hex):
  """
  Send a color value to elicit

  Parameters:
    hex - hexidecimal color string
 
  hex must be 6 characters long plus an optional '#' prefix.
  """
  obj = get_obj()
  if not obj: return

  try:
    obj.SetHex(hex)
  except dbus.exceptions.DBusException:
    print "Error: '{val}' is not valid hex".format(val=val)

def receive_color(hash_prefix=True, uppercase=False):
  """
  Send a color value to elicit

  Parameters:
    hash_prefix: boolean - whether to include hashmark at start or not

  Returns:
    hexidecimal color string
  """
  obj = get_obj()
  if not obj: return

  hex = ''
  try:
    hex = obj.GetHex()

    if not hash_prefix and hex[0] == '#':
      hex = hex[1:]
    if uppercase:
      hex = hex.upper()
  except dbus.expection.DbusException:
    print "Error: Unable to communicate with Elicit"

  return hex

def servername():
  return vim.eval('v:servername')

def start_signalling():
  obj = get_obj('/Vim')
  if not obj: return

  val = obj.StartSignalling(servername())

def stop_signalling():
  obj = get_obj('/Vim')
  if not obj: return

  val = obj.StopSignalling(servername())

endpython

function! s:GetColorPos()
  let orig_pos = getpos(".")
  let color_pattern = '#\?[A-Fa-f0-9]\{6\}'
  let start_pos = searchpos(color_pattern, "bcW", orig_pos[1])
  let end_pos = searchpos(color_pattern, "ceW", orig_pos[1])

  if start_pos[0] == end_pos[0] && start_pos[1] <= orig_pos[2] && end_pos[1] >= orig_pos[2]
    let line = getline(".")
    let ret = [start_pos[0], start_pos[1], end_pos[1]]
  else
    let ret = [0,0,0]
  end

  call setpos(".", orig_pos)

  return ret
endfunction

function! s:GetColor()
  let pos = s:GetColorPos()
  if pos[0] != 0
    let line = getline(pos[0])
    return line[pos[1]-1:pos[2]-1]
  else
    return ''
  endif
endfunction

function! elicit#Elicit_SetCurrentColor()
  let hex = s:GetColor()
  if hex != ''
    py send_color(vim.eval("hex"))
  else
    echomsg "Not currently on a color value"
  endif
endfunction

function! s:GetWord(pos)
  let line = getline(a:pos[0])
  return line[a:pos[1]-1:a:pos[2]-1]
endfunction

function! s:ReplaceWord(pos,word)
  let line = getline(a:pos[0])
  echo a:pos

  let newline = a:word . line[a:pos[2]:]
  if a:pos[1] > 1
    let newline = line[:a:pos[1]-2] . newline
  endif
  call setline(a:pos[0], newline)
endfunction

function! elicit#Elicit_ReplaceCurrentColor()
  py vim.command("let hex = '%s'"%receive_color())
  let pos = s:GetColorPos()
  call s:ReplaceWord(pos, hex)
endfunction

function! elicit#Elicit_NotifyChange(hex)
  if !exists('s:curpos')
    echomsg "Not currently auto-updating."
    return
  endif
  call s:ReplaceWord(s:curpos, a:hex)
endfunction

function! elicit#Elicit_StartSignalling()
  let pos = s:GetColorPos()
  if pos[0] == 0
    echomsg "Not currently on a color value."
    return
  endif

  let s:curpos = pos
  let hex = s:GetWord(pos) 
  py send_color(vim.eval("hex"))
  py start_signalling()
endfunction

function! elicit#Elicit_StopSignalling()
  if !exists('s:curpos')
    echomsg "Not currently auto-updating."
    return
  endif
  py stop_signalling()
  unlet s:curpos
endfunction
