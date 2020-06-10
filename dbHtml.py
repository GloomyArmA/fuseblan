import sharedHtml as sh #to make common page header and submit buttons
import fsMan as fs # to get dump file last modification time

db_descr_cb_prefix = 'db_descr_cb_'# gather descriptions to update
db_descr_ta_prefix = 'db_descr_ta_'
db_radio = 'db_name_radio'
add_db_descr = 'add_db_descr'
add_from_xml = 'add_from_xml'

del_act = 'delete'
add_act = 'add'
get_xml_act = 'get_xml'
upd_act = 'update'


def mk_db_descr(db_name, db_descr):
  db_descr_ta = db_descr_ta_prefix + db_name
  db_descr_cb = db_descr_cb_prefix + db_name
  html = '<input type = "checkbox" name = "' + db_descr_cb + \
         '" onclick = "setEnableChBox(this, \'' + db_descr_ta + '\')">'
  html += '<label for = "' + db_descr_cb + '">update description:</label><br>'
  html += '<textarea name = "' + db_descr_ta + '" id = "' + \
          db_descr_ta + '" disabled cols = "50" rows = "2" >'
  html += db_descr + '</textarea><br>'
  return html

def mk_db_radio(db_name):
  # js = "setHiddenField('db_name', '" + db_name + "')"
  # return '<input type = "radio" name = "' + db_radio + '" value = "' + \
         # db_name + '" title = "check to choose db" onclick = "' + js + '">'
  return '<input type = "radio" name = "db_name" value = "' + \
         db_name + '" title = "check to choose db">'
         
# def mk_table_cols(group_to_col_labels):
  # html = ''
  # for group, labels in group_to_col_labels.items():
    # html += '<b>' + group + ':</b><br>'
    # html += '; '.join(labels)
  # return  html
  
def mk_db_dump(db_name):
  dump_path, dump_date = fs.get_db_dump_info(db_name)
  return '<a href = "' + dump_path + '" target = "_blank">' + dump_date + \
         '</a>'

def mk_db_table_header():
  html = '''<tr class = "table_header">
            <td><font color = "transparent"> - </font></td>
            <td> Db name </td>
            <td> Db description </td>
            <td> Db dump (last updated) </td>
            </tr>'''
  return html
          
def mk_db_table_html(db_info):
  html = '<table class = "viewer">'
  html += mk_db_table_header()
  for db_name, db_descr in db_info.name_to_descr.items():
    html += '<tr><td>' + mk_db_radio(db_name) + '</td>'
    html += '<td>' + db_name + '</td>'
    html += '<td>' + mk_db_descr(db_name, db_descr) + '</td>'
    html += '<td>' + mk_db_dump(db_name) + '</td>'
    html += '</tr>'
  html += '</table>'
  return html
  

def mk_main_form(db_info_list):
  html = '<form id = "metadata" enctype="multipart/form-data">'
  html += sh.mk_action_field()
  html += mk_db_table_html(db_info_list)
  html += '<table class = "form_holder"><tr><td>'
  #actions with chosen:
  # html += '<input type = "hidden" name = "db_name" value = "">\n' 
  # js doesn't work with onclick and radiobox, so db_name is kept in radiobox 
  # values
  html += '<fieldset><legend> Actions with chosen databases: </legend>\n'
  html += sh.mk_submit_btn('view database', 'orgEnzMan.py')
  html += sh.mk_submit_btn('show alignments','alMan.py')
  html += sh.mk_submit_btn('make/update database dump', 'dbMan.py', get_xml_act)
  html += sh.mk_submit_btn('update checked database descriptions', 'dbMan.py', 
                            upd_act)
  html += sh.mk_submit_btn('delete database', 'dbMan.py', del_act)
  html += '</fieldset></td></tr>'
  #add action:
  html += '<tr><td><fieldset><legend> New database: </legend>\n'
  # html += '* Describe new database:'
  html += '<textarea cols = "40" rows = "2" name = "' + add_db_descr + \
          '" placeholder = "place here your database description">'
  html += '</textarea> use xml file as data source: '
  html += '<input type = "file" name = "' + add_from_xml + '">\n'
  html += sh.mk_submit_btn('add database', 'dbMan.py', add_act)
  html += '</fieldset></td></tr></table>'
  html += '</form>'
  return html

def get_add_data(post_data):
  xml_file = post_data.getvalue(add_from_xml, None)
  # xml_file = xml_file.file.read if
  descr = post_data.getvalue(add_db_descr, '')
  return descr, xml_file
  
# def get_chosen_db_name(post_data):
  # db_name = post_data.getvalue(db_radio, '')
  # return db_name
  
def get_descr_to_update(post_data):
  db_name_to_descr = dict()
  for key in post_data.keys():
    if key.startswith(db_descr_cb_prefix): # find checked upd_descr checkboxes
      db_name = key[len(db_descr_cb_prefix) : ]
      new_descr = post_data.getvalue(db_descr_ta_prefix + db_name, '')
      db_name_to_descr[db_name] = new_descr
  return db_name_to_descr
      
  
# пусть этот же файл отвечает за поиск в постдата: ему post_data, он нам - чё надо
# (т.к. названия полей - ёбаный фронтэнд, это область ведения htmler'а)
