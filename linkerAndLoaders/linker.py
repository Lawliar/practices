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

input_objs = []
for input_files in args.i:
    for each_input_file in input_files:
        obj = lb.read(each_input_file)
        input_objs.append(obj)


summed_segs = OrderedDict()
for each_obj in input_objs:
    for seg_idx,each_seg in enumerate(each_obj.segs):
        seg_name = each_seg.name
        if(seg_name in summed_segs):
            ## calculate summed size
            summed_segs[seg_name][0] += round_up(each_seg.len,word_align)
            ## append data(what about the "hole" caused by alignment?)
            summed_segs[seg_name][1] += each_obj.data[seg_idx]
        else:
            summed_segs[seg_name] = [round_up(each_seg.len,word_align), each_obj.data[seg_idx] ]

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






o_obj = lb.Obj()

o_obj.nseg = len(summed_segs)
## leave out symbols and relcs for now
o_obj.nsyms, o_obj.nrels = 0,0

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