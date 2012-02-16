" =========================================================
" File: elicit.vim
" Description: two-way integration with elicit colorpicker
" Maintainer: Brian Mattern <http://rephorm.com>
" Version: 0.1
" Licensed under the same terms as Vim iteself
" =========================================================
if !exists('g:elicit_map_keys')
  let g:elicit_map_keys = 1
endif

if !exists('g:elicit_highlight_auto')
  let g:elicit_highlight_auto = 1
endif

if g:elicit_map_keys
  nmap <leader>ee :call elicit#Elicit_SendCurrentColor()<cr>
  nmap <leader>ei :call elicit#Elicit_InsertColor()<cr>
  nmap <leader>er :call elicit#Elicit_ReplaceCurrentColor()<cr>
  nmap <leader>ea :call elicit#Elicit_StartAutoReplace()<cr>
  nmap <leader>es :call elicit#Elicit_StopAutoReplace()<cr>
endif

"                  ,_
"                  | \
"     ,-._ ___,-.__| |__  __ ,-._,-._ ___
"     | ._) _ \ __ \ __ \/  \| ._) . V   \
"     | |(  __/ |/ / || | () ) | | |\ /| |
"     |_/ \___) ,_/|_/|_/\__/|_/ |_/|_||_/
"             | |
"             |_/
