# 3rd party package
from IPython import embed
# official package
import argparse
from collections import OrderedDict
import os

# self-developed
import linker_lib as lb
from gen_obj import round_up,page_align,text_base,word_align


class G_Sym_Prop:
    def __init__(self):
        self.value = -1
        self.seg_idx = -1
        self.is_abs = False
        self.is_defined = False
        self.is_mul_defined = False
        self.defining_objs = []
        self.referencing_objs = []
    def __str__(self):
        ret = 'val:{}\nseg_idx:{}\nis_abs:{}\nis_defined:{}\nis_mul_defined:{}\n'.format( 
            self.value,self.seg_idx,self.is_abs,self.is_defined,self.is_mul_defined 
        ) 
        ret += "defining objs:"
        for each_d_obj in self.defining_objs:
            ret += "  "+str(each_d_obj)+'\n'
        for each_r_obj in self.referencing_objs:
            ret += "  "+str(each_r_obj)+'\n'
        ret += '\n'
        return ret
    def __repr__(self):
        ret = 'val:{}\nseg_idx:{}\nis_abs:{}\nis_defined:{}\nis_mul_defined:{}\n'.format( 
            self.value,self.seg_idx,self.is_abs,self.is_defined,self.is_mul_defined 
        ) 
        ret += "defining objs:"
        for each_d_obj in self.defining_objs:
            ret += "  "+str(each_d_obj)+'\n'
        for each_r_obj in self.referencing_objs:
            ret += "  "+str(each_r_obj)+'\n'
        ret += '\n'
        return ret


def relocation(input_objs):
    abs_addr_map = {} ## this map maps absolute address from input obj to output objs to solve abs symbols/relocatables more quickly
    summed_segs = OrderedDict() ## this is the merged segments
    for obj_idx,each_obj in enumerate(input_objs):
        abs_addr_map[obj_idx] = OrderedDict()
        for seg_idx,each_seg in enumerate(each_obj.segs):
            seg_name = each_seg.name
            abs_addr_map[obj_idx][seg_name] = []
            if(seg_name in summed_segs):
                ## calculate summed size
                prev_seg_sz = summed_segs[seg_name][0] ## this prev_seg_sz has already been word aligned
                summed_segs[seg_name][0] += round_up(each_seg.len,word_align)
                                                              ## here doesn't need to word align
                abs_addr_map[obj_idx][seg_name] = [prev_seg_sz,prev_seg_sz + each_seg.len]

                ## append data
                summed_segs[seg_name][1] += each_obj.data[seg_idx]
            else:
                                        # size and word aligned                ## append data
                summed_segs[seg_name] = [round_up(each_seg.len,word_align), each_obj.data[seg_idx] ]

                ## we didn't consider the base yet, and we ignore the base from the input objs
                ## so this starts from 0 first(will adjust later)
                abs_addr_map[obj_idx][seg_name] = [0,each_seg.len]
    ## calculate base address
    first_seg = next(iter(summed_segs))
    assert(first_seg == ".text")
    summed_segs[first_seg].insert(0,text_base)
    seg_names = list(summed_segs.keys())
    for seg_idx,seg_name in enumerate(seg_names):
        if seg_name == ".text":
            continue
        last_seg_name = seg_names[seg_idx - 1]
        ## the base of last seg plus the size of the last seg
        last_seg_base = summed_segs[last_seg_name][0]
        last_seg_size = summed_segs[last_seg_name][1]
        assert(len(summed_segs[seg_name]) == 2)

        summed_segs[seg_name].insert(0, last_seg_base + last_seg_size) 
        
        ## do the round up
        if seg_name == ".bss":
            assert(last_seg_name == ".data")
            ## word align
            summed_segs[seg_name][0] = round_up(summed_segs[seg_name][0],word_align)
        else:
            ## page align
            summed_segs[seg_name][0] = round_up(summed_segs[seg_name][0],page_align)

    ## adjust abs_addr_map according to the new base
    for each_obj in abs_addr_map:
        for each_seg_name in abs_addr_map[each_obj]:
            new_base = summed_segs[each_seg_name][0]
            abs_addr_map[each_obj][each_seg_name][0] += new_base
            abs_addr_map[each_obj][each_seg_name][1] += new_base

    ### summed_segs:
    ####- key: seg name
    ####- value:(seg base, seg size, actual data)
    return abs_addr_map,summed_segs

