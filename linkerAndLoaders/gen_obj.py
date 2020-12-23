#! /usr/bin/python
import sys
from random import randint
from random_word import RandomWords
from IPython import embed

'''
author: Changming Liu(charley.ashbringer@gmail.com)
Dec/14/2020

A obj generator written for "Linkers and Loaders" project 3.1,
as this book only asks to write a reader and writer , 
but didn't generate the file to read/write
'''

assert(len(sys.argv) == 2)
target_file_name = sys.argv[1]

out_file = open(target_file_name,"w")
# magic number
out_file.write("LINK\n")

## pre-defined segments
            ## segments names, start addr, length, seg description(looks like start addr is only useful when loading, it doesn't not affect the linking process at all)
segments = [(".text",0x1000,0x2500,"RP"),(".data",0x4000,0xc00,"RWP"),(".bss",0x5000,0x1900,"RW")]

# header
num_segments= len(segments)
num_sym_entries = randint(50,60)
## it makes sense if num of reloc entries is less than num of sym entries
num_reloc_entries = randint(30,40)
out_file.write("{} {} {}\n".format(num_segments,num_sym_entries,num_reloc_entries))

# segment table
            # name,  # addr # len, #desc
for each_seg in segments:
    out_file.write("{} {} {} {}\n".format(each_seg[0],hex(each_seg[1]),hex(each_seg[2]),each_seg[3]))


# symbol table
for i in range(num_sym_entries):
    word_len = randint(3,5)
    name = ""
    for _ in range(word_len):
        ch = randint(97,122)
        name += chr(ch)
    ## this value might fall into the "hole" between different segments
    value = randint(0x1000,0x6900)
    ## 0 means undefined, 1-3 means the corresponding segs
    seg = randint(0,len(segments))
    choice = randint(0,1)
    type = "U" if choice == 0 else "D"
    out_file.write("{} {} {} {}\n".format(name,hex(value),seg,type))

# reloc
unrefereced_sym = set(range(1,num_sym_entries+1))
for i in range(num_reloc_entries):
    loc = randint(0x1000,0x6900)
    seg = randint(1,len(segments))
    ## [-3,-1], means this symbol is a plain relocation item, [1,num_sym_entries] means this is a symbol and refers to the symbol table
    ref = randint(0,num_sym_entries)
    if(ref >= 1):
        ## since random value has conflict(generate the same value), resolve it here
        if ref not in unrefereced_sym:
            ## conflict happens
            ref = unrefereced_sym.pop()
        else:
            unrefereced_sym.remove(ref)
    else:
        ## if ref picks 0, means, it's a plain relocation item which doesn't refer to a symbol,
        ## then this value should refect the seg(this seg should refer to the same `seg` above(I guess?))
        ref = -seg
    type = "A4" if randint(0,1) == 0 else "R4"
    out_file.write("{} {} {} {}\n".format(hex(loc),seg,ref,type))

# object data
for each_seg in segments:
    len = each_seg[2]
    for each_byte in range(len):
        up_four_bits = hex(randint(0,15)).replace("0x","")
        low_four_bits = hex(randint(0,15)).replace("0x","")
        out_file.write(up_four_bits+low_four_bits)
    out_file.write("\n")

out_file.close()