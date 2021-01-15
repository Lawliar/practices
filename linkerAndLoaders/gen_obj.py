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

def round_up(num,base):
    assert(num >= 0 and base >= 0)
    return -( - num // base) * base

page_align = 0x1000
text_base = 0x1000
word_align = 0x04


if __name__ == "__main__":
    assert(len(sys.argv) == 2)
    target_file_name = sys.argv[1]

    out_file = open(target_file_name,"w")
    # magic number
    out_file.write("LINK\n")


    ## pre-defined segments
                ## segments names, start addr, length, seg description(looks like start addr is only useful when loading, it doesn't not affect the linking process at all)
    segments = [(".text",0x1000,randint(0x2000,0x3000),"RP")]
    segments.append((".data", round_up(segments[0][1] + segments[0][2], page_align),randint(0xa00,0x1000),"RWP" ))
    segments.append((".bss", round_up(segments[1][1] + segments[1][2], word_align),randint(0x1100,0x2000),"RW" ))


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
        ## generate random name
        word_len = randint(3,5)
        name = ""
        for _ in range(word_len):
            ch = randint(97,122)
            name += chr(ch)

        
        ## this value might fall into the "hole" between different segments
        choice = randint(0,1)
        ## defined or undefined
        type = "U" if choice == 0 else "D"
        ## relative or absolute
        choice = randint(0,1)
        if choice == 0:
            type += "A"
        else:
            type += "R"
        if(type == "UA"):
            seg_idx = 0
            value = 0
        elif(type == "UR"):
            seg_idx = randint(1,num_segments)
            value = 0
        elif(type =="DA"):
            ## seg_idx == 0 means an absolute or undefined symbol
            seg_idx = 0
            ## offset within the whole module
            value = randint(0,sum([x[2] for x in segments]))
        elif(type == "DR"):
            seg_idx = randint(1,num_segments)
            value = randint(0,segments[seg_idx-1][2])
        out_file.write("{} {} {} {}\n".format(name,hex(value),seg_idx,type))

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
        seg_name = each_seg[0]
        # no data generated for bss
        if not seg_name == ".bss":
            for each_byte in range(len):
                up_four_bits = hex(randint(0,15)).replace("0x","")
                low_four_bits = hex(randint(0,15)).replace("0x","")
                out_file.write(up_four_bits+low_four_bits)
        out_file.write("\n")

    out_file.close()