import htmlClasses as hc
import sharedFuncs as sf

start_page = 'dbMan.py'

page_name_to_label = {
  'dbMan.py': 'Database manager', 
  'orgEnzMan.py': 'Organisms and enzymes viewer',
  'attrColEdit.py': 'Edit attributes',
  'addCol.py': 'Add attributes',
  'getSuSeqLoadAl.py': 'Subunits sequences and alignments',
  'alMan.py':'Fused alignment manager',
  'fusedAlViewer.py': 'Fused alignment viewer',
  'splitAn.py': 'Split analyser'
  }

page_name_to_parents = {
  'dbMan.py': [], 
  'orgEnzMan.py': ['dbMan.py'],
  'alMan.py': ['dbMan.py'],
  'fusedAlViewer.py':['alMan.py', 'dbMan.py'],
  'splitAn.py':['fusedAlViewer.py', 'alMan.py', 'dbMan.py'],
  'attrColEdit.py': ['dbMan.py', 'orgEnzMan.py'],
  'addCol.py': ['dbMan.py', 'orgEnzMan.py', 'attrColEdit.py'],
  'getSuSeqLoadAl.py':['dbMan.py', 'orgEnzMan.py']
  }

act_field_id = 'action_field'

page_header = '''<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf8">
  <title> FuseBlAn - Fused Subunit Blocks Analysis</title>
  <link rel="import" href="start.html">
  <link rel="stylesheet" type="text/css" href="basic.css">
  <script src="jascr.js"></script>
  </head>
  
  <body>
  <div class = "page_header">
    <table>
      <tr>
        <td class = "logo">
      <font class="logo">Fuse</font>d Subunit <font class="logo">Bl</font>ock <font class="logo">An</font>alysis (FuseBlAn) 
        </td>'''
        
        
def mk_page_header(page_name, page_status = [], page_label = '', 
                   form_id = 'metadata', no_post_data = False):
  # if type(page_descr).__name__ != 'PageDescr':
    # page_descr = hc.PageDescr('unknown page', 'metadata')
  html = page_header
  label = page_name_to_label.get(page_name, '') + page_label
  if no_post_data:
    html += '<td class = "page_descr">\n No post data available, go to ' + \
            '<a href = "' + start_page + '">start page</a><td>\n'
  else:
    html += '<td class = "page_descr">\n' + label + '</td> \n'
    if page_status:
      html += '<td class = "page_status">\n' + str(page_status) + '\n</td>\n'
    parents = page_name_to_parents.get(page_name, [])
    if parents:
      html += '<td class = "page_descr">\n Go back to: '
      for parent_name in parents:
        parent_label = page_name_to_label.get(parent_name, '')
        html += '<button type = "submit" formaction = "' + parent_name + \
            '" formmethod = "POST" ' + 'value = "' + parent_label + \
            '" form = "' + form_id + '">' + parent_label + '</button> \n'
      html += '</td>\n'
  html += '</tr></table>\n</div><br>\n' #page header div closed
  return html
  
def mk_hidden_field(field_name, value):
  return '<input type = "hidden" name = "' + field_name + '" value = "' + \
         str(value) + '">\n'
  
def mk_db_name_field(db_name):
  return  mk_hidden_field('db_name', db_name)
  
def mk_db_descr_field(db_descr):
  return mk_hidden_field('db_descr', db_descr)
  
def mk_id_list_field(table_name, id_list):
  if type(id_list).__name__ != 'list':
    return ''
  return mk_hidden_field(get_id_list_field_name(table_name), str(id_list))
  
def get_id_list_field_name(table_name):
  return sf.get_id_name(table_name) + '_list'
  
def get_id_list_from_post(post_data, table_name):
  return eval(post_data.getvalue(get_id_list_field_name(table_name), '[]'))
  
def get_db_name(post_data):
  db_name = post_data.getvalue('db_name', '')
  #for f-cking python cgi module getting radibox value as a list!!!
  if db_name:
    # print('***Got db_name from post_data:', db_name, '<br>')
    if type(db_name).__name__ == 'list': 
      db_name = db_name[0]
  return db_name
  
def get_db_descr(post_data):
  return post_data.getvalue('db_descr', '')
  
def get_action(post_data):
  act = post_data.getvalue(act_field_id, '')
  return act
  
def mk_action_field():
  return '<input type = "hidden" name = "' + act_field_id + '" id = "' + \
          act_field_id + '" value = "">\n'
  
