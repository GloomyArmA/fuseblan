#TODO: доставать id_set из post_data отдельной функцией в AttrFilter
import filterHtml as fh
import dbFace as df
import sharedFuncs as sf
import sharedClasses as sc

class RankFilter:
  #Applied to data which can be splitted on ranks, namely containing
  #repetitive values
  @staticmethod
  def get_query(table_name, col_name, where_case):
    return "SELECT DISTINCT " + col_name + " FROM " + table_name + \
             where_case + " ORDER BY " + col_name
    
  def _init_ranks(self, db_cursor, table_name, col_name, where_case):
    self.ranks, self.chosen_ranks = set(), set()
    query = self.get_query(table_name, col_name, where_case)
    db_rows = df.send_query(db_cursor, query)
    if type(db_rows).__name__ != 'str':
      # print('fc db_rows:', db_rows, '<br>')
      # self.ranks = []
      ranks = [str(row[col_name]) for row in db_rows]
      for rank in ranks:
        if rank:
          self.ranks.add(rank)
    #ERR wrong db_rows + else part
    
  def _set_ranks(self, chosen_ranks):
    self.chosen_ranks = sf.to_set(chosen_ranks) & self.ranks
    
 
  def _set_where_case(self):
    wc = ' IN (' + sf.quoted_vals(self.chosen_ranks) + ')'
    self.where_case = wc if self.chosen_ranks else ''
    
  def get_where_case(self):
    return self.where_case
    
  def apply(self, val):
    return val in self.chosen_ranks
    
  def get_value(self):
    return str(self.chosen_ranks)
    
  def __init__(self, table_name, col_name, db_cursor, chosen_ranks, where_case):
    self._init_ranks(db_cursor, table_name, col_name, where_case)               
    self._set_ranks(chosen_ranks)
    self._set_where_case()
    
# class TextRangeFilter:
  #For attributes like "7.2 - 4,5" and so on
  
class RangeFilter:
  #Applied to 'ceil_range', 'float_range', 'ceil_num', 'float_num' and 'id'
  #data_types
  @staticmethod
  def get_query(table_name, col_name, where_case):
    return "SELECT MIN(" + col_name + "), MAX(" + col_name + ") FROM " + \
                  table_name + where_case
  
  def _init_min_max(self, db_cursor, table_name, col_name, where_case):
    query = self.get_query(table_name, col_name, where_case)
    db_rows = df.send_query(db_cursor, query)
    val_list = [i if i else 0 for i in db_rows[0].values()]
    min_max = [round(val,2) for val in sorted(val_list)]
    # min_max = sorted(db_rows[0].values())
    #ERR wrong db_rows 
    # min_max = sorted(db_rows.values()) # ERR more than two values
    self.min_val, self.max_val = min_max
    self.chosen_min, self.chosen_max = min_max
   
  def _set_min_max(self, chosen_min, chosen_max):
    self.chosen_min = chosen_min if chosen_min else self.min_val
    self.chosen_max = chosen_max if chosen_max else self.max_val
    
  def _set_where_case(self):
    wc = ' BETWEEN ' + str(self.chosen_min) + ' AND ' + str(self.chosen_max)
    chosen = (self.chosen_min != self.min_val) or \
             (self.chosen_max != self.max_val)
    self.where_case = wc if chosen else ''
    
  def get_where_case(self):
    return self.where_case
    
  def apply(self, val):
    if type(val).__name__ == 'str':
      val = sf.get_num_val_from_str(val)
      if not val:
        return True
    return (val <= self.chosen_max and val >= self.chosen_min)
    
  def get_value(self):
    return 'from ' + str(self.chosen_min) + ' to ' + str(self.chosen_max)
    
  def __init__(self, table_name, col_name, db_cursor, chosen_min, chosen_max, 
                                                                 where_case):
    self._init_min_max(db_cursor, table_name, col_name, where_case)
    self._set_min_max(chosen_min, chosen_max)
    self._set_where_case()

class TextFilter:
  def _set_where_case(self):
    wc = " REGEXP '" + self.text + "'"
    self.where_case = wc if self.text else ''
    
  def get_where_case(self):
    return self.where_case

  def __init__(self, text):
    self.text = str(text)
    self._set_where_case()
    
  def apply(self, re_text):
    return True if not self.text else re.search(self.text, re_text)
    
  def get_value(self):
    return self.text
  

