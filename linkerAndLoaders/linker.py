# 3rd party package
from IPython import embed
# official package
import argparse
from collections import OrderedDict

# self-developed
import linker_lib as lb
from gen_obj import round_up,page_align,text_base,word_align



parser = argparse.ArgumentParser(description='input obj files and output the linked(allocated) output file')
parser.add_argument("-i",required=True, action="append",nargs="+", help='input object files')
parser.add_argument('-o',required=True, help='output object file')
args = parser.parse_args()

# read in input obj files
input_objs = []
for input_files in args.i:
    for each_input_file in input_files:
        obj = lb.read(each_input_file)
        input_objs.append(obj)

# relocation
## calculate sizes for each merged segments

abs_addr_map = {} ## this map maps absolute address from input obj to output objs to solve abs symbols/relocatables more quickly
summed_segs = OrderedDict() ## this is the merged segments
for obj_idx,each_obj in enumerate(input_objs):
    abs_addr_map[obj_idx] = {}
    for seg_idx,each_seg in enumerate(each_obj.segs):
        seg_name = each_seg.name
        abs_addr_map[obj_idx][seg_name] = []
        if(seg_name in summed_segs):
            ## calculate summed size
            prev_seg_sz = summed_segs[seg_name][0] ## this prev_seg_sz has already been word aligned
            summed_segs[seg_name][0] += round_up(each_seg.len,word_align)

            abs_addr_map[obj_idx][seg_name] = [prev_seg_sz,prev_seg_sz + each_seg.len]

            ## append data
            summed_segs[seg_name][1] += each_obj.data[seg_idx]
        else:
            summed_segs[seg_name] = [round_up(each_seg.len,word_align), each_obj.data[seg_idx] ]

            ## we didn't consider the base yet, and we ignore the base from the input objs
            ## so this starts from 0 first(will adjust later)
            abs_addr_map[obj_idx][seg_name] = [0,each_seg.len]


## calculate base address
seg_bases = OrderedDict()
first_seg = next(iter(summed_segs))
assert(first_seg == ".text")
seg_bases[first_seg] = text_base
seg_names = list(summed_segs.keys())
for seg_idx,seg_name in enumerate(seg_names):
    if seg_name == ".text":
        continue
    last_seg_name = seg_names[seg_idx - 1]
    ## the base of last seg plus the size of the last seg
    seg_bases[seg_name] = seg_bases[last_seg_name] + summed_segs[last_seg_name][0]
    if seg_name == ".bss":
        assert(last_seg_name == ".data")
        ## word align
        seg_bases[seg_name] = round_up(seg_bases[seg_name],word_align)
    else:
        ## page align
        seg_bases[seg_name] = round_up(seg_bases[seg_name],page_align)

## adjust abs_addr_map according to the new base
for each_obj in abs_addr_map:
    for each_seg_name in abs_addr_map[each_obj]:
        new_base = seg_bases[each_seg_name]
        abs_addr_map[each_obj][each_seg_name][0] += new_base
        abs_addr_map[each_obj][each_seg_name][1] += new_base

class G_Sym_Prop:
    def __init__(self):
        self.value = -1
        self.seg_idx = -1
        self.is_abs = False
        self.is_defined = False
        self.is_mul_defined = False
        self.defined_objs = []

global_sym_table = OrderedDict()
# symbol resolution
## global symbol table
for obj_idx,each_obj in enumerate(input_objs):
    for sym_idx, each_sym in enumerate(each_obj.sym_tbl):
        embed()




o_obj = lb.Obj()

o_obj.nseg = len(summed_segs)
## leave out symbols and relcs for now
o_obj.nsyms = 0
o_obj.nrels = 0

for seg_idx,seg_name in enumerate(seg_names):
    seg = lb.Seg()
    seg.name = seg_name
    seg.start_addr = seg_bases[seg_name]
    seg.len = summed_segs[seg_name][0]
    ## just use the first obj
    seg.desc = input_objs[0].segs[seg_idx].desc
    o_obj.segs.append(seg)

    o_obj.data.append(summed_segs[seg_name][1])

lb.write(o_obj,args.o)