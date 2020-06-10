import os
from sys import argv
import subprocess

def get_aligner_call_params(aligner_soft, src_filename, al_filename):
  if not os.path.exists(aligner_soft):
    print('No aligner software at path ', aligner_soft,
          'can\'t make an alignment <br>')
    return ''
  return aligner_soft + ' -in ' + src_filename + ' -out ' + al_filename

def mk_alignment():
  if not os.path.exists('alignments'):
    os.mkdir('alignments') 
  for f_name in os.listdir():
    if f_name.endswith('.fasta'):
      al_filename = os.path.join('alignments', 'aligned_' + f_name)
      al_call_params = get_aligner_call_params('muscle.exe', f_name, al_filename)
      print(al_call_params)
      if al_call_params:
        subprocess.call(al_call_params)
    #print('Subunit file ', f_name,' is sent to aligner...')
    if not os.access(al_filename, os.R_OK):
      print('can\'t access ', al_filename, '<br>')
      return
    print('alignment is done')
  
mk_alignment()