#!C:/Python/python.exe
print(r"Content-Type: text/html")
print("\r\n")

from contextlib import closing
from copy import deepcopy
import cgi 
import cgitb
#import srcAndAlMaker as saam
import sharedVars as sv
import sharedFuncs as sf
import sharedClasses as sc
import sharedHtml as sh
import htmlClasses as hc
import dbFace as df
import filterClasses as fc
import filterHtml as fh
# import filterManager as fm

panel_height = 400
   
def mk_su_table_header(su_names_to_show, su_colors):
  html = '<tr class = "table_header">\n'
  for su in su_names_to_show:
    html += '<td bgcolor = "' + su_colors.get_bg_color(su) + \
             '"><font color = "' + su_colors.get_fg_color(su) + \
             '">' + su + '</font></td>'
  html += '\n </tr> \n'
  return html
  
def mk_su_row(enz, su_names_to_show, su_colors):
  su_row = '<tr>'
  for su_name in su_names_to_show:
    same_named_su = enz.su_name_to_su_list.get(su_name, [])
    if len(same_named_su) <1:
      su_row += '<td><font color = "transparent"> - </font></td>'
      continue
    su_row += '<td bgcolor = "' + su_colors.get_bg_color(su_name) + \
              '"><font color = "' + su_colors.get_fg_color(su_name) + '">'
    su_row += ';'.join(s.name for s in same_named_su)
    su_row += '</font></td>'
  su_row += '\n </tr>\n' 
  return su_row
  
def mk_filter_info(filter_vals, id_list):
  html = '<td> Current filters: <br>'
  html += '<textarea name = "filter_vals_ta" cols = "40" rows = "6"' + \
          ' readonly>' + '\n'.join(filter_vals) + '</textarea></td>\n'
  # html += '<input type = "hidden" name = "filter_vals" value = "' + \
          # str(filter_vals) + 
  html += '<td> Showing enzymes identifiers:<br>'
  html += '<textarea name = "id_list" cols = "30" rows = "6">' + \
          str(id_list) + '</textarea></td>\n'
  return html
         
  
def mk_vp_buttons():
  f_set_name_to_acts = dict()
  # f_set_name_to_acts['Actions with enzymes:'] = {}
  f_set_name_to_acts['Actions with enzymes:'] = {
         'getSuSeqLoadAl.py':'get subunit sequences and make fused alignment '
         # 'addEnz.py':'add enzyme',
         # 'editEnz.py':'edit selected',
         # 'removeEnz.py':'remove selected'
         }
  # f_set_name_to_acts['Actions with organisms:'] = {
               # 'addOrg.py':'add organism',
               # 'editOrg.py':'edit selected',
               # 'removeOrg.py':'remove selected'
             # }
  html = ''
  for f_set_name, acts in f_set_name_to_acts.items():
    html += '<td><fieldset><legend>' + f_set_name + '</legend>\n'
    for script_name, btn_text in acts.items():
      html += sh.mk_submit_btn(btn_text, script_name)
    html += '</fieldset></td>\n'
  html += '<td><fieldset><legend> Actions with attributes: </legend>\n'
  html += sh.mk_select('table_name', sv.main_tables) 
  html += sh.mk_submit_btn('edit attributes', 'attrColEdit.py')
  html += '</fieldset></td>\n'
  return html
  
def mk_footer(db_obj, filter_set):
  html = '<table class = "form_holder"><tr>\n' 
  html += mk_filter_info(filter_set.get_filters_values(), db_obj.get_enz_ids())
  html += mk_vp_buttons()
  html += '</tr></table>\n </form><br>\n </body></html>'
  return html
  
def mk_attr_table_header(table_name, attr_col_names, attr_col_descr_list, 
                         show_name = True):
  html = '<tr class = "table_header">\n'
  #first col for checkboxes:
  cb_class, cb_hint = sh.get_id_cb_prefix(table_name), 'check all ' + table_name
  html += '<td> ' + sh.mk_cb_checker(cb_class, cb_hint) + ' </td>'
  #second col for names:
  if show_name:
    html += '<td> Name: </td>'
  #other cols are for attributes:
  # obj_attr_names = attr_col_descr_list.get_table_col_names(table_name)
  for col_name in attr_col_names:
    attr_col = attr_col_descr_list.get_col_by_name(col_name)
    #TODO: make checkbox to edit this attribute column?
    label = attr_col.label if attr_col else 'col label is missed'
    html += '<td> ' + label + ' </td>' #
  html += '</tr>\n'
  return html

def mk_attr_row(data_obj, table_name, attr_col_names, multi_name, 
                show_name = True):    
  # multi_name is True if one checkbox affects another with the same name
  # first col for checkboxes:
  html = '<tr><td>'
  html += sh.mk_id_checkbox(data_obj.id, table_name, multi_name) + '</td>'
  #second col for names:
  if show_name:
    html += '<td> ' + data_obj.name + ' </td>'
  for val in data_obj.get_str_vals(attr_col_names):
    html += '<td> ' + val + ' </td>' 
  html += '</tr>\n'
  return html
  
  
