
verbose = 0


"""
This file has several implementations of parsers for block witnesses.
  parse_Block_Witness_fewer_recursive_funcs() - is like the spec implementation but with some recursive functions merged
  parse_Block_Witness_single_recursive_func() - is like the above, but all recursive functions merged into one
  parse_Block_Witness_stack_based() - is a custom-written stack-based implementation
 
"""




#################
# the entry point

def parse_Block_Witness(bytes_,idx):
  # PLEASE COMMENT ALL OF THESE BUT ONE
  #return parse_Block_Witness_fewer_recursive_funcs(bytes_,idx)
  return parse_Block_Witness_single_recursive_func(bytes_,idx)
  #return parse_Block_Witness_stack_based(bytes_,idx)







########################################
# helper funcs used in many places below

def parse_Bytes(bytes_, idx, numbytes):
  if verbose: print("parse_Bytes", idx, numbytes, len(bytes_))
  assert len(bytes_)>=idx+numbytes-1
  if numbytes==0:
    return idx, bytearray([])
  elif numbytes==1:
    return idx+numbytes, bytes_[idx]
  else:
    return idx+numbytes, bytes_[idx:idx+numbytes]

def peek(bytes_, idx):
  assert len(bytes_)>idx
  return bytes_[idx]

def parse_Nibbles(bytes_, idx, nibbleslen):
  if verbose: print("parse_Nibbles",idx,nibbleslen)
  assert nibbleslen <= 64
  nibbles = bytearray([])
  for i in range(nibbleslen//2):
    idx, b = parse_Bytes(bytes_, idx, 1)
    nibbles.append(b)
  if nibbleslen%2:
    idx, b = parse_Bytes(bytes_, idx, 1)
    assert b%8==0   # rightmost nibble is zero
    nibbles.append(b)
  return idx, nibbles.hex()

def parse_Integer(bytes_, idx, n):
  if verbose: print("parse_Integer(",idx, n,")")
  idx, low = parse_Bytes(bytes_, idx, 1)
  assert low<2**n
  if low>>7:
    idx,high = parse_Integer(bytes_, idx, n-7)
    assert high>0
  else:
    high = 0
  return idx, (high<<7) + low - 128*(low>>7)












####################################
# combine into fewer recursive funcs

def parse_Block_Witness_fewer_recursive_funcs(bytes_,idx):
  if verbose: print("parse_Block_Witness_fewer_recursive_funcs",idx)
  idx, v = parse_Bytes(bytes_, idx, 1)
  assert v == 0x01 # version
  tree_roots = []
  while len(bytes_)>idx:
    idx,zero = parse_Bytes(bytes_,idx,1)
    assert zero == 0x00
    idx, tree_root = parse_Node(bytes_,idx, 0, 0)
    tree_roots.append(tree_root)
  return idx, tree_roots

def parse_Branch_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Branch_Node", idx, depth, storage_flag)
  idx,bitmask = parse_Bytes(bytes_,idx,2)
  bitmaskstr = bin(bitmask[0])[2:].zfill(8) + bin(bitmask[1])[2:].zfill(8)
  assert bitmaskstr.count("1")>1
  children = []
  for bit in bitmaskstr:
    if bit=="1":
      idx, child = parse_Node(bytes_, idx, depth+1, storage_flag)
      children.append(child)
    else:
      children.append(None)
  return idx, ("branch",children)

def parse_Leaf_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Leaf_Node", idx, depth, storage_flag)
  assert depth<65
  if storage_flag==0:
    idx, accounttype = parse_Bytes(bytes_, idx, 1)
    assert accounttype in {0x00,0x01}
    if accounttype == 0x00:
      idx, address = parse_Bytes(bytes_,idx,20)
      idx, balance = parse_Integer(bytes_,idx,256)
      idx, nonce = parse_Integer(bytes_,idx,256)
      return idx, ("leaf", address.hex(), balance, nonce)
    elif accounttype == 0x01:
      idx, address = parse_Bytes(bytes_,idx,20)
      idx, balance = parse_Integer(bytes_,idx,256)
      idx, nonce = parse_Integer(bytes_,idx,256)
      idx, bytecodetype = parse_Bytes(bytes_, idx, 1)
      assert bytecodetype in {0x00,0x01}
      if bytecodetype == 0x00:
        idx, codelen = parse_Integer(bytes_,idx,256)
        idx, code = parse_Bytes(bytes_,idx,codelen)
        idx, storage = parse_Node(bytes_,idx,0,1)
        return idx, ("leaf", address.hex(), balance, nonce, code.hex(), storage)
      elif bytecodetype == 0x01:
        idx, codelen = parse_Integer(bytes_,idx,256)
        idx, codehash = parse_Bytes(bytes_,idx,32)
        idx, storage = parse_Node(bytes_,idx,0,1)
        return idx, ("leaf", address.hex(), balance, nonce, (codelen, codehash.hex()), storage)
  else:
    idx, key = parse_Bytes(bytes_,idx,32)
    idx, value = parse_Bytes(bytes_,idx,32)
    return idx, ("leaf", key.hex(), value.hex())

def parse_Extension_Node(bytes_,idx, depth, storage_flag):
  if verbose: print("parse_Extension_Node", idx, depth, storage_flag)
  assert depth<64
  idx, pathnibbleslen = parse_Bytes(bytes_,idx,1)
  idx, pathnibbles = parse_Nibbles(bytes_,idx,pathnibbleslen)
  assert peek(bytes_,idx) in {0x00,0x03} # extension node can have child branch or hash nodes
  idx, node = parse_Node(bytes_, idx, storage_flag, depth+pathnibbleslen)
  return idx, ("extension", (pathnibbleslen, pathnibbles), node)

def parse_Node(bytes_, idx, depth, storage_flag):
  if verbose: print("parse_Node", idx, depth, storage_flag)
  idx, node_type = parse_Bytes(bytes_,idx,1)
  if node_type == 0x00:  # branch node
    idx, node = parse_Branch_Node(bytes_, idx, depth, storage_flag)
    return idx, node
  elif node_type == 0x01:  # extension node
    idx, node = parse_Extension_Node(bytes_, idx, depth, storage_flag)
    return idx, node
  elif node_type == 0x02:  # leaf node
    idx, node = parse_Leaf_Node(bytes_, idx, depth, storage_flag)
    return idx, node
  elif node_type == 0x03:  # hash node
    idx, hash_ = parse_Bytes(bytes_, idx, 32)
    return idx, ("hash",hash_.hex())
  else:
    print("ERROR")









###########################
# Single recursive function

def parse_Block_Witness_single_recursive_func(bytes_,idx):
  idx, v = parse_Bytes(bytes_, idx, 1)
  assert v == 0x01 # version
  tree_roots = []
  while len(bytes_)>idx:
    idx,zero = parse_Bytes(bytes_,idx,1)
    assert zero == 0x00
    idx, tree_root = parse_Node_single_recursive_func(bytes_,idx, 0, 0)
    tree_roots.append(tree_root)
  return idx, tree_roots

def parse_Node_single_recursive_func(bytes_, idx, depth, storage_flag):
  idx, node_type = parse_Bytes(bytes_,idx,1)
  if node_type == 0x00:  # branch node
    if verbose: print("parse_Branch_Node", bytes_, idx, depth, storage_flag)
    idx,bitmask = parse_Bytes(bytes_,idx,2)
    bitmaskstr = bin(bitmask[0])[2:].zfill(8) + bin(bitmask[1])[2:].zfill(8)
    assert bitmaskstr.count("1")>1
    children = []
    for bit in bitmaskstr:
      if bit=="1":
        idx, child = parse_Node_single_recursive_func(bytes_, idx, depth+1, storage_flag)
        children.append(child)
      else:
        children.append(None)
    return idx, ("branch", children)
  elif node_type == 0x01:  # extension node
    if verbose: print("parse_Extension_Node", bytes_,idx, depth, storage_flag)
    assert depth<64
    idx, pathnibbleslen = parse_Bytes(bytes_,idx,1)
    idx, pathnibbles = parse_Nibbles(bytes_,idx,pathnibbleslen)
    assert peek(bytes_,idx) in {0x00,0x03} # extension node can have child branch or hash nodes
    idx, node = parse_Node_single_recursive_func(bytes_, idx, storage_flag, depth+pathnibbleslen)
    return idx, ("extension", (pathnibbleslen, pathnibbles), node)
  elif node_type == 0x02:  # leaf node
    if verbose: print("parse_Leaf_Node", bytes_, idx, depth, storage_flag)
    assert depth<65
    if storage_flag==0:
      idx, accounttype = parse_Bytes(bytes_, idx, 1)
      assert accounttype in {0x00,0x01}
      if accounttype == 0x00:
        idx, address = parse_Bytes(bytes_,idx,20)
        idx, balance = parse_Integer(bytes_,idx,256)
        idx, nonce = parse_Integer(bytes_,idx,256)
        return idx, ("leaf", address.hex(), balance, nonce)
      elif accounttype == 0x01:
        idx, address = parse_Bytes(bytes_,idx,20)
        idx, balance = parse_Integer(bytes_,idx,256)
        idx, nonce = parse_Integer(bytes_,idx,256)
        idx, bytecodetype = parse_Bytes(bytes_, idx, 1)
        assert bytecodetype in {0x00,0x01}
        if bytecodetype == 0x00:
          idx, codelen = parse_Integer(bytes_,idx,256)
          idx, code = parse_Bytes(bytes_,idx,codelen)
          idx, storage = parse_Node(bytes_,idx,0,1)
          return idx, ("leaf", address.hex(), balance, nonce, code.hex(), storage)
        elif bytecodetype == 0x01:
          idx, codelen = parse_Integer(bytes_,idx,256)
          idx, codehash = parse_Bytes(bytes_,idx,32)
          idx, storage = parse_Node(bytes_,idx,0,1)
          return idx, ("leaf", address.hex(), balance, nonce, (codelen, codehash.hex()), storage)
    else:
      idx, key = parse_Bytes(bytes_,idx,32)
      idx, value = parse_Bytes(bytes_,idx,32)
      return idx, ("leaf", key.hex(), value.hex())
  elif node_type == 0x03:  # hash node
    if verbose: print("parse_Hash_Node", bytes_,idx, depth, storage_flag)
    idx, hash_ = parse_Bytes(bytes_, idx, 32)
    return idx, ("hash",hash_.hex())
  else:
    print("ERROR")







#############
# Stack based

def parse_Block_Witness_stack_based(bytes_,idx):

  storage_flag = 0

  idx, v = parse_Bytes(bytes_, idx, 1)
  assert v == 0x01 # version

  tree_roots = []
  while len(bytes_)>idx:

    idx,bb00 = parse_Bytes(bytes_,idx,2)
    assert bb00 == bytearray([0xbb,0x00]) # new tree, no metadata

    nibbledepth = 0
    stack = []
    stack.append(["parent_of_root",[]])
    first_iter=1
    while len(stack)>1 or first_iter:
      if verbose: print("while 1  nibbledepth",nibbledepth)
      first_iter=0

      # parse node type byte
      idx, node_type = parse_Bytes(bytes_,idx,1)
      assert node_type in {0x00,0x01,0x02,0x03}
      # create appropriate node type
      if node_type == 0x00:  # branch node
        if verbose: print("branch 1", idx, nibbledepth, storage_flag)
        assert nibbledepth<65
        idx,bitmask = parse_Bytes(bytes_,idx,2)
        bitmaskstr = bin(bitmask[0])[2:].zfill(8) + bin(bitmask[1])[2:].zfill(8)
        assert bitmaskstr.count("1")>1
        children = []
        for bit in bitmaskstr:
          if bit=="0":
            children.append(None)
          else:
            break
        stack.append(["branch", bitmaskstr, children])
        nibbledepth+=1
      elif node_type == 0x01:  # extension node
        if verbose: print("extension 1", idx, nibbledepth, storage_flag)
        assert nibbledepth<63
        idx, pathnibbleslen = parse_Bytes(bytes_,idx,1)
        assert pathnibbleslen>0
        idx, pathnibbles = parse_Nibbles(bytes_,idx,pathnibbleslen)
        assert peek(bytes_,idx) in {0x00,0x03} # extension node can have child branch or hash nodes
        stack.append(["extension", (pathnibbleslen, pathnibbles), []])
        nibbledepth+=pathnibbleslen
      elif node_type == 0x02:  # leaf node
        """
  elif node_type == 0x02:  # leaf node
    if verbose: print("parse_Leaf_Node", bytes_, idx, depth, storage_flag)
    assert depth<65
    if storage_flag==0:
      idx, accounttype = parse_Bytes(bytes_, idx, 1)
      assert accounttype in {0x00,0x01}
      if accounttype == 0x00:
        idx, address = parse_Bytes(bytes_,idx,20)
        idx, balance = parse_Integer(bytes_,idx,256)
        idx, nonce = parse_Integer(bytes_,idx,256)
        return idx, ("leaf", address.hex(), balance, nonce)
      elif accounttype == 0x01:
        idx, address = parse_Bytes(bytes_,idx,20)
        idx, balance = parse_Integer(bytes_,idx,256)
        idx, nonce = parse_Integer(bytes_,idx,256)
        idx, bytecodetype = parse_Bytes(bytes_, idx, 1)
        assert bytecodetype in {0x00,0x01}
        if bytecodetype == 0x00:
          idx, codelen = parse_Integer(bytes_,idx,256)
          idx, code = parse_Bytes(bytes_,idx,codelen)
          idx, storage = parse_Node(bytes_,idx,0,1)
          return idx, ("leaf", address.hex(), balance, nonce, code.hex(), storage)
        elif bytecodetype == 0x01:
          idx, codelen = parse_Integer(bytes_,idx,256)
          idx, codehash = parse_Bytes(bytes_,idx,32)
          idx, storage = parse_Node(bytes_,idx,0,1)
          return idx, ("leaf", address.hex(), balance, nonce, (codelen, codehash.hex()), storage)
    else:
      idx, key = parse_Bytes(bytes_,idx,32)
      idx, value = parse_Bytes(bytes_,idx,32)
      return idx, ("leaf", key.hex(), value.hex())
        """
        if verbose: print("leaf 1", idx, nibbledepth, storage_flag)
        assert nibbledepth<65
        if storage_flag==0:
          idx, accounttype = parse_Bytes(bytes_, idx, 1)
          assert accounttype in {0x00,0x01}
          if accounttype == 0x00: # externally owned account
            idx, address = parse_Bytes(bytes_,idx,20)
            idx, balance = parse_Integer(bytes_,idx,256)
            idx, nonce = parse_Integer(bytes_,idx,256)
            return idx, ("leaf", address, balance, nonce)
          elif accounttype == 0x01: # contract account
            idx, address = parse_Bytes(bytes_,idx,20)
            idx, balance = parse_Integer(bytes_,idx,256)
            idx, nonce = parse_Integer(bytes_,idx,256)
            idx, bytecodetype = parse_Bytes(bytes_, idx, 1)
            assert bytecodetype in {0x00,0x01}
            if bytecodetype == 0x00:
              idx, codelen = parse_Integer(bytes_,idx,256)
              idx, code = parse_Bytes(bytes_,idx,codelen)
              stack.append(("leaf", address.hex(), balance, nonce, code.hex(), []))
            elif bytecodetype == 0x01:
              idx, codelen = parse_Integer(bytes_,idx,256)
              idx, codehash = parse_Bytes(bytes_,idx,32)
              stack.append(("leaf", address.hex(), balance, nonce, (codelen, codehash.hex()), []))
            # finally parse storage tree
            storage_flag = 1
            nibbledepth = 0
            stack.append(["parent_of_root",[]])
        else:
          idx, key = parse_Bytes(bytes_,idx,32)
          idx, value = parse_Bytes(bytes_,idx,32)
          stack.append(["leaf", key.hex(), value.hex()])
        """
        if storage_flag==0:
          idx, accounttype = parse_Bytes(bytes_, idx, 1)
          assert accounttype in {0x00,0x01}
          if accounttype == 0x00:
            idx, pathnibbles = parse_Nibbles(bytes_,idx,64-nibbledepth)
            idx, address = parse_Bytes(bytes_,idx,20)
            idx, balance = parse_Bytes(bytes_,idx,32)
            idx, nonce = parse_Bytes(bytes_,idx,32)
            stack.append(["leaf", (64-nibbledepth, pathnibbles), address, balance, nonce, None, None])
          elif accounttype == 0x01:
            idx, pathnibbles = parse_Nibbles(bytes_,idx,64-nibbledepth)
            idx, address = parse_Bytes(bytes_,idx,20)
            idx, balance = parse_Bytes(bytes_,idx,32)
            idx, nonce = parse_Bytes(bytes_,idx,32)
            idx, codelen = parse_Bytes(bytes_,idx,4)
            codelen = int.from_bytes(codelen, byteorder="big")
            idx, code = parse_Bytes(bytes_,idx,codelen)
            # must parse storage tree
            storage_flag = 1
            stack.append(["leaf", (64-nibbledepth, pathnibbles), address, balance, nonce, code, []])
            nibbledepth = 0
            stack.append(["parent_of_root",[]])
          elif accounttype == 0x02:
            idx, pathnibbles = parse_Nibbles(bytes_,idx,64-nibbledepth)
            idx, address = parse_Bytes(bytes_,idx,20)
            idx, balance = parse_Bytes(bytes_,idx,32)
            idx, nonce = parse_Bytes(bytes_,idx,32)
            idx, codehash = parse_Bytes(bytes_,idx,32)
            idx, codelen = parse_Bytes(bytes_,idx,4)
            codelen = int.from_bytes(codelen, byteorder="big")
            # must parse storage tree
            storage_flag = 1
            stack.append(["leaf", (64-nibbledepth, pathnibbles), address, balance, nonce, codehash, codelen, []])
            nibbledepth = 0
            stack.append(["parent_of_root",[]])
        else:
          idx, pathnibbles = parse_Nibbles(bytes_,idx,64-nibbledepth)
          idx, key = parse_Bytes(bytes_,idx,32)
          idx, value = parse_Bytes(bytes_,idx,32)
          nibbledepth = 64
          stack.append(["leaf", (64-nibbledepth,pathnibbles), key, value])
        """
      elif node_type == 0x03:  # hash node
        if verbose: print("hash 1")
        assert nibbledepth<65
        idx, hash_ = parse_Bytes(bytes_, idx, 32)
        #nibbledepth+=1
        stack.append(["hash", hash_])
      else:
        print("ERROR, something strange happend")


      # pop stack items if current_node is
      #   hash, branch with 16 children, extension with child, account leaf with storage figured out, storage leaf, or parent of root
      while len(stack)>1:
        if verbose: print("while 2")
        if stack[-1][0] == "hash":
          if verbose: print("hash 2")
          stack[-2][-1].append(stack.pop())
        elif stack[-1][0] == "branch":
          if verbose: print("branch node 2")
          # if have 16 children, pop, otherwise break
          bitmaskstr = stack[-1][1]
          for bit in bitmaskstr[len(stack[-1][-1]):]:
            if bit=="0":
              stack[-1][-1].append(None)
            else: 
              break
          # check if we filled all 16 children
          if len(stack[-1][-1])==16:
            stack[-2][-1].append(stack.pop())
          else:
            break
        elif stack[-1][0] == "extension":
          if stack[-1][-1]:
            stack[-2][-1].append(stack.pop())
          else:
            break
        elif stack[-1][0] == "leaf":
          if verbose: print("leaf 2")
          if len(stack[-1])>3:
            storage_flag = 0
          if stack[-1][-1] != []:
            stack[-2][-1].append(stack.pop())
        elif stack[-1][0] == "parent_of_root":
          if verbose: print("parent_of_root 2")
          if stack[-1][-1]:
            parent_of_root = stack.pop()
            stack[-1][-1].append(parent_of_root[-1])
          else:
            break


        if len(stack)==1:
          # done parsing this tree
          tree_roots.append(stack.pop()[-1])
          break

  #print(tree_roots)
  return tree_roots




########################################
# No Stack, Just traverse and build tree

# similar to above algorithm, but once find node, attach to parent node, then walking up stack is just traversing to parent
# but need parent pointer

#TODO



