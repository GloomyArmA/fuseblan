from copy import deepcopy
import numpy as np
import re
from math import log, log10
from math import factorial
import dbFace as df
import sharedFuncs as sf
from decimal import *
from scipy import stats

class Aac:
  def __init__(self, letter, seq_pos, al_pos):
    self.letter = letter #sf.to_str(letter)
    self.seq_pos, self.al_pos = seq_pos, al_pos
    
  def __str__(self):
    return self.letter + '<sub>' + str(self.seq_pos) + '</sub>'
    
class SplitCol:
  def mk_fractions(self, elems):
    elem_to_num, elem_to_fract = dict(), dict()
    for elem in set(elems):
      elem_to_num[elem] = 0 #make dict with zero initial aac fractions
    for elem in elems:
      elem_to_num[elem] += 1 #count each occurence of every aac
    for key in elem_to_num.keys():
      #set aac fractions as (aac counts) / (all aac number)
      elem_to_fract[key] = elem_to_num[key]/len(elems) 
    return elem_to_num, elem_to_fract
    
  def set_aac_order(self):
    l_of_t = sorted(self.all_aac_to_fract.items(), key = lambda x: x[1], 
                                                         reverse = True)
    self.aac_order = [i[0] for i in l_of_t]

  def get_sh_entropy(self, fractions):
    # print('got fracts:',fractions, '<br>')
    return -sum(f*log(f,2) for f in fractions)
        
  def get_random_shen_sample(self, aac_col, sample_size, rand_samp_num):
    rand_shen_samp = []
    for i in range(0, rand_samp_num + 1):
      rand_col = np.random.choice(aac_col, sample_size, False)
      # print('rand_col:', rand_col,'<br>')
      aac_to_fract = self.mk_fractions(rand_col)[1]
      rand_shen_samp.append(self.get_sh_entropy(aac_to_fract.values()))
    return rand_shen_samp
  
  def set_shen_score(self, size, rand_samp_num = 40):
    self.all_shen = self.get_sh_entropy(self.all_aac_to_fract.values())
    self.spl_shen = self.get_sh_entropy(self.spl_aac_to_fract.values())
    rand_shen_samp = self.get_random_shen_sample(self.aac_col, size,
                                                      rand_samp_num)
    if len(self.all_aac_to_fract) > 1:
      # k is an additional value to unpack, only norm_p_val is used here:
      k, self.norm_p_val = stats.normaltest(rand_shen_samp) # normality test
      self.sm, self.sd = np.mean(rand_shen_samp), np.std(rand_shen_samp)
      self.shen_score = abs(self.sm - self.spl_shen)/self.sd if self.sm else 0
    
  def set_prob_score(self, spl_size_factorial = 1):
    denom, prob_mult = 1, 1 #Decimal(), Decimal()
    for aac, num in self.spl_aac_to_num.items():
      # print('num:', num, ', fract:', round(self.all_aac_to_fract[aac], 2))
      fract = Decimal(self.all_aac_to_fract[aac])
      denom *= factorial(num)
      prob_mult *= fract**num
      # print(', lg(denom):', denom.log10, ', lg(prob_mult):', prob_mult.log10, '<br>')
    self.prob = Decimal(spl_size_factorial)*prob_mult/denom
    # print('(', spl_size_factorial, '/',  denom, ')*', prob_mult, '=', self.prob, '<br>')
    # self.prob_score = -log(self.prob, 10) # - gives "math domain error"!!!
    self.prob_score = -float(self.prob.log10())
        
  # def set_fract_diff(self):
    # for aac_name, fract in self.spl_aac_to_fract.items():
      # self.aac_to_diff[aac_name] = fract - self.all_aac_to_fract[aac_name]
      
  def set_split_aacs(self, split_ids, id_to_row_num):
    if not split_ids:
      return
    split_col, size = [], len(split_ids)
    # find row number for each split id and add aac of this row to split col:
    for id in split_ids: 
      split_col += self.aac_col[id_to_row_num[id]]
    self.spl_aac_to_num, self.spl_aac_to_fract = self.mk_fractions(split_col)
    # self.aac_to_diff = dict()
    # self.set_fract_diff() #assign differences in fractions of all and split aacs
    #count prob (probability of column content) and score = -lg(prob):
    # self.set_prob()

  def __init__(self, aac_col, ref_aac):
    #set up scores and their dependent variables:
    self.prob, self.all_shen, self.spl_shen, self.sm, self.sd, = 0, 0, 0, 0, 0
    self.norm_p_val, self.shen_score, self.prob_score = 0, 0, 0
    self.aac_col, self.ref_aac = aac_col, ref_aac
    self.aac_names = sorted(sf.to_set(aac_col))
    self.all_aac_to_fract = self.mk_fractions(aac_col)[1]
    self.set_aac_order() 
    self.spl_aac_to_num, self.spl_aac_to_fract = dict(), dict()
    self.aac_to_diff = dict()
                                                             
