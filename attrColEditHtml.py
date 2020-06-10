import sharedClasses as sc
import sharedHtml as sh #to make common elements
import sharedFuncs as sf # to make col_name of table_name and col_id
import htmlClasses as hc
import re


def mk_metadata(db_name, table_name, col_names, groups, id_list, max_id):
  html = '<form id="metadata">\n'
  html += sh.mk_datalist('group_data_list', groups)
  html += sh.mk_hidden_field('groups', str(groups))
  html += sh.mk_db_name_field(db_name)
  html += sh.mk_hidden_field('table_name', table_name)
  html += sh.mk_hidden_field('col_names_list', str(col_names))
  html += sh.mk_hidden_field('last_col_id', str(max_id))
  html += sh.mk_id_list_field(table_name, id_list)
  return html
  
def get_groups(post_data):
  return eval(post_data.getvalue('groups', '[]'))
  
def get_last_col_id(post_data):
  val = post_data.getvalue('last_col_id', '0') 
  # next strings are to see what the FFUU---CK does .getvalue returns!!!!
  # vv = 'yes' if val == 'None' else 'no'
  # print('is last_col_id a string with text "None":', vv, '<br>')
  # print('last col id:', val, '<br>')
  # v = 'yes' if val else 'no'
  # print('really got last col id: ', v, '<br>')
  # vt = 'yes' if type(val).__name__ == 'None' else 'no'
  # print('does last col id have type "None":', vt, '<br>')
  return val if val != 'None' else '0'
  
def get_add_col_num(post_data):
  return post_data.getvalue('add_col_num', '0')
  
def get_id_list(post_data, table_name):
  return sh.get_id_list_from_post(post_data, table_name)
  
def mk_attr_col_name(table_name, col_id):
  col_prefix = sf.get_col_name_prefix(table_name)
  return col_prefix + '_' + str(col_id)

def get_col_names(post_data):
  return eval(post_data.getvalue('col_names_list','[]'))
  
def get_table_name(post_data):
  return post_data.getvalue('table_name', 'organisms')
  
def get_attr_id_val(post_data, col_name, id):
  val = post_data.getvalue(get_val_field_name(col_name, id), None)
  # if val in sv.na_val:
    # val = ''
  return val
  
def mk_attr_col_descr_from_post(post_data, table_name, col_name):
  label = post_data.getvalue(get_lbl_field_name(col_name), 'label missed') 
  group = post_data.getvalue(get_group_field_name(col_name), 'other')
  data_type = post_data.getvalue(get_dt_field_name(col_name), 'text')
  acd = sc.AttrColDescr(table_name, col_name, label, data_type, group)
  return acd
  
def mk_attr_col_from_post(post_data, table_name, col_name):
  return sc.AttrCol(mk_attr_col_descr_from_post(post_data, table_name, col_name))
  
def fill_attr_col_from_post(post_data, col_name, attr_col, id_list = []):
  for id in id_list:
    attr_col.add_id_val(id, get_attr_id_val(post_data, col_name, id))
  return
  
def get_action(post_data, col_name):
  return post_data.getvalue(get_act_field_name(col_name), 'none')

bra, ket = '<tr><td>', '</td></tr>\n'

def get_val_field_name(col_name, id):
  return col_name + '_' + str(id)
  
def get_act_field_name(col_name):
  return 'action_' + col_name
  
def get_lbl_field_name(col_name):
  return 'lbl_' + col_name
  
def get_group_field_name(col_name):
  return 'group_' + col_name
  
def get_dt_field_name(col_name):
  return 'data_type_' + col_name
  
def get_col_content_field_name(col_name): 
  # changing name change it in js actChanged too!
  return 'col_content_' + col_name
  
def get_col_content_field_val(post_data, col_name):
  cnt_field_name = get_col_content_field_name(col_name)
  return post_data.getvalue(cnt_field_name, '')

