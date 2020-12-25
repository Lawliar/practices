# 3rd party package
from IPython import embed
# official package
import argparse
from collections import OrderedDict

# self-developed
import linker_lib

page_align = 0x1000
text_base = 0x1000
word_align = 0x04


parser = argparse.ArgumentParser(description='input obj files and output the linked(allocated) output file')
parser.add_argument("-i",required=True, action="append",nargs="+", help='input object files')
parser.add_argument('-o',required=True, help='output object file')
args = parser.parse_args()

input_objs = []
for input_files in args.i:
    for each_input_file in input_files:
        obj = linker_lib.read(each_input_file)
        input_objs.append(obj)

def round_up(num,base):
    return int(base * round(float(num) / base) )

total_seg_sizes = OrderedDict()
for each_obj in input_objs:
    for each_seg in each_obj.segs:
        seg_name = each_seg.name
        if(seg_name in total_seg_sizes):
            total_seg_sizes[seg_name] += round_up(each_seg.len,word_align)
        else:
            total_seg_sizes[seg_name] = round_up(each_seg.len,word_align)