class AttrFilter:
  #Is used for attribute. Can be filled from post data with user chosen
  #values of filter. All filter values are obtained from col of db table
  #accordingly to filter data_type. Each data_type defines particular
  #filter subtype using in filter. Every filter subtype should support 
  #apply(db_row), 
  data_type_to_filter_type = {'ranks': 'RankFilter', 
    'ceil_range': 'RangeFilter', 'ceil_num': 'RangeFilter', 
    'float_range': 'RangeFilter', 'float_num': 'RangeFilter',
    'text' : 'TextFilter', 'id' : 'TextFilter'}
  @staticmethod
  def get_filter_type(data_type):
    return AttrFilter.data_type_to_filter_type.get(data_type, '')
    
  def __init__(self, attr_col_descr, db_cursor, post_data, where_case = ''):
    self.attr_col_descr = attr_col_descr
    tn, cn = attr_col_descr.table_name, attr_col_descr.col_name
    self.show_col = fh.get_show_col(post_data, cn)
    self.use_filter = fh.get_use_filter(post_data, cn)
    f_type = self.get_filter_type(self.attr_col_descr.data_type)
    if f_type == 'RankFilter':
      chosen_ranks = fh.get_chosen_ranks(post_data, cn)
      self.filter = RankFilter(tn, cn, db_cursor, chosen_ranks, where_case)
    if f_type == 'RangeFilter':
      ch_min, ch_max = fh.get_range_filter_vals(post_data, cn)
      self.filter = RangeFilter(tn, cn, db_cursor, ch_min, ch_max, where_case)
    if f_type == 'TextFilter':
      text = fh.get_text_filter_val(post_data, cn)
      self.filter = TextFilter(text)
      
  def get_value(self):
    return self.filter.get_value() if self.use_filter else ''

  def get_col_name(self):
    return self.attr_col_descr.col_name
    
  def get_label(self):
    return self.attr_col_descr.label
    
  def get_type(self):
    return self.attr_col_descr.data_type
    
  def get_filter(self):
    return self.filter
    
  def get_where_case(self):
    wc = self.filter.get_where_case()
    return self.get_col_name() + wc if wc else ''

    
  def apply_to_db_row(self, db_row):
    if self.use_filter:
      val = db_row.get(self.get_col_name(), None)
      return True if type(val).__name__ == None else self.filter.apply(val)
      #Don't discard row if it doesn't have 'col_name' value!
    return True
  
  def apply_to_val(self, val):
    if self.use_filter:
      return self.filter.apply(val)
    return True
  
  def apply_to_attr_col(self, attr_col):
    id_passed = []
    for id, val in attr_col.id_to_val.items():
      if self.apply_to_val(val):
        id_passed.append(id)
    return id_passed
    
class SuNames():
  def __init__(self, f_name, db_cursor, post_data, where_case = ''):
    self.f_name = f_name
    query = "SELECT DISTINCT su_name FROM `subunits`" + where_case + \
             " ORDER BY su_name"
    db_rows = df.send_query(db_cursor, query)
    self.su_names = []
    if type(db_rows).__name__ != 'str':
      # print('fc db_rows:', db_rows, '<br>')
      self.su_names = [str(row['su_name']) for row in db_rows]
    self.use_filter = fh.get_use_filter(post_data, f_name)
    self.chosen_names = sorted(fh.get_chosen_su_names(post_data, f_name))
    
class SuFilter():
  options = ['has_all', 'has_any', 'exclude', 'exact', 'extra', 'lack']
  opt_to_label = {'has_any':' has any of selected', 
                  'has_all':' has all selected', 
                  'exact':' has only selected',
                  'exclude':' has no selected', 
                  'extra':' has extra of selected',
                  'lack':' lacks some of selected'}
                  
  def get_value(self):
    if self.use_filter:
      return str(self.chosen_su_set) + ', ' + \
             str(self.opt_to_label.get(self.option, ''))
    return ''
  
  def __init__(self, su_names_f, post_data):
    self.su_names_f = su_names_f
    self.use_filter = su_names_f.use_filter
    self.su_names_set = sf.to_set(su_names_f.su_names)
    self.chosen_su_set = set(su_names_f.chosen_names)
    self.option = fh.get_su_set_option(post_data)
      
  def apply(self, obj):
    #here obj is an Enzyme object
    if type(obj).__name__ != 'Enzyme' :
      print ('SuFilter hasn\'t got Enzyme object to filter')
      return True
    # if not self.use_filter:
      # return True
    enz_su_set = obj.su_names_union
    if self.option == 'has_any': #есть хоть одна из выбранных
      return True if enz_su_set & self.chosen_su_set else False
    if self.option == 'has_all': #есть все выбранные
      return True if self.chosen_su_set <= enz_su_set else False
    if self.option == 'exclude': #нет ни одной из выбранных
      return True if not (self.chosen_su_set & enz_su_set) else False
    if self.option == 'exact': #есть только выбранные
      return True if (self.chosen_su_set == enz_su_set) else False
    if self.option == 'extra': #содержит больше, чем выбрано
      return True if self.chosen_su_set < enz_su_set else False
    if self.option == 'lack': #содержит не все выбранные 
      return True if self.chosen_su_set - enz_su_set else False

