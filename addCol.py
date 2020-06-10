#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

import cgi 
import cgitb
import sharedHtml as sh
import sharedFuncs as sf
import sharedClasses as sc
import attrColEditHtml as ah
import dbFace as df
import dbEdit as de

  
def mk_attr_col_cell(col_name):
  html = '<font class = "h3">' + col_name + '</font><br>'
  html += '<table><tr><td>'
  html += 'Attribute label: ' + ah.mk_label_field(col_name, '', False) 
  html += '</td></tr><tr><td>'
  html += 'Attribute group: ' + ah.mk_group_field(col_name, '', False)
  html += '</td></tr><tr><td>'
  html += 'Attribute data type: ' + ah.mk_data_type_select(col_name, '', False)
  html += '</td></tr></table>'
  # html += '''(Choose "ranks" for repetitive values, "text" for unknown data 
             # type. "ceil_num" is for number without delimiter. "float_num" 
             # is for numbers having one dot or comma between digits. 
             # "ceil_range" and "float_range" assume "0.15 - 2" format. Being 
             # applied to single number (i.e. 1.2) range becomes "1.2 - 1.2") 
             # <p>'''  
  return html
  
def mk_footer():
  html = sh.mk_action_field()
  html += sh.mk_submit_btn('Add attributes', 'attrColEdit.py', action = 'add')
  html += '</form>\n'
  return html
  
def mk_attr_cols(max_id, col_num, table_name):
  html = '<table class = "viewer">\n<tr>'
  # max_id = int(ah.get_last_col_id(post_data))
  col_prefix = sf.get_col_name_prefix(table_name)
  # col_num = int(ah.get_add_col_num(post_data))
  for i in range(1, col_num + 1):
    if i/4 == i//4: #finish current tr, start next:
      html += '</tr><tr>\n'
    col_name = ah.mk_attr_col_name(table_name, max_id + i)
    html += '<td>' + mk_attr_col_cell(col_name) + '</td>'
  html += '</tr></table>\n'
  return html
  
cgitb.enable()  
post_data = cgi.FieldStorage()
page_descr, status, content = 'Adding an attribute', '', ''

db_name = sh.get_db_name(post_data)
table_name = ah.get_table_name(post_data)
groups = ah.get_groups(post_data) # ERR: datalist is not a form and could be inaccessible from post_data
max_id = ah.get_last_col_id(post_data) 
# print('got last col id:', max_id, '<br>')
col_num = ah.get_add_col_num(post_data)
content = ah.mk_metadata(db_name, table_name, [], groups, [], max_id)
content += sh.mk_hidden_field('add_col_num', col_num)
content += mk_attr_cols(int(max_id), int(col_num), table_name)
content += mk_footer()

page_label = ' to ' + table_name + ' of ' + db_name
html = sh.mk_page_header('addCol.py', status, page_label)
html += content
print(html)
    
  
  
  