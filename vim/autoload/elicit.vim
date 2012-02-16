" See plugin/elicit.vim for information

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
  """
  Get the current vim servername
  """
  return vim.eval('v:servername')

def start_signalling():
  """
  Tell elicit to start sending us color changes
  """

  obj = get_obj('/Vim')
  if not obj: return

  name = servername()
  if name:
    val = obj.StartSignalling(name)
  else:
    vim.command('echo "Error: vim is not in clientserver mode"')

def stop_signalling():
  """
  Tell elicit to stop sending us color changes
  """
  obj = get_obj('/Vim')
  if not obj: return

  val = obj.StopSignalling(servername())

endpython

function! s:GetColorPos()
  " Get position of color value under cursor
  "
  " Returns: [line_no, start_pos, end_pos]
  " if not on color, then [0,0,0] is returned

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
  " Get hex color value under cursor
  " Returns: hex value as string, or '' if not on color value

  let pos = s:GetColorPos()
  if pos[0] != 0
    let line = getline(pos[0])
    return line[pos[1]-1:pos[2]-1]
  else
    return ''
  endif
endfunction

function! s:ParseRGB(hex)
  let hex = a:hex
  if hex[0] == '#'
    let hex = hex[1:]
  endif

  return [str2nr(hex[0:1], 16), str2nr(hex[2:3], 16), str2nr(hex[4:5], 16)]
endfunction

function! s:ColorIsLight(hex)
  let [r,g,b] = s:ParseRGB(a:hex)
  let l = (0.21 * r + 0.72 * g + 0.07 * b)
  echo [r,g,b,l]
  return (l > 127)
endfunction

function! elicit#Elicit_SendColor(hex)
  " Send a color value to elicit
  py send_color(vim.eval("a:hex"))
endfunction

function! elicit#Elicit_SendCurrentColor()
  " Send color value under cursor to elicit
  let hex = s:GetColor()
  if hex != ''
    py send_color(vim.eval("hex"))
  else
    echomsg "Not currently on a color value"
  endif
endfunction

function! s:GetWord(pos)
  " Get a word at `pos`
  "
  " pos must be a List [line_no, start_pos, end_pos]
  let line = getline(a:pos[0])
  return line[a:pos[1]-1:a:pos[2]-1]
endfunction

function! s:MatchPos(pos, group)
  " Highlight word a pos
  let word = s:GetWord(a:pos)
  let matchstr = '\%'.a:pos[0].'l\%'.a:pos[1].'c'.word
  return matchadd(a:group, matchstr)
endfunction

function! s:HighlightColor(pos, group)
  let hex = s:GetWord(a:pos)
  execute "highlight ElicitAutoReplace guibg=".hex." guifg=". (s:ColorIsLight(hex) ? '#002b36' : '#fdf6e3')
  return s:MatchPos(a:pos, a:group)
endfunction

function! s:ReplaceWord(pos,word)
  " Replace word at `pos` with `word`
  "
  " See GetWord for the format of `pos`
  let line = getline(a:pos[0])
  let newline = a:word . line[a:pos[2]:]
  if a:pos[1] > 1
    let newline = line[:a:pos[1]-2] . newline
  endif
  call setline(a:pos[0], newline)
endfunction

function! s:InsertString(string)
  " Insert string at current cursor position
  let cmd = "normal! i".a:string.""
  exe cmd
endfunction

function! elicit#Elicit_ReceiveColor()
  py vim.command("let hex = '%s'"%receive_color())
  return hex
endfunction

function! elicit#Elicit_InsertColor()
  call s:InsertString(elicit#Elicit_ReceiveColor())
endfunction

function! elicit#Elicit_ReplaceCurrentColor()
  " Replace color under cursor with color from elicit
  let hex = elicit#Elicit_ReceiveColor()
  let pos = s:GetColorPos()
  call s:ReplaceWord(pos, hex)
endfunction

function! elicit#Elicit_NotifyChange(hex)
  if !exists('s:curpos')
    echomsg "Not currently auto-replacing."
    return
  endif
  call s:ReplaceWord(s:curpos, a:hex)
  if exists('s:auto_highlight_id')
    call matchdelete(s:auto_highlight_id)
    let s:auto_highlight_id = s:HighlightColor(s:curpos, 'ElicitAutoReplace')
  endif
endfunction

function! elicit#Elicit_StartAutoReplace()
  " Begin auto-replacing color under cursor
  "
  " This sends the color under the cursor to elicit and tells elicit to send
  " all color changes back to vim.
  "
  " The line and position of the color is stored, so it is ok to move the
  " cursor while auto-update is on.  However, if the line number or position
  " changes, the wrong text will get updated...
  "
  " Note: this requires that v:servername is set (see :help clientserver)
  if v:servername == ''
    echomsg "Vim is not in clientserver mode. See :help clientserver for more information."
    return
  endif

  if exists('s:curpos')
    call elicit#Elicit_StopAutoReplace()
  endif

  let pos = s:GetColorPos()
  if pos[0] == 0
    echomsg "Not currently on a color value."
    return
  endif

  let s:curpos = pos
  let hex = s:GetWord(pos)
  py send_color(vim.eval("hex"))
  py start_signalling()
  if g:elicit_highlight_auto
    let s:auto_highlight_id = s:HighlightColor(pos, 'ElicitAutoReplace')
  endif
endfunction

function! elicit#Elicit_StopAutoReplace()
  " Stop auto-replacingg the color
  if !exists('s:curpos')
    echomsg "Not currently auto-replacing."
    return
  endif
  py stop_signalling()
  if exists('s:auto_highlight_id')
    call matchdelete(s:auto_highlight_id)
    unlet s:auto_highlight_id
  endif
  unlet s:curpos
endfunction
