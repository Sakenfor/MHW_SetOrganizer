import os
import json
baseF=os.getcwd()
txt2read=baseF+'\\clothes_numbers.txt'
towrite=baseF+'\\clothes_num.json'
with open(txt2read,'r',encoding='utf-8') as asdf:test=asdf.read()
    

as_dict={}
for ii in test.split('\n'):
    i=ii.split('\t')
    as_dict[i[1]]=i[2]
with open(towrite,'w') as kl:
    json.dump(as_dict,kl,indent=1,sort_keys=1)
print(as_dict)
input('done')
    