def mk_val_field(col_name, id, val):
  #field belongs to col_name css-class for js to enable/disable it
  # print('val:', val, ', val_str:', sf.to_str(val),', val_type:', type(val).__name__, '<br>')
  vf = '<input type = "text" name = "' + get_val_field_name(col_name, id) + \
         '" class = "' + col_name + '" value = "' + sf.to_str(val) + '" readonly>'
  return vf
  
def mk_col_content_field(col_name, id_to_val, id_to_name, id_list):
  content, cnt_field_name = '', get_col_content_field_name(col_name)
  for id in id_list:
    content += str(id) + ':=' + id_to_name.get(id, 'Name not found') + '\t' + \
               sf.to_str(id_to_val.get(id, '')) + '\n'
  ta = '<textarea readonly wrap = "off" name = "' + cnt_field_name + \
       '" id = "' + cnt_field_name + '" cols = "30" rows = "6">'
  ta += content + '</textarea>\n'
  return ta
  
def fill_attr_col_from_content_field(post_data, col_name, attr_col):
  lines = get_col_content_field_val(post_data, col_name).replace('\r', '')
  for line in lines.split('\n'): # line format: 'id:=name \t attribute value'. 
    # I.e. '23:= Akkermansia muciniphila ATCC BAA-835 \t Bacteria'
    line = re.split('\t', line)
    if len(line) < 2: # at least id and val are expected
      continue
    id_name, val = re.split(':=', line[0]), line[1]
    id = id_name[0].replace(' ','')
    if re.findall('\D',id): #first item isn't natural number
      continue
    attr_col.add_id_val(int(id), val)
  return 
     

def mk_action_select(col_name):
  # changing actions change them in js actChanged too!
  val_list = ['none', 'edit', 'from_field', 'delete']
  val_to_label = {'none':'no action', 'edit':'edit', 
                  'from_field': 'fill from field above', 'delete':'delete'}
  jscr = ' onchange = "actChanged(this, \'' + col_name + '\')"'
  act_sel = sh.mk_select(get_act_field_name(col_name), val_list, val_to_label, 
                      js = jscr, selected_set = sf.to_set('none'))
  return act_sel
  
def mk_label_field(col_name, col_label, readonly = True): 
  lf = '<input type = "text" class = "' + col_name + '" name = "' + \
        get_lbl_field_name(col_name) + '" value = "' + col_label
  lf += '" readonly>' if readonly else '">'
  return lf

#the vars are outside mk_group_field to avoid making group_datalist each call

def mk_group_field(col_name, group, readonly = True):
  gf = '<input type = "text" name = "' + get_group_field_name(col_name) + \
       '" class = "' + col_name + '" list = "group_data_list" value = "' + group
  gf += '" readonly>' if readonly else '">'
  return gf

def mk_data_type_select(col_name, data_type, readonly = True):
  dt = '<select name = "' + get_dt_field_name(col_name) + '" class = "' + \
       col_name
  dt += '" readonly>' if readonly else '">'
  for type in sc.AttrColDescr.data_types:
    dt += '<option value = "' + type
    dt += '" selected>' if type == data_type else '">'
    dt += type + '</option>\n'
  dt += '</select>'
  # sh.mk_select(get_dt_field_name(col_name), sc.AttrColDescr.data_types, 
       # selected_set = sf.to_set([data_type]) )
  return dt
  
def mk_names_col_caption(table_name, id_list, id_to_name):
  html = '<table style = "width:100%;">'
  col_name = sf.get_name_col_name(table_name)
  html += bra + mk_col_content_field(col_name, dict(), id_to_name, id_list)
  html += bra + 'actions' + ket
  html += bra + 'label' + ket
  html += bra + 'group' + ket
  html += bra + 'data type' + ket
  html += '</table>\n'
  return html

def mk_names_col_content(table_name, id_list, id_to_name):
  html = '<table class = "viewer" style = "text-align: left;"><tr><td>\n'
  # html = '<table><tr><td>\n'
  html += mk_names_col_caption(table_name, id_list, id_to_name)
  html += '</td></tr>\n'
  for id in id_list:
    html += bra + id_to_name.get(id, 'no name for id ' + str(id)) + ket
  html += '</table>\n'
  return html
  