def sum_up_symbols(input_objs):
    global_sym_table = OrderedDict()
    # symbol resolution
    ## global symbol table
    for obj_idx,each_obj in enumerate(input_objs):
        for sym_idx, each_sym in enumerate(each_obj.sym_tbl):
            sym_name = each_sym.name
            sym_type = each_sym.type
            sym_seg = each_sym.seg_idx
            sym_val = each_sym.val

            ## check if it's in global symbol table yet
            if sym_name not in global_sym_table:
                ## current symbol not in sym table, just create one and continue
                g_sym_ent = G_Sym_Prop()

                g_sym_ent.value = sym_val
                g_sym_ent.seg_idx = sym_seg
                if("A" in sym_type):
                    g_sym_ent.is_abs = True ## default is false
                if("D" in sym_type):
                    g_sym_ent.is_defined = True ## default is false
                    g_sym_ent.defining_objs.append((obj_idx,sym_idx))
                else:
                    g_sym_ent.referencing_objs.append((obj_idx,sym_idx))
                global_sym_table[sym_name] = g_sym_ent
                ## is multi_defined is alway false here
            else:
                g_sym_ent = global_sym_table[sym_name]
                ## multi-definition(collision), just remember the collision 
                if g_sym_ent.is_defined and "D" in sym_type:
                    global_sym_table[sym_name].is_mul_defined = True
                    global_sym_table[sym_name].defining_objs.append((obj_idx,sym_idx))
                    continue
                elif g_sym_ent.is_defined and "D" not in sym_type:
                    assert("U" in sym_type)
                    global_sym_table[sym_name].referencing_objs.append((obj_idx,sym_idx))
                elif not g_sym_ent.is_defined and "D" in sym_type:
                    global_sym_table[sym_name].value = sym_val
                    global_sym_table[sym_name].seg_idx = sym_seg
                    if("A" in sym_type):
                        global_sym_table[sym_name].is_abs = True
                    else:
                        global_sym_table[sym_name].is_abs = False
                    global_sym_table[sym_name].is_defined = True
                    global_sym_table[sym_name].is_mul_defined = False

                    assert(len(global_sym_table[sym_name].defining_objs) == 0)
                    global_sym_table[sym_name].defining_objs.append((obj_idx,sym_idx))

                    assert(len(global_sym_table[sym_name].referencing_objs) > 0)
                elif not g_sym_ent.is_defined and "D" not in sym_type:
                    global_sym_table[sym_name].referencing_objs.append((obj_idx,sym_idx))
    return global_sym_table

def abs_to_relative(abs_val,input_obj):
    for each_seg in input_obj.segs:
        start_addr,len = each_seg.start_addr,each_seg.len
        if(abs_val >= start_addr and abs_val <= (start_addr + len)):
            return each_seg.name, abs_val - start_addr
    print("abs val not in this obj")
    embed()

def gen_new_val(cur_val,defining_obj_idx,seg_idx,abs_addr_map):
    ## input:
    ###  defining_obj_idx: starts from 0
    ###  seg_idx: starts from 1 e.g., the seg of .text is 1
    seg_name = list(abs_addr_map[1].keys())[seg_idx - 1]
    low,high = abs_addr_map[defining_obj_idx][seg_name]
    assert((high - low) >= cur_val )

    assert(defining_obj_idx > 0)## because if it's 0, then it doesn't need a new relative addr
    foremost_low,_ = abs_addr_map[0][seg_name]
    assert(low  >  foremost_low)
    return cur_val + low - foremost_low
