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

if g:elicit_map_keys
  nmap <leader>ee :call elicit#Elicit_SetCurrentColor()<cr>
  nmap <leader>er :call elicit#Elicit_ReplaceCurrentColor()<cr>
  nmap <leader>ea :call elicit#Elicit_StartSignalling()<cr>
  nmap <leader>es :call elicit#Elicit_StopSignalling()<cr>
endif