def mk_attr_col_caption(attr_col, id_to_name, id_list):
  acd, id_to_val = attr_col.attr_col_descr, attr_col.id_to_val
  name, label = acd.col_name, acd.label
  group, dt = acd.col_group, acd.data_type
  html = '<table>'
  html += bra + mk_col_content_field(name, id_to_val, id_to_name, id_list) + ket
  html += bra + mk_action_select(name) + ket
  html += bra + mk_label_field(name, label) + ket
  html += bra + mk_group_field(name, group) + ket
  html += bra + mk_data_type_select(name, dt) + ket
  html += '</table>\n'
  return html
  
def mk_attr_cols_content(attr_cols, id_to_name, id_list):
  html = '<table class = "viewer">\n <tr>'
  for attr_col in attr_cols: # make action and descr row
    # col_name = attr_col.attr_col_descr.col_name
    html += '<td>' + mk_attr_col_caption(attr_col, id_to_name, id_list) + \
            '</td>\n'
  html += '</tr>\n'
  for id in id_list: # make row of attr col values for each id
    html += '<tr>'
    for attr_col in attr_cols:
      col_name = attr_col.attr_col_descr.col_name
      val = attr_col.id_to_val.get(id, None)
      html += '<td>' + mk_val_field(col_name, id, val) + \
              '</td>\n'
    html += '</tr>\n'
  html += '</table>\n'
  return html
  
def mk_panel(table_name, attr_cols, id_list, id_to_name):
  panel = hc.Panel(500)
  names_content = mk_names_col_content(table_name, id_list, id_to_name)
  panel.add_sect(hc.PanelSect(table_name +' names', names_content, 15))
  attr_cols_content = mk_attr_cols_content(attr_cols, id_to_name, id_list)
  panel.add_sect(hc.PanelSect(table_name + ' attributes', attr_cols_content, 84))
  return panel
  
# def mk_names_to_id_convert(table_name, id_to_name):
  # js = '''convertNamesToIds('outer_names_ta', 'name_to_id','match_names_ta')'''
  # html = '''<table><tr><td> 
  # Enter names separated with '##':<br>
  # <textarea cols = "40" rows = "10" name = "outer_names_ta" ></textarea>'
  # </td><td>
  # <input type = "hidden" name = "name_to_id" value = "''' + str(id_to_name) + \
  # '''">
  # <input type = "button" onclick = "''' + js + '''" value = "Convert">
  # Get matching ids and names from table "''' + table_name + '''"<br>
  # <textarea cols = "40" rows = "9" name = "match_names_ta" ></textarea>
  # </td></tr></table>'''
  # return html
  
def mk_actions(table_name):
  tn = table_name # get_table_name(post_data)
  format_info = 'File format: id ## col1 := val1 ## col2 := val2 ... \n' + \
    'Id is a ceil number represents an identifier in ' + tn + ' table.\n' + \
    'Col1, col2, ... are attribute column names in ' + tn + ' table. \n' + \
    'Value is everything but :=, ## and end-of-line symbols taking \n' + \
    'that its type has to be of valid attribute data types'
  html = '<fieldset><legend>Actions with attributes</legend><table><tr><td>\n'
  html += sh.mk_submit_btn('Add', 'addCol.py')
  html += '<input type = "number" min = "0" max = "10" name = "add_col_num">'
  html += ' attribute columns to table "' + tn + '"</td><td>'
  html += 'File to update chosen attributes: '
  html += '<input type = "file" name = "attr_scr_xml" title = "' + \
          format_info + '">\n'
  html += sh.mk_submit_btn('Perform selected actions', 'attrColEdit.py')
  html += '\n</td></tr></table></fieldset>\n'
  return html

def mk_footer(table_name, id_to_name):
  html = '<table class = "form_holder"><tr><td>\n'
  html += mk_actions(table_name) #+ '</td><td>\n'
  # html += mk_names_to_id_convert(table_name, id_to_name)
  html += '</td></tr></table>\n'
  return html