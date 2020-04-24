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

def parse_U32(bytes_, idx):
  b = bytearray([])
  for i in range(4):
    idx, byte = parse_Byte(bytes_, idx)
    b.append(byte)
  u32 = int.from_bytes(b, byteorder="big")
  return idx, u32

def gen_U32(file_, u32):
  b = u32.to_bytes(4, byteorder="big")
  #b = u32.to_bytes((u32.bit_length() + 7) // 8, byteorder="big")
  for byte in b:
    gen_Byte(file_,byte)

def parse_Bytes32(bytes_,idx):
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
  return idx, (nibbleslen, nibbles.hex())

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
  idx, terminal_bb = parse_Byte(bytes_, idx)
  assert terminal_bb == 0xbb
  idx,c = parse_Metadata(bytes_,idx)
  idx,w = parse_Tree_Node(bytes_,idx,0,0)
  return idx, (c,w)

def gen_Tree(file_, w):
  if verbose: print("gen_Tree",file_,w)
  gen_Byte(file_,0xbb)
  gen_Metadata(file_, None)
  gen_Tree_Node(file_,w[1])

def parse_Metadata(bytes_,idx):
  idx, b = parse_Byte(bytes_, idx)
  assert b == 0x00
  return idx, ()

def gen_Metadata(file_, c):
  if verbose: print("gen_Metadata",file_,c)
  gen_Byte(file_,0x00)


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
    return idx, hash_

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
    print("ERROR")

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
  for child in b[1:]:
    if child:
      bitmaskstr += '1'
    else:
      bitmaskstr += '0'
  bitmask = int(bitmaskstr,2).to_bytes(2,"big")
  gen_Bytes2_More_Than_One_Bit_Set(file_,bitmask)
  # generate children
  for i in range(16):
    if bitmaskstr[i]=='1':
      gen_Tree_Node(file_,b[i+1])

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
    return idx, hash_

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
  if len(leaf)>4:
    gen_Account_Node(file_, leaf)
  else:
    gen_Storage_Leaf_Node(file_, leaf)

def parse_Account_Node(bytes_,idx,depth):
  idx, accounttype = parse_Byte(bytes_, idx)
  assert accounttype in {0x00,0x01}
  idx, pathnibbles = parse_Nibbles(bytes_,idx,64-depth)
  idx, address = parse_Address(bytes_,idx)
  idx, nonce = parse_Bytes32(bytes_,idx)
  idx, balance = parse_Bytes32(bytes_,idx)
  if accounttype == 0x01:
    idx, bytecode = parse_Bytecode(bytes_,idx)
    idx, storage = parse_Tree_Node(bytes_, idx, 0, 1)
    return idx, ("account_leaf", pathnibbles, address, balance, nonce, bytecode, storage)
  return idx, ("account_leaf", pathnibbles, address, balance, nonce)

def gen_Account_Node(file_, leaf):
  if len(leaf)==5:
    gen_Byte(file_, 0x00)
  elif len(leaf)==7:
    gen_Byte(file_, 0x01)
  gen_Nibbles(file_,leaf[1][1])
  gen_Address(file_,leaf[2])
  gen_Bytes32(file_,leaf[3])
  gen_Bytes32(file_,leaf[4])
  if len(leaf)>5:
    gen_Bytecode(file_,leaf[5])
    gen_Tree_Node(file_,leaf[6])

def parse_Bytecode(bytes_, idx):
  idx, len_ = parse_U32(bytes_, idx)
  b = bytearray([])
  for i in range(len_):
    idx, byte = parse_Byte(bytes_, idx)
    b.append(byte)
  return idx, b.hex()

def gen_Bytecode(file_, bytecode):
  len_ = len(bytecode)
  gen_U32(file_, len_)
  for i in range(len_):
    gen_Byte(file_, bytecode[i])

def parse_Storage_Leaf_Node(bytes_,idx,depth):
  idx, pathnibbles = parse_Nibbles(bytes_,idx,64-depth)
  idx, key = parse_Bytes32(bytes_,idx)
  idx, value = parse_Bytes32(bytes_,idx)
  return idx, ("storage_leaf", pathnibbles, key, value)

def gen_Storage_Leaf_Node(file_, leaf):
  gen_Nibbles(file_,leaf[1])
  gen_Bytes32(file_,leaf[2])
  gen_Bytes32(file_,leaf[3])

