import inspect
#if verbose: print(inspect.currentframe().f_code.co_name,idx)
import pprint

verbose = 0

############
# base stuff

def parse_Byte(bytes_, idx):
  #if verbose: print("parse_Byte",bytes_, idx)
  assert len(bytes_)>idx
  byte = bytes_[idx]
  idx += 1
  return idx, byte

def gen_Byte(file_, byte):
  #if verbose: print("gen_byte",file_,byte)
  #file_.write(byte)
  file_.append(byte)

def parse_Integer(bytes_, idx, n):
  if verbose: print("parse_Integer(",idx, n,")")
  idx, low = parse_Byte(bytes_, idx)
  assert low<2**n
  if low>>7:
    idx,high = parse_Integer(bytes_, idx, n-7)
    assert high>0
  else:
    high = 0
  return idx, (high<<7) + low - 128*(low>>7)

def gen_Integer(file_,integer):
  if verbose: print("gen_Integer(",file_,integer,")")
  if type(integer)==str:
    integer = int(integer,16)
  if integer<128:
    gen_Byte(file_,integer)
  else:
    gen_Byte(file_,128+integer%128)
    gen_Integer(file_,integer>>7)

def parse_Bytes32(bytes_,idx):
  if verbose: print("parse_Bytes32",bytes_,idx)
  b = bytearray([])
  for i in range(32):
    idx, byte = parse_Byte(bytes_, idx)
    b.append(byte)
  return idx, b.hex()

def gen_Bytes32(file_,b):
  if verbose: print("gen_Bytes32",file_,b)
  bytes_ = bytes.fromhex(b)
  for i in range(32):
    gen_Byte(file_,bytes_[i])

def parse_Address(bytes_,idx):
  if verbose: print("parse_Address",idx)
  b = bytearray([])
  for i in range(20):
    idx, byte = parse_Byte(bytes_, idx)
    b.append(byte)
  return idx, b.hex()

def gen_Address(file_,a):
  a = bytes.fromhex(a)
  for i in range(20):
    gen_Byte(file_,a[i])

def parse_Byte_Nonzero(bytes_, idx):
  idx, b = parse_Byte(bytes_, idx)
  assert b != 0x00
  return idx, byte

def gen_Byte_Nonzero(file_, b):
  assert b != 0x00
  gen_Byte(file_,b)

def parse_Byte_More_Than_One_Bit_Set(bytes_, idx):
  idx, b = parse_Byte(bytes_, idx)
  assert b not in {0x00,0x01,0x02,0x04,0x08}
  return idx, bytearray([b])

def gen_Byte_More_Than_One_Bit_Set(file_, b):
  gen_Byte(file_,b)

def parse_Bytes2_More_Than_One_Bit_Set(bytes_, idx):
  idx, b1 = parse_Byte(bytes_,idx)
  if bin(b1).count('1')==0:
    idx, b2 = parse_Byte_More_Than_One_Bit_Set(bytes_,idx)
  elif bin(b1).count('1')==1:
    idx, b2 = parse_Byte_Nonzero(bytes_,idx)
  elif bin(b1).count('1')>1:
    idx, b2 = parse_Byte(bytes_,idx)
  return idx, bytearray([b1,b2])

def gen_Bytes2_More_Than_One_Bit_Set(file_, b):
  gen_Byte(file_,b[0])
  gen_Byte(file_,b[1])

def parse_Byte_Lower_Nibble_Zero(bytes_, idx):
  idx, b = parse_Byte(bytes_, idx)
  assert b%16==0
  return idx, b

def gen_Byte_Lower_Nibble_Zero(file_, b):
  gen_Byte(file_,b)

