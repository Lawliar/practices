class Seg:
    def __init__(self):
        self.name = ''
        self.start_addr = -1
        self.len = -1
        self.desc = ""
class Sym:
    def __init__(self):
        self.name = ''
        self.val = -1
        ## 0 for undefined, 1 for the first seg(usually .text)
        self.seg_idx = -1
        self.type = ''
class Relc:
    def __init__(self):
        self.loc = -1
        self.seg_idx = -1

        #### [-3,-1], means this symbol is a plain relocation item, and 0 means for the first seg
        ####, [1,num_sym_entries] means this is a symbol and refers to the symbol table
        self.ref = -0x7fff
        self.type = ''

class Obj:
    def __init__(self):
        self.nseg = -1
        self.nsyms = -1
        self.nrels = -1
        self.segs = []
        self.sym_tbl = []
        self.relc_tbl = []
        self.data = []

def read(obj_filename):
    obj = Obj()
    with open(obj_filename,'r') as rfile:
        lines = rfile.readlines()
        cur = 0

        assert(lines[cur].strip() == "LINK")
        cur += 1

        nums = lines[cur].strip().split(" ")
        assert(len(nums) == 3)

        obj.nseg = int(nums[0])
        obj.nsyms = int(nums[1])
        obj.nrels = int(nums[2])
        cur += 1

        ## now seg definitions
        for _ in range(obj.nseg):
            seg = Seg()
            seg_seps = lines[cur].strip().split(" ")
            seg.name       = seg_seps[0]
            seg.start_addr = int(seg_seps[1])
            seg.len        = int(seg_seps[2])
            seg.desc       = seg_seps[3]
            obj.segs.append(seg)
            cur += 1
        
        ## now symbol definitions
        for _ in range(obj.nsyms):
            sym = Sym()
            sym_seps = lines[cur].strip().split(" ")
            sym.name    = sym_seps[0]
            sym.val     = int(seg_seps[1])
            sym.seg_idx = int(seg_seps[2])
            sym.type    = sym_seps[3]
            obj.sym_tbl.append(sym)
            cur += 1
        
        ## now the reloc table
        for _ in range(obj.nrels):
            relc = Relc()
            relc_seps = lines[cur].strip().split(" ")
            relc.loc     = int(relc_seps[0])
            relc.seg_idx = int(relc_seps[1])
            relc.ref     = int(relc_seps[2])
            relc.type    = relc_seps[3]
            obj.relc_tbl.append(relc)
            cur += 1
        
        ## now data
        for  seg_idx in range(obj.nseg):
            obj.data.append((obj.segs[seg_idx].name,lines[cur].strip() ))
            cur += 1
    
    return obj

def write(obj, write_name):
    with open(write_name,"w") as wfile:

        wfile.write("LINK\n")

        wfile.write("{} {} {}\n".format(obj.nseg,obj.nsyms,obj.nrels))
        
        for seg_idx in range(obj.nseg):
            seg = obj.segs[seg_idx]
            wfile.write("{} {} {} {}\n".format(seg.name,hex(seg.start_addr), hex(seg.len), seg.desc))
        
        for sym_idx in range(obj.nsyms):
            sym = obj.sym_tbl[sym_idx]
            wfile.write("{} {} {} {}\n".format(sym.name,hex(sym.val), sym.seg_idx,sym.type))
        
        for relc_idx in range(obj.nrels):
            relc = obj.relc_tbl[relc_idx]
            wfile.write("{} {} {} {}\n".format(hex(relc.loc),relc.seg_idx, relc.ref,relc.type))
        
        for seg_idx in range(obj.nseg):
            wfile.write("{}\n".format(obj.data[1]))