def global_symbol_resolution(abs_addr_map, global_sym_table,input_objs):
    ## input_obj are just for references
    not_defined_syms = OrderedDict()
    mul_defined_syms = OrderedDict()
    for each_global_sym in global_sym_table:
        if global_sym_table[each_global_sym].is_defined == False:
            not_defined_syms[each_global_sym] = global_sym_table[each_global_sym]
            continue
        if global_sym_table[each_global_sym].is_mul_defined == True:
            mul_defined_syms[each_global_sym] = global_sym_table[each_global_sym]
            continue
        if global_sym_table[each_global_sym].is_abs == True:
            cur_val = global_sym_table[each_global_sym].value
            assert(len(global_sym_table[each_global_sym].defining_objs) == 1)
            defining_obj_idx = global_sym_table[each_global_sym].defining_objs[0][0]
            
            old_seg_name, old_seg_off = abs_to_relative(cur_val, input_objs[defining_obj_idx])
            new_val = abs_addr_map[defining_obj_idx][old_seg_name][0] + old_seg_off
            assert(new_val <= abs_addr_map[defining_obj_idx][old_seg_name][1])
            global_sym_table[each_global_sym].value = new_val
        else:
            ## because it's not abs, then seg_idx must not be 0
            ## since seg_idx in myobj starts from 1 if the symbol is either undefined or absolute
            seg_idx = global_sym_table[each_global_sym].seg_idx

            cur_val = global_sym_table[each_global_sym].value
            assert(seg_idx > 0)
            assert(len(global_sym_table[each_global_sym].defining_objs) == 1)
            
            defining_obj_idx = global_sym_table[each_global_sym].defining_objs[0][0]
            
            
            if defining_obj_idx == 0:
                ## 1st obj's relative address remains unchanged
                continue
            ## TODO: generate new relative address
            new_val = gen_new_val(cur_val,defining_obj_idx,seg_idx,abs_addr_map)
            global_sym_table[each_global_sym].value = new_val
    global_sym_table = OrderedDict([ (k,global_sym_table[k]) for k in global_sym_table.keys() \
        if k not in not_defined_syms.keys() and k not in mul_defined_syms.keys() ])
    return global_sym_table,not_defined_syms,mul_defined_syms
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
## `abs_addr_map` maps from input objs into summed_segments
## `summed_segments` record, the base addr, size and data for each summed segment
abs_addr_map,summed_segments = relocation(input_objs)

## global symbol resolution
global_sym_table = sum_up_symbols(input_objs)


global_sym_table,not_defined_sym_table,mul_defined_sym_table = global_symbol_resolution(abs_addr_map, global_sym_table,input_objs)








out_obj = lb.Obj()

out_obj.nseg = len(summed_segments)
## leave out symbols and relcs for now
out_obj.nsyms = len(global_sym_table)
out_obj.nrels = 0

seg_names = list(summed_segments.keys())
for seg_idx,seg_name in enumerate(seg_names):
    seg = lb.Seg()
    seg.name = seg_name
    seg.start_addr, seg.len = summed_segments[seg_name][0],summed_segments[seg_name][1]
    ## just use the first obj, since all desc of all segs merged together should be the same
    seg.desc = input_objs[0].segs[seg_idx].desc
    out_obj.segs.append(seg)

    out_obj.data.append(summed_segments[seg_name][2])
for each_sym in global_sym_table:
    sym = lb.Sym()
    sym.name = each_sym
    sym.val = global_sym_table[each_sym].value
    sym.seg_idx = global_sym_table[each_sym].seg_idx
    
    type = ''
    if(global_sym_table[each_sym].is_defined):
        type += 'D'
    else:
        type += 'U'
    if(global_sym_table[each_sym].is_abs):
        type += 'A'
    else:
        type += 'R'
    sym.type = type
    out_obj.sym_tbl.append(sym)
lb.write(out_obj,args.o)