class Split:
  def set_al_info(self, al_info_row):
    # self.all_filter_str = al_info_row.get('filter_set', '')
    self.all_ids = eval(al_info_row.get('enz_id_set', 'set()'))
    return True
    
  def add_sn_to_bm(self, su_name, bm_str):
    #make [10,11,12,12,14,22,23,24,25,36,37...] from '10-14;22-25;36-...'
    if not bm_str:
      bm_str = ''
    bm, block_coords = [], [int(s) for s in re.findall('[0-9]+', bm_str)]
    for i in range(1, len(block_coords), 2): # end + 1 to include block end
      bm += range(block_coords[i-1], block_coords[i] + 1)
    self.sn_to_bm[su_name] = bm
    
  def set_su_data(self, sd_rows):
    for row in sd_rows:
      su_name = row.get('su_name', 'no subunit name')
      self.su_names.append(su_name)
      self.sn_to_al[su_name] = sf.try_val_to_int(row.get('al_length', 0))
      #convert markup string to block position list and assign it to subunit:
      self.add_sn_to_bm(su_name, row.get('block_markup', '')) 
      self.sn_to_ref_row[su_name] = []
      
  def set_ref_row(self, su_name, al_seq, bm):
    ref_row, al_pos, seq_pos = [], 0, 0
    for item in al_seq:
      al_pos += 1
      if item != '-':
        seq_pos += 1
      ref_row.append(Aac(item, seq_pos, al_pos))
    for k in range(0, len(bm)): #add necessary positions from ref_row:
      #pick al_pos number from bm (bm[k]), add aac from bm[k]-1 position 
      self.sn_to_ref_row[su_name].append(ref_row[bm[k]-1]) 
        
  def set_aac_cols(self, ad_rows, ref_id):
    row_num, cur_su_name, aac_cols, aac_cols_size_range = 0, '', [], ''
    for db_row in ad_rows:
      su_name = db_row.get('su_name', '')
      if su_name not in self.su_names:
        continue
      if su_name != cur_su_name: 
        #write down previous subunit aac_cols, initialize new ones:
        if aac_cols:
          self.sn_to_aac_cols[cur_su_name] = deepcopy(aac_cols)
          if not self.sn_to_ref_row[cur_su_name]: 
            #ref row hasn't been set, set it as row of gap aac:
            self.set_ref_row(cur_su_name, '-' * self.sn_to_al[cur_su_name], bm)
        #change current su_name, null the row_num to fill in cols from 1st row:
        row_num, cur_su_name = 0, su_name
        aac_cols, bm = [], self.sn_to_bm[su_name] # set new aac_cols and markup
        # aac_cols is shorter than alignment sequences if blocks are marked up,
        # using len(bm) to initialize corresponding number of cols:
        aac_cols_size_range = range(0, len(bm))
        for j in aac_cols_size_range: # make aac_col for each block
          aac_cols.append([])
      al_seq = db_row.get('al_seq') 
      id = sf.try_val_to_int(db_row.get('enz_id', 0))
      self.id_to_row_num[id] = row_num # set row_num for enzyme id
      if id == ref_id: # set reference sequence to enumerate positions:
        self.set_ref_row(su_name, al_seq, bm)
      # read each aac in al_seq to corresp. col: take alignment block pos (j)
      # from k-th bm then add j-th symbol from i-th al_seq to j-th aac_col:
      for k in aac_cols_size_range: 
        # print('k=', k, ', j = ', bm[k], ', al_seq[j] = ', al_seq[bm[k]-1], '<br>')
        aac_cols[k].append(al_seq[bm[k]-1]) #-1 for zero-start enumeration
      row_num += 1
    if aac_cols: #write down the last subunit aac_cols and ref_row
      self.sn_to_aac_cols[cur_su_name] = deepcopy(aac_cols)
      if not self.sn_to_ref_row[cur_su_name]: 
        #ref row hasn't been set, set it as row of gap aac:
        self.set_ref_row(cur_su_name, '-' * self.sn_to_al[cur_su_name], bm)

  def get_split_ids_from_su_pos_aac(self, sn, al_pos, aac_name):
    split_ids = []
    al_pos = int(al_pos) if al_pos.isnumeric() else None
    if al_pos:
      split_col_index = self.sn_to_bm[sn].index(al_pos)
      aac_col = self.sn_to_aac_cols[sn][split_col_index]
      for id, row_num in self.id_to_row_num.items():
        if aac_col[row_num] == aac_name:
          split_ids.append(id)
    return split_ids
    
  def set_split_cols(self, split_ids, use_prob = False, use_shen = False, 
                                                         rand_samp_num = 0):
    spl_size = len(split_ids)
    #to count factorial for all split cols only one time:
    spl_size_factorial = factorial(spl_size) if use_prob else 1
    for sn, aac_cols in self.sn_to_aac_cols.items():
      split_cols = []
      for i in range(0, len(aac_cols)):
        split_col = SplitCol(aac_cols[i], self.sn_to_ref_row[sn][i])
        split_col.set_split_aacs(split_ids, self.id_to_row_num)
        if use_prob:
          split_col.set_prob_score(spl_size_factorial)
        if use_shen:
          split_col.set_shen_score(spl_size, rand_samp_num)
        split_cols.append(split_col)
      self.sn_to_split_cols[sn] = deepcopy(split_cols)

  def set_from_db(self, db_cursor, al_id, ref_id):
    wc = ' WHERE al_id = ' + str(al_id)
    al_info_row = df.send_query(db_cursor, 'SELECT * FROM `al_info` '+ wc)
    sd_rows = df.send_query(db_cursor, 'SELECT * FROM `al_su_data` '+ wc)
    ad_rows = df.send_query(db_cursor, 'SELECT * FROM `al_data` '+ wc + \
                            ' ORDER BY su_name')
    for query_result in [al_info_row, sd_rows, ad_rows]:
      if type(query_result).__name__ == 'str':
        return ['Can\'t get alignment from database: ' + query_result]
    if al_info_row and self.set_al_info(al_info_row[0]):
      self.set_su_data(sd_rows)
      self.set_aac_cols(ad_rows, ref_id)
      
  def __init__(self, db_cursor, al_id, ref_id):
    self.su_names,  self.sn_to_al, self.sn_to_bm = [], dict(), dict()
    self.sn_to_aac_cols, self.sn_to_split_cols = dict(), dict()
    self.sn_to_ref_row, self.id_to_row_num = dict(), dict()
    self.all_ids = set()
    self.set_from_db(db_cursor, al_id, ref_id)
        