class FilterSet: 
  def _mk_main_filters(self, db_cursor, post_data):
    etn, stn = 'enzymes','subunits'
    where_case = self.table_to_where_case.get(etn, '')
    enz_name_col_descr = sc.AttrColDescr(etn, sf.get_name_col_name(etn), 
                         'enzyme name', 'ranks', 'main')
    self.enz_name_filter = AttrFilter(enz_name_col_descr, db_cursor, post_data,
                          where_case)
    self.su_names_filter = SuNames('su_names_filter', db_cursor, post_data, 
                          where_case)
    su_set_filter = SuNames('su_set_filter', db_cursor, post_data, where_case)
    self.su_set_filter = SuFilter(su_set_filter, post_data)
    
  def _mk_attr_filters(self, db_cursor, post_data): 
    for acd in self.attr_col_descr_list.all_cols:
      where_case = self.table_to_where_case.get(acd.table_name, '')
      #temporary banned 'RangeFilter':
      # f_type = AttrFilter.get_filter_type(acd.data_type)
      # if f_type != 'RangeFilter':
      attr_filter = AttrFilter(acd, db_cursor, post_data, where_case)
      self.attr_filters.append(attr_filter)
      sf.add_to_key_to_list(self.table_to_filters, acd.table_name, 
                                attr_filter)
      sf.add_to_key_to_list(self.group_to_filters, acd.col_group,
                                attr_filter)
                              
  def get_db_query_filter(self):
    #return  ' WHERE col1 = 'A' AND col2 = 'B' AND ... AND colN = 'M'"
    where_case, joint,  = [], ' AND '
    for af in self.attr_filters + [self.enz_name_filter]:
      wc = af.get_where_case() if af.use_filter else ''
      if wc:
        where_case.append(wc)
    where_case = ' AND '.join(where_case) if where_case else ''
    return where_case
                                
  def get_show_enz_name(self):
    return self.enz_name_filter.show_col
  
  def get_filters_of_group(self, group):
    return self.group_to_filters.get(group, [])
    
  def get_groups(self):
    return sorted(self.group_to_filters.keys())
    
  def filter_by_su_composition(self, org_list_obj):
    if self.su_set_filter.use_filter:
      filtered_org_list = []
      for org in org_list_obj.org_list:
        filtered_enz_list = []
        for enz in org.enz_list:
          if self.su_set_filter.apply(enz): 
            filtered_enz_list.append(enz)
        if filtered_enz_list:
          org.enz_list = filtered_enz_list
          filtered_org_list.append(org)
      org_list_obj.set_org_list(filtered_org_list)
    
  def get_su_names_to_show(self):
    snf = self.su_names_filter
    return snf.chosen_names if snf.use_filter else snf.su_names
    
  def get_col_names_to_show(self, table_name):
    col_names = []
    for filter in self.table_to_filters.get(table_name, []):
      if filter.show_col:
        col_names.append(filter.get_col_name())
    return col_names
    
  def get_filters_values(self):
    f_vals = []
    for af in self.attr_filters:
      val = af.get_value()
      if val:
        f_vals.append(af.get_label() + ': ' + val)
    val = self.su_set_filter.get_value()
    if val:
      f_vals.append('subunits: ' + val)
    return f_vals
    
  def set_where_case_table(self, enz_id_set, org_id_set):
    self.table_to_where_case = dict()
    table_name_to_id_set = {'enzymes': enz_id_set, 'organisms': org_id_set}
    for tn, id_set in table_name_to_id_set.items():
      wc = sf.get_where_id_case(id_set, tn)
      self.table_to_where_case[tn] = ' WHERE ' + wc if wc else ''
    
  def __init__(self, db_cursor, post_data, db_obj, 
               enz_id_set = set(), org_id_set = set()):
    # if not post_data:
      # return None
    self.db_name = db_obj.db_name
    self.attr_col_descr_list = db_obj.attr_col_descr_list
    self.set_where_case_table(enz_id_set, org_id_set)
    self.attr_filters = []
    self.table_to_filters = dict()
    self.group_to_filters = dict()
    self._mk_attr_filters(db_cursor, post_data)
    self._mk_main_filters(db_cursor, post_data)
    # self.html = fh.mk_filter_form(self)
    
  # def get_html(self):
    # return self.html
    
  