def mk_submit_btn(btn_text, script_name, action = ''):
  js = " onclick = \"setHiddenField('" + act_field_id + "', '" + action + \
       "')\"" if action else ''
  btn = '<input type = "submit" formaction = "' + script_name + \
        '" formmethod = "POST" ' + 'value = "' + btn_text +'"' + js +'> \n'
  return btn
  
def mk_id_set_field(id_name, id_set):
  if type(id_set).__name__ != 'set':
    return ''
  return mk_hidden_field(id_name + '_set', str(id_set))
  
def get_id_set_field_name(id_name):
  return id_name + '_set'
  
def get_id_set_from_post(post_data, table_name):
  id_field_name = get_id_set_field_name(sf.get_id_name(table_name))
  return eval(post_data.getvalue(id_field_name,'set()'))
  
def mk_select(name, val_list, val_to_label = dict(), js = '', size = 1,  
              is_mult = False, selected_set = set(), style = ''):
  mult = 'multiple' if is_mult else ''
  html = '<select ' + mult + ' size = "' + str(size) + '" name = "' + name + \
         '"' + js + style + '>\n'
  for val in val_list:
    html += '<option value = "' + str(val) + '"'
    html += ' selected>' if val in selected_set else '>'
    html += str(val_to_label.get(val, val)) + '</option>\n'
  html += '</select>\n' 
  return html
  
def mk_datalist(datalist_id, val_list):
  #offers values for text input field
  html = '<datalist id = "' + datalist_id + '">'
  for val in val_list:
    html += '<option value = "' + val + '">'
  html += '</datalist>'
  return html
  
def mk_textarea(name, rows, cols, content, readonly = True):
  html = '<textarea name = "' + name + '" rows = "' + str(rows) + \
         '" cols = "' + str(cols) + '"'
  html += ' readonly>\n' if readonly else '>\n'
  html += str(content) + '</textarea>\n'
  return html
  
def mk_names_rows_html(id_list, id_to_names):
  html = ''
  for id in id_list:
    name_subst = 'No name found with id ' + id
    html += '<tr><td>' + id_to_names.get(id, name_subst) + '</td></tr>'
  return html
    
def mk_id_checkbox(id, table, multi_name = False):
  #if some checkboxes have the same names, multi_name is true
  if not str(id).isnumeric():
    return ''
  id_cb_prefix = get_id_cb_prefix(table)
  cb_name = id_cb_prefix + str(id)
  #set the same-named checkboxes to the same status:
  js_func = ' onclick = "setSameNamedChBoxState(this)"' if multi_name else ''
  cb_html = '<input type="checkbox" id="'+ cb_name + '" name="' + cb_name + \
            '" class = "' + id_cb_prefix + '" title = "id#' + str(id) + \
            ' in ' + table + '"' + js_func + '/>'
  return cb_html
  
def mk_checkbox(cb_name, label, checked, js = ''): 
  field = '<input name = "' + cb_name + '" type = "checkbox" ' + js
  field += ' checked>' if checked else '>'
  field += '<label for = "' + cb_name + '">' + label + '</label>'
  return field
  
def get_id_cb_prefix(table):
  return sf.get_id_name(table) + '_cb_'
  
def mk_cb_checker(cb_class_name, hint):
  js_func = 'setChBoxStateAsThis(this, \'' + cb_class_name + '\')'
  cb_checker = '<input type = "checkbox" onclick = "' + js_func + \
               '" title = "' + hint + '"/>'
  return cb_checker
  
def get_id_set_from_cb(post_data, table):
  id_set = set()
  cb_prefix = get_id_cb_prefix(table)
  for key in post_data.keys():
    if key.startswith(cb_prefix):
      id_set.add(int(key[len(cb_prefix):]))
  return id_set
  
def get_id_list_from_cb(post_data, table):
  id_list = []
  cb_prefix = get_id_cb_prefix(table)
  for key in post_data.keys():
    if key.startswith(cb_prefix):
      id_list.append(int(key[len(cb_prefix):]))
  return sorted(id_list)
  
def mk_folded_layer(layer_tag, layer_content):
  html = '<div class = "folded"><font class = "h2">' + layer_tag + '</font>\n'
  html += '<div class = "form_holder">\n' + layer_content + '</div>\n</div>\n'
  return html


  
# def get_where_id_from_post(post_data, table_name):
  
