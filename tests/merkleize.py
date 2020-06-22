import sha3
import yaml
import pickle
import math



verbose = 0




# Implementation of some sections of the Ethereum yellowpaper.





#####################################
# Appendix B. Recursive Length Prefix

# main functions for encoding (RLP) and decoding (RLP_inv)
def RLP(x, leaf_flag=True):
  if verbose: print("RLP(",x,")")
  if type(x) in {bytearray,bytes}:
    return R_b(x)
  elif type(x)==int:
    return RLP(BE(x))
  else: #list
    return R_l(x, leaf_flag)

# binary encoding/decoding
def R_b(x):
  if verbose: print("R_b(",x,")")
  if len(x)==1 and x[0]<128:
    return x #bytearray([x[0] + 0x80])
  elif len(x)<56:
    return bytearray([128+len(x)])+x
    #return x
  else:
    #print(len(BE(len(x))), BE(len(x)) , x)
    return bytearray([ 183+len(BE(len(x))) ]) + BE(len(x))  + x

# int to big-endian byte array
def BE(x):
  if verbose: print("BE(",x,")")
  if x==0:
    return bytearray([])
  ret = bytearray([])
  while x>0:
    ret = bytearray([x%256]) + ret
    x=x//256
  return ret

# list encoding/decoding
def R_l(x, leaf_flag):
  if verbose: print("R_l(",x,")")
  sx=s(x,leaf_flag)
  if len(sx)<56:
    return bytearray([192+len(sx)]) + sx
  else:
    return bytearray([ 247+len(BE(len(sx)))]) + BE(len(sx)) + sx

# for a list, recursively call RLP
def s(x, leaf_flag):
  if verbose: print("s(",x,")")
  sx = bytearray([])
  for xi in x:
    if leaf_flag:
      sx+=RLP(xi)
    else:
      sx+=xi
  return sx





###########################################
# Appendix D. Modified Merkle Patricia Tree

"""
Trying to follow the yellowpaper, tree nodes are lists, with nested children
(with optional memoized hashes appended to extension and branch nodes):
  ["extension", (len,segment_hex), child]
  ["branch", children]
And leafs are one of
  ["leaf", addyhex, nonce, balance]
  ["leaf", addyhex, nonce, balance, storage, codehex]
  ["leaf", addyhex, nonce, balance, storage, [codelen,codehash]]
  ["leaf", keyhex, valuehex]
"""

def merkleize_branch_recursive(branch_node,nibbledepth,storageflag):
  children = branch_node[1]
  children_hashes = []
  for child in children:
    if child == None or child == "":
      children_hashes.append(bytes([]))
    else:
      child_hash = merkleize(child,nibbledepth+1,storageflag)
      children_hashes.append(child_hash)
  hash_ = sha3.keccak_256(RLP(children_hashes+[b''])).digest()
  return hash_

def merkleize_extension_recursive(ext_node,nibbledepth,storageflag):
  if verbose: print("merkleize_extension_recursive",ext_node,nibbledepth,storageflag)
  segment = ext_node[1][1]
  child = ext_node[2]
  if len(segment) % 2 == 0:
    segment_hp = bytes.fromhex("00" + segment)
  else:
    segment_hp = bytes.fromhex("1"  + segment)
  child_hash = merkleize(child,nibbledepth+len(segment),storageflag)
  hash_ = sha3.keccak_256(RLP([segment_hp, child_hash])).digest()
  return hash_

def merkleize_leaf(leaf_node,nibbledepth,storageflag):
  if verbose: print("merkleize_leaf",leaf_node)
  addyhex = leaf_node[1]
  leaf_data = leaf_node[2:]
  if not storageflag:
    nonce = int(leaf_data[0],16)
    balance = int(leaf_data[1],16)
    if len(leaf_data)==2:
      account = [BE(nonce),
                 BE(balance),
                 bytes.fromhex("56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"), #empty root
                 bytes.fromhex("c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")] #empty codeHash
    else:
      storage = leaf_data[3]
      code_ = leaf_data[2]
      if len(code_)==2:
        codehash = bytes.fromhex(code_[1])
      else:
        codehash = sha3.keccak_256(bytes.fromhex(code_)).digest()
      storageroothash = merkleize(storage,0,1)
      account = [BE(nonce),
                 BE(balance),
                 storageroothash,
                 codehash]
    rlp_encoded_leaf_data = RLP(account)
  else:
    key = bytes.fromhex(addyhex)
    value = bytes.fromhex(leaf_data[0])
    rlp_encoded_leaf_data = RLP([key,value])
  segment = sha3.keccak_256(bytes.fromhex(addyhex)).digest().hex()[nibbledepth:]
  if len(segment) % 2 == 0:
    segment_hp = bytes.fromhex("20" + segment)
  else:
    segment_hp = bytes.fromhex("3"  + segment)
  rlp_encoded_leaf = RLP([segment_hp, rlp_encoded_leaf_data])
  hash_ = sha3.keccak_256(rlp_encoded_leaf).digest()
  return hash_


def merkleize_storageleaf(leaf_nodenibbledepth):
  addyhex = leaf_node[1]
  leaf_data = leaf_node[2:]
  hash_ = sha3.keccak_256(rlp_encoded_leaf).digest()
  return hash_


def merkleize(tree_node,nibbledepth,storageflag):
  if tree_node[0] == "hash":
    return bytes.fromhex(tree_node[1])
  elif tree_node[0] == "branch":
    return merkleize_branch_recursive(tree_node,nibbledepth,storageflag)
  elif tree_node[0] == "extension":
    return merkleize_extension_recursive(tree_node,nibbledepth,storageflag)
  elif tree_node[0] == "leaf":
    return merkleize_leaf(tree_node,nibbledepth,storageflag)