def parse_Nibbles(bytes_, idx, nibbleslen):
  if verbose: print("parse_Nibbles",idx,nibbleslen)
  assert nibbleslen <= 64
  nibbles = bytearray([])
  for i in range(nibbleslen//2):
    idx, b = parse_Byte(bytes_, idx)
    nibbles.append(b)
  if nibbleslen%2:
    idx, b = parse_Byte_Lower_Nibble_Zero(bytes_,idx)
    nibbles.append(b)
  return idx, nibbles.hex()

def gen_Nibbles(file_, n):
  if verbose: print("gen_Nibbles",file_,n)
  bytes_ = bytes.fromhex(n)
  for b in bytes_:
    gen_Byte(file_,b)



#####################################
# main entrypoint here, block witness

def parse_Block_Witness(bytes_, idx):
  idx, v = parse_Version(bytes_, idx)
  assert v == 0x01
  trees = []
  #for i in range(numtrees):
  while len(bytes_)>idx:
    idx, tree = parse_Tree(bytes_,idx)
    trees += [tree]
  return idx, trees

def gen_Block_Witness(file_, trees):
  if verbose: print("gen_Block_Witness",file_,trees)
  gen_Version(file_)
  for t in trees[2:]:
    gen_Tree(file_, t)

def parse_Version(bytes_, idx):
  idx, b = parse_Byte(bytes_, idx)
  return idx, b

def gen_Version(file_):
  if verbose: print("gen_Version",file_)
  gen_Byte(file_,0x01)

def parse_Tree(bytes_,idx):
  idx, b = parse_Byte(bytes_, idx)
  assert b==0x00
  idx,w = parse_Tree_Node(bytes_,idx,0,0)
  return idx, w

def gen_Tree(file_, w):
  if verbose: print("gen_Tree",file_,w)
  gen_Byte(file_,0x00)
  gen_Tree_Node(file_,w[1])



#################################
# tree nodes for world state tree

def parse_Tree_Node(bytes_, idx, d, s):
  if verbose: print("parse_Tree_Node", idx, d, s)
  assert d<65
  idx, nodetype = parse_Byte(bytes_, idx)
  assert nodetype in {0x00,0x01,0x02,0x03}
  if nodetype==0x00:
    idx, branch = parse_Branch_Node(bytes_, idx, d, s)
    return idx, branch
  elif nodetype==0x01:
    idx, extension = parse_Extension_Node(bytes_, idx, d, s)
    return idx, extension
  elif nodetype==0x02:
    idx, leaf = parse_Leaf_Node(bytes_, idx, d, s)
    return idx, leaf
  elif nodetype==0x03:
    idx, hash_ = parse_Bytes32(bytes_, idx)
    return idx, ("hash", hash_)

def gen_Tree_Node(file_, node):
  if verbose: print("gen_Tree_Node",file_,node)
  if node[0]=="branch":
    gen_Byte(file_, 0x00)
    gen_Branch_Node(file_, node)
  elif node[0]=="extension":
    gen_Byte(file_, 0x01)
    gen_Extension_Node(file_, node)
  elif node[0]=="leaf":
    gen_Byte(file_, 0x02)
    gen_Leaf_Node(file_, node)
  elif node[0]=="hash":
    gen_Byte(file_, 0x03)
    gen_Bytes32(file_, node[1])
  else:
    print("ERROR gen_Tree_Node")

def parse_Branch_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Branch_Node",idx,depth, storage_flag)
  assert depth < 64
  idx, bitmask = parse_Bytes2_More_Than_One_Bit_Set(bytes_, idx)
  bitmaskstr = bin(bitmask[0])[2:].zfill(8) + bin(bitmask[1])[2:].zfill(8)
  c = [None]*16
  for i in range(16):
    if bitmaskstr[i]=='1':
      idx, child = parse_Tree_Node(bytes_, idx, depth+1, storage_flag)
      c[i] = child
  return idx, ("branch", c)

def gen_Branch_Node(file_,b):
  if verbose: print("gen_Branch_Node",file_,b)
  # generate bitmask
  bitmaskstr = ""
  for child in b[1]:
    if child:
      bitmaskstr += '1'
    else:
      bitmaskstr += '0'
  bitmask = int(bitmaskstr,2).to_bytes(2,"big")
  gen_Bytes2_More_Than_One_Bit_Set(file_,bitmask)
  # generate children
  for i in range(16):
    if bitmaskstr[i]=='1':
      gen_Tree_Node(file_,b[1][i])

def parse_Extension_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Extension_Node", idx, depth, storage_flag)
  assert depth < 63
  idx, nibbleslen = parse_Byte(bytes_, idx)
  idx, nibbles = parse_Nibbles(bytes_, idx, nibbleslen)
  idx, child = parse_Child_Of_Extension_Node(bytes_, idx, depth+nibbleslen, storage_flag)
  # if odd number of nibbles, last one must be zeros
  return idx, ("extension", (nibbleslen, nibbles), child)

def gen_Extension_Node(file_,e):
  if verbose: print("gen_Extension_Node",file_,e)
  gen_Byte(file_, e[1][0])
  gen_Nibbles(file_, e[1][1])
  gen_Child_Of_Extension_Node(file_,e[2])

def parse_Child_Of_Extension_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Child_Of_Extension_Node",bytes_,idx,depth)
  assert depth<65
  idx, nodetype = parse_Byte(bytes_, idx)
  assert nodetype in {0x00,0x03}
  if nodetype==0x00:
    idx, branch = parse_Branch_Node(bytes_, idx, depth, storage_flag)
    return idx, branch
  elif nodetype==0x03:
    idx, hash_ = parse_Bytes32(bytes_, idx)
    return idx, ("hash", hash_)

def gen_Child_Of_Extension_Node(file_, node):
  if node[0]=="branch":
    gen_Byte(file_, 0x00)
    gen_Branch_Node(file_, node)
  elif node[0]=="hash":
    gen_Byte(file_, 0x03)
    gen_Bytes32(file_, node[1])

def parse_Leaf_Node(bytes_,idx, depth, storage_flag):
  if verbose: print("parse_Leaf_Node", idx, depth, storage_flag)
  assert depth<65
  if storage_flag == 0: # leaf of account tree
    return parse_Account_Node(bytes_,idx,depth)
  else: # leaf of storage tree
    return parse_Storage_Leaf_Node(bytes_,idx,depth)

def gen_Leaf_Node(file_, leaf):
  if verbose: print("gen_Leaf_Node",file_,leaf)
  #print("gen_Leaf_Node",file_,leaf,len(leaf))
  if len(leaf)>3:
    gen_Account_Node(file_, leaf)
  else:
    gen_Storage_Leaf_Node(file_, leaf)

def parse_Account_Node(bytes_,idx,depth):
  if verbose: print("parse_Account_Node",idx,depth)
  idx, accounttype = parse_Byte(bytes_, idx)
  assert accounttype in {0x00,0x01}
  if accounttype == 0x00:
    idx, address = parse_Address(bytes_,idx)
    idx, balance = parse_Integer(bytes_,idx,256)
    idx, nonce = parse_Integer(bytes_,idx,256)
    return idx, ("leaf", address, balance, nonce)
  elif accounttype == 0x01:
    idx, address = parse_Address(bytes_,idx)
    idx, balance = parse_Integer(bytes_,idx,256)
    idx, nonce = parse_Integer(bytes_,idx,256)
    idx, bytecode = parse_Bytecode(bytes_,idx)
    idx, storage = parse_Tree_Node(bytes_, idx, 0, 1)
    return idx, ("leaf", address, balance, nonce, bytecode, storage)

def gen_Account_Node(file_, leaf):
  if verbose: print("gen_Account_Node",leaf, len(leaf))
  if len(leaf)==4:
    gen_Byte(file_, 0x00)
    gen_Address(file_,leaf[1])
    gen_Integer(file_,leaf[2])
    gen_Integer(file_,leaf[3])
  elif len(leaf)==6:
    gen_Byte(file_, 0x01)
    gen_Address(file_,leaf[1])
    gen_Integer(file_,leaf[2])
    gen_Integer(file_,leaf[3])
    gen_Bytecode(file_,leaf[4])
    gen_Tree_Node(file_,leaf[5])

def parse_Bytecode(bytes_, idx):
  if verbose: print("parse_Bytecode(",bytes_, idx,")")
  idx, codetype = parse_Byte(bytes_, idx)
  assert codetype in {0x00,0x01}
  if codetype == 0x00:
    idx, codelen = parse_Integer(bytes_, idx, 32)
    b = bytearray([])
    for i in range(codelen):
      idx, byte = parse_Byte(bytes_, idx)
      b.append(byte)
    return idx,b.hex()
  elif codetype == 0x01:
    idx, codelen = parse_Integer(bytes_, idx, 32)
    idx, codehash = parse_Bytes32(bytes_, idx)
    return idx, (codelen,codehash)

def gen_Bytecode(file_, bytecode):
  if verbose: print("gen_Bytecode(",file_, bytecode,")")
  if type(bytecode)==str:
    gen_Byte(file_, 0x00)
    codelen = len(bytecode)//2
    gen_Integer(file_, codelen)
    for i in range(codelen):
      gen_Byte(file_, bytecode[i])
  else:
    gen_Byte(file_, 0x01)
    gen_Integer(file_,bytecode[0])
    gen_Bytes32(file_,bytecode[1])

def parse_Storage_Leaf_Node(bytes_,idx,depth):
  if verbose: print("parse_Storage_Leaf_Node",bytes_,idx,depth)
  idx, key = parse_Bytes32(bytes_,idx)
  idx, value = parse_Bytes32(bytes_,idx)
  return idx, ("leaf", key, value)

def gen_Storage_Leaf_Node(file_, leaf):
  gen_Bytes32(file_,leaf[1])
  gen_Bytes32(file_,leaf[2])


