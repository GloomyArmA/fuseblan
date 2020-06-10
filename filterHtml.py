import sharedHtml as sh
import sharedFuncs as sf

#_____________________________Name getters:

def get_sc_name(col_name):
  return col_name + '_sc'
  
def get_uf_name(col_name):
  return col_name + '_uf'

def get_max_field_name(col_name):
  return col_name + '_to'
  
def get_min_field_name(col_name):
  return col_name + '_from'
  
def get_rank_select_name(col_name):
  return col_name + '_ranks'
  
def get_text_field_name(col_name):
  return col_name + '_text'
  
#_____________________________Data getters:
  
def get_show_col(post_data, col_name):
  return post_data.getvalue(get_sc_name(col_name))
  
def get_use_filter(post_data, col_name):
  return post_data.getvalue(get_uf_name(col_name), False)
  
# def get_su_set_names_sel_name():
  # return 
  
# def get_su_set_actions_
  
# def get_min_max_vals(post_data, col_name)
  # chosen_min = post_data.getvalue(get_min_field_name(col_name), '')
  # chosen_max = post_data.getvalue(get_max_field_name(col_name), '')
  # return chosen_min, chosen_max
  
def get_chosen_ranks(post_data, col_name):
  cr = post_data.getvalue(get_rank_select_name(col_name), [])
  if type(cr).__name__ == 'str':
    return [cr]
  return cr
  
def get_range_filter_vals(post_data, col_name):
  ch_min_str = post_data.getvalue(get_min_field_name(col_name))
  ch_max_str = post_data.getvalue(get_max_field_name(col_name))
  ch_min = sf.get_num_val_from_str(ch_min_str)
  ch_max = sf.get_num_val_from_str(ch_max_str)
  return ch_min, ch_max
  
def get_text_filter_val(post_data, col_name):
  return post_data.getvalue(get_text_field_name(col_name), '')
  
# def get_chosen_val(post_data, col_name, data_type):
  # f_class = fc.AttrFilter.data_type_to_filter_type.get(data_type, '')
  # if f_class == 'RangeFilter':
    # return get_range_filter_vals(post_data, col_name)
  # if f_class == 'RankFilter':
    # return get_chosen_ranks(post_data, col_name)
  # if f_class == 'TextFilter':
    # return get_text_filter_val(post_data, col_name)
    
def get_chosen_su_names(post_data, filter_name):
  return sf.to_set(post_data.getvalue(filter_name, []))
  
def get_su_set_option(post_data):
  return post_data.getvalue('su_set_option', '')
  
  
#_____________________________Html makers

def mk_range_filter_html(rgf, col_name):
  html = 'from <input type = "number" name = "' + \
          get_min_field_name(col_name) + '" min = "' + str(rgf.min_val) + \
          '" max = "' + str(rgf.max_val) + '" value = "' + \
          str(rgf.chosen_min) + '"><br> \n'
  html += ' to <input type = "number" name = "' + \
          get_max_field_name(col_name) + '" min = "' + str(rgf.min_val) + \
          '" max = "' + str(rgf.max_val) + '" value = "' + \
          str(rgf.chosen_max) + '"> \n'
  return html
  
def mk_rank_filter_html(rkf, col_name):
  select_name = get_rank_select_name(col_name)
  return sh.mk_select(select_name, sorted(rkf.ranks), size = 4, is_mult = True, 
                      selected_set = rkf.chosen_ranks)
                      
def mk_text_filter_html(tf, col_name):
  return '<input type = "text" placeholder = "has text..." name = "' + \
         get_text_field_name(col_name) + '" value = "' + tf.text +'">\n'
         
def mk_filter_cell(uf, f_name, label):
  html = '<td><table id = "' + f_name + '"'
  html += ' class = "active_green">\n<tr><td>' if uf else '>\n<tr><td>'
  html += label + '</td></tr>\n<tr><td>'
  uf_js = 'onclick = "setUseFilterCell(this, \'' + f_name + '\')"'
  html += sh.mk_checkbox(get_uf_name(f_name), ' use filter', uf, uf_js)
  html += '</td></tr>\n'
  return html

def mk_attr_filter_cell(attr_filter, show_col_cb):
  cn, lbl = attr_filter.get_col_name(), attr_filter.get_label()
  html = mk_filter_cell(attr_filter.use_filter, cn, lbl) + '<tr><td>'
  if show_col_cb:
    html += sh.mk_checkbox(get_sc_name(cn), ' show column', 
            attr_filter.show_col) + '</td></tr><tr><td>'
  f = attr_filter.filter
  f_class = type(f).__name__
  if f_class == 'RangeFilter':
    html += mk_range_filter_html(f, cn)
  if f_class == 'RankFilter':
    html += mk_rank_filter_html(f, cn)
  if f_class == 'TextFilter':
    html += mk_text_filter_html(f, cn)
  html += '</td></tr>\n</table></td>'
  return html

def mk_attr_filters(group_to_filters, show_col_cb):
  html = ''
  for group, filters in group_to_filters.items():
    html += '<fieldset> <legend> Filters for ' + group + ' columns </legend>'
    html += '<table class = "form_holder"><tr>'
    for f in filters: # make filter cells for current group
      html += mk_attr_filter_cell(f, show_col_cb)
    html += '</tr></table>'
    html += '</fieldset>'
  return html
  
def mk_main_filters(enz_name_f, su_names_f, su_set_f):
  html = '<fieldset> <legend> Main filters: </legend>'
  html += '<table class = "form_holder"><tr>'
  html += mk_attr_filter_cell(enz_name_f, True)
  html += mk_su_names_filter(su_names_f, 'show subunits')
  html += mk_su_set_filter(su_set_f)
  html += '</tr></table>'
  html += '</fieldset>'
  return html
  
def mk_su_names_filter(su_names_f, label):
  uf, f_name = su_names_f.use_filter, su_names_f.f_name
  html = mk_filter_cell(uf, f_name, label) + '<tr><td>'
  html += sh.mk_select(f_name, su_names_f.su_names, is_mult = True, size = 4,
          selected_set = sf.to_set(su_names_f.chosen_names))
  html += '</td>\n</tr></table></font>\n'
  return html
          
  
def mk_su_set_filter(su_set_f):
  html = mk_su_names_filter(su_set_f.su_names_f, 'subunit composition')
  html += sh.mk_select('su_set_option', su_set_f.options, su_set_f.opt_to_label,
                       selected_set = sf.to_set(su_set_f.option))
  html += '</td>\n</tr></table></font>\n'
  return html
  
def mk_filter_form(f_set, label, btn_name = '', script_name = '',
                   form_name = '', show_col_cb = True, main_filters = True):
  #start of filters layer:
  form_html = ''
  if btn_name:
    form_html += '<input type = "submit" value = "' + btn_name + \
                 '" formaction = "' + script_name + '" form = "' + \
                 form_name + '" formmethod = "POST">\n'
  if main_filters:
  #fill the filters layer with grouped filters:
    form_html += mk_main_filters(f_set.enz_name_filter, f_set.su_names_filter, 
                                 f_set.su_set_filter)
  form_html += mk_attr_filters(f_set.group_to_filters, show_col_cb)
  return sh.mk_folded_layer('Filters', form_html)
  