class ViewerParams:
  def __init__(self, db_obj, filter_set):
    if type(db_obj).__name__ == 'DbObj':
      self.acd_list = db_obj.attr_col_descr_list
      self.su_isect_list = sorted(db_obj.org_list_obj.su_names_isect)
      if type(filter_set).__name__ == 'FilterSet':
        self.su_cols = sorted(filter_set.get_su_names_to_show())
        self.org_cols = filter_set.get_col_names_to_show('organisms')
        self.enz_cols = filter_set.get_col_names_to_show('enzymes')
        self.enz_name_col = filter_set.get_show_enz_name()
        # self.filter_vals = filter_set.get_filters_values()
      else: 
        self.su_cols = sorted(db_obj.org_list_obj.su_names_union)
        self.org_cols = self.acd_list.get_table_col_names('organisms')
        self.enz_cols = self.acd_list.get_table_col_names('enzymes')
        self.enz_name_col = True
        # self.filters_vals = []
    else:
      self.su_cols = self.org_cols = self.enz_cols = self.acd_list = []
      # self.filter_vals = []
      
def mk_view_panel(db_obj, viewer_params):
  vp, view_panel = viewer_params, hc.Panel(panel_height)
  su_colors = hc.BgFgHtmlColor(vp.su_cols)
  org_table = enz_table = su_table = '<table class = "viewer">'
  org_table += mk_attr_table_header('organisms', vp.org_cols, vp.acd_list)
  enz_table += mk_attr_table_header('enzymes', vp.enz_cols, vp.acd_list)
  su_table += mk_su_table_header(vp.su_cols, su_colors)
  org_num = len(db_obj.org_list_obj.org_list) # number of found organisms
  for org in db_obj.org_list_obj.org_list:
    for enz in org.enz_list: # each row is for enzyme, organism can be repeated.
      org_table += mk_attr_row(org, 'organisms', vp.org_cols, True)
      enz_table += mk_attr_row(enz, 'enzymes', vp.enz_cols, False) #, 
                              # vp.enz_name_col)
      su_table += mk_su_row(enz, vp.su_cols, su_colors)
  # for table in [org_table, enz_table, su_table]: # close all tables
    # table += '</table> \n' - не пашет!
  enz_num, ct = len(db_obj.get_enz_ids()), '</table> \n'
  org_sect = hc.PanelSect(str(org_num) + ' organisms:', org_table + ct, 50)
  enz_sect = hc.PanelSect(str(enz_num) + ' enzymes:', enz_table + ct, 10)
  su_sect_label = 'shared subunits: ' + str(vp.su_isect_list)
  su_sect = hc.PanelSect(su_sect_label, su_table + ct, 38)
  for sect in [org_sect, enz_sect, su_sect]: # add all sections to panel
    view_panel.add_sect(sect)
  return view_panel

def mk_data_form(db_obj, filter_set):
  #o_ and e_attr_col_names are for _visible_ attributes, not all org or enz attr 
  data_form = '<form id = "metadata">\n '
  data_form += sh.mk_db_name_field(db_obj.db_name)
  data_form += fh.mk_filter_form(filter_set, 'Organisms and enzymes filter',
               'apply checked filters', 'orgEnzMan.py', 'metadata')
  view_panel = mk_view_panel(db_obj, ViewerParams(db_obj, filter_set))
  data_form += view_panel.get_html() + mk_footer(db_obj, filter_set) 
  return data_form            

def get_filter_set_and_db_obj(post_data):
  db_name = sh.get_db_name(post_data)
  db_link, db_cursor = df.get_link_and_cursor(db_name)
  if not db_cursor:
    df.close_db(db_link)
    return ['Cannot connect to database ' + db_name], None, None
  db_obj = sc.DbObj(db_name)
  attr_rows = df.get_attr_rows(db_cursor)
  # fill attribute columns description list to set organisms and filters:
  db_obj.attr_col_descr_list.fill_from_attr_rows(attr_rows) 
  # make filters to filter rows obtained from database
  filter_set = fc.FilterSet(db_cursor, post_data, db_obj) 
  wc = filter_set.get_db_query_filter()
  # print('got db qurey clause from filters:', db_rows_clause, '<br>')
  db_rows = df.get_db_rows(db_cursor, ' WHERE ' + wc if wc else '')
  # db_rows = filter_set.filter_db_rows(df.get_db_rows(db_cursor))
  db_obj.set_from_db_rows(db_rows)
  return [], filter_set, db_obj
   
cgitb.enable()
post_data = cgi.FieldStorage()
page_name, status, content, html = 'orgEnzMan.py', [], '', ''
if not post_data: 
  html = sh.mk_page_header(page_name, no_post_data = True)
else:
  status, filter_set, db_obj = get_filter_set_and_db_obj(post_data)
  if db_obj:
    page_label = ' for database ' + db_obj.db_name
    acd_list = db_obj.attr_col_descr_list
    if filter_set:
      filter_set.filter_by_su_composition(db_obj.org_list_obj)
      content += mk_data_form(db_obj, filter_set)
    else:
      o_attr_col_names = acd_list.get_table_col_names('organisms')
      e_attr_col_names = acd_list.get_table_col_names('enzymes')
      content = mk_data_form(db_obj, o_attr_col_names, e_attr_col_names, None)         
  html = sh.mk_page_header(page_name, status, page_label) + content
print(html)
  
  



    