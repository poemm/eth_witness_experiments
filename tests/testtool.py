import ethereum_spec
import yaml
import sys
sys.path.append('..')

# uncomment one parse_Block_Witness() and one gen_Block_Witness()
from parse_generate_spec import gen_Block_Witness
from parse_generate_spec import parse_Block_Witness
#from parse_alternative_implementations import parse_Block_Witness


# this flag should be set to zero when filling, otherwise it prints junk to the json file
verbose = 0


def parse_yaml_recursive_helper(node, storage_tree=False):
  if verbose: print("parse_yaml_recursive_helper(",node,storage_tree,")")
  if "hash" in node:
    hash_ = node["hash"][2:]
    return ("hash", hash_)
  elif "branch" in node:
    branch = node["branch"]
    children=[]
    for i in range(16):
      if branch[i]=="":
        children.append(None)
      else:
        children.append(parse_yaml_recursive_helper(branch[i],storage_tree))
    return "branch",children
  elif "leaf" in node:
    account = node["leaf"]
    if storage_tree==False:
      address = account[0][2:]
      #print(account[1][:2])
      if account[1][:2]=="0x":
        balance = int(account[1][2:],16)
      else:
        balance = int(account[1])
      if account[2][:2]=="0x":
        nonce = int(account[2][2:],16)
      else:
        nonce = int(account[2])
      if len(account)==3:
        return ("leaf", address, balance, nonce)
      elif len(account)==5:
        code = ""
        if type(account[3])==str:
          code = account[3][2:]
        elif len(account[3])==2:
          code = account[3][0],account[3][1][2:]
        state = parse_yaml_recursive_helper(account[4], storage_tree=True)
        return ("leaf", address, balance, nonce, code, state)
      else:
        print("ERROR unknown account")
        return None
    else: # storage_tree==True
      storageleaf = node["leaf"]
      key = storageleaf[0][2:]
      value = storageleaf[1][2:]
      return ("leaf",key,value)
  elif "storageleaf" in node:
    storageleaf = node["leaf"]
    pathnibbles = (storageleaf[0][0], storageleaf[0][1][2:])
    key = storageleaf[1][2:]
    value = storageleaf[2][2:]
    return ("storageleaf",pathnibbles,key,value)
  elif "extension" in node:
    extension = node["extension"]
    assert len(extension)==2
    pathlennibbles = (extension[0][0], extension[0][1][2:])
    child = parse_yaml_recursive_helper(extension[1],storage_tree)
    return ("extension", pathlennibbles, child)
  else:
    print("ERROR unknown node")

def parse_yaml(filename):
  stream = open(filename, 'r')
  docs = yaml.load_all(stream)
  witnesses = []
  for doc in docs:
    test_name = doc["test name"]
    test_types = doc["test type"]
    version = doc["version"]
    assert doc["version"]==1
    trees = []
    for t in doc["trees"]:
      tree = parse_yaml_recursive_helper(t)
      trees.append(tree)
    witnesses.append({"test name":test_name,"test types":test_types,"version":version,"trees":trees})
  return witnesses

def fill(filename):
  witnesses = parse_yaml(filename)
  print("[")
  for i,w in enumerate(witnesses):
    if i:
      print(" ,")
    trees = w["trees"]
    witness_internal_format = ["Ethereum 1x witness",("version", w["version"])] + [["tree",tree] for tree in trees]
    #print("witness_internal_format:",witness_internal_format)
    bytes_ = bytearray([])
    gen_Block_Witness(bytes_,witness_internal_format)
    print(" {")
    print("  \"test name\": \"" + w["test name"] + "\",")
    print("  \"test types\": \"" + w["test types"] + "\",")
    print("  \"witness\": \"0x" + bytes_.hex() + "\",")
    print("  \"root hashes\":[",end="")
    roothashes=[]
    for idx,tree in enumerate(trees):
      if idx != 0:
        print(",",end="")
      tree_root_hash = ethereum_spec.merkleize(tree,0,0)
      print("\"0x" + tree_root_hash.hex() + "\"",end="")
    print("]",end="")
    print(" }")
  print("]")




#####################################################################################
# test2sexpr
# inputs json test file, outputs s-expression (nested parentheses) format of the test

def test2sexpr_recursive_helper(node, indent):
  if verbose: print("test2sexpr_recursive_helper", node, indent)
  #print("ok node[0]",node[0])
  print("\n" + " "*indent + "(" + node[0], end="")
  if node[0]=="hash":
    print(" 0x" + node[1] + ")", end="")
  elif node[0]=="extension":
    print("\n" + " "*(indent+1) + "(" + str(node[1][0]) + ", 0x" + node[1][1] + ")", end="")
    #print("node[2]",node[2])
    test2sexpr_recursive_helper(node[2], indent+1)
    print(" "*indent + ")", end="")
  elif node[0]=="branch":
    #print(" "*indent + "(" + node[0] + " ", end="")
    flag_just_had_blank = 1
    for i in range(16):
      #if not flag_just_had_blank:
      #  print()
      if node[1][i]:
        test2sexpr_recursive_helper(node[1][i], indent+1)
        flag_just_had_blank = 0
      else:
        if flag_just_had_blank:
          print("None", end="")
        else:
          print("\n"+" "*(indent+1) + "None", end="")
        flag_just_had_blank = 1
      if i<15:
        print(" ", end="")
    print(")", end="")
  elif node[0]=="leaf":
    #print("node",node)
    if len(node)==4:
      #print("\n" + " "*(indent+1) + "(" + node[1][0] + ", \"0x" + node[1][1] + "),")
      print("\n" + " "*(indent+1) + "0x" + node[1] + " ", end="")
      #print("\n" + " "*(indent+1) + "" + hex(node[2]) + " ", end="")
      #print("\n" + " "*(indent+1) + "" + hex(node[3]) + ")", end="")
      print("\n" + " "*(indent+1) + "" + str(node[2]) + " ", end="")
      print("\n" + " "*(indent+1) + "" + str(node[3]) + ")", end="")
    elif len(node)==6:
      #print("\n" + " "*(indent+1) + "(" + node[1][0] + ", \"0x" + node[1][1] + "),")
      print("\n" + " "*(indent+1) + "0x" + node[1] + " ", end="")
      #print("\n" + " "*(indent+1) + "" + hex(node[2]) + " ", end="")
      #print("\n" + " "*(indent+1) + "" + hex(node[3]) + ")", end="")
      print("\n" + " "*(indent+1) + "" + str(node[2]) + " ", end="")
      print("\n" + " "*(indent+1) + "" + str(node[3]) + " ", end="")
      if type(node[4])==str: # code is given, not codehash
        #print("okokokokokokokokokokokokokokokkokokokokokokok")
        print("\n" + " "*(indent+1) + "0x" + node[4], end="")
      else: # codehash is given
        print("\n" + " "*(indent+1) + "("+ str(node[4][0]) +", 0x" + node[4][1]+")", end="")
      test2sexpr_recursive_helper(node[5], indent+1)
      print(")\n")
    elif len(node)==3:
      #print("\n" + " "*(indent+1) + "(" + node[1][0] + ", \"0x" + node[1][1] + "),")
      print("\n" + " "*(indent+1) + "0x" + node[1] + " ", end="")
      print("\n" + " "*(indent+1) + "0x" + node[2] + ")", end="")
    else:
      print("ERROR printing leaf, don't know which type")
  #elif node[0]=="storage_leaf":
  #print("\n" + " "*indent + ")")

def test2sexpr(filename):
  if verbose: print("test2sexpr",filename)
  stream = open(filename, 'r')
  tests = yaml.load_all(stream)
  witnesses = []
  sexprs = []
  tests = next(tests)
  #print(tests)
  for t in tests:
    test_name = t["test name"]
    test_types = t["test types"]
    witness_bytes = bytearray.fromhex(t["witness"][2:])
    idx,trees = parse_Block_Witness(witness_bytes,0)
    print("\n\n"+t["test name"]+":")
    #print(trees)
    for tree in trees:
      test2sexpr_recursive_helper(tree,0)
    print()





#####################################################################################
# test
# inputs a json file, runs tests on the json file

def test_parse(witness_bytes,test_name):
  idx,trees=None,None
  idx,trees = parse_Block_Witness(witness_bytes,0)
  return idx,trees

def test_gen(witness_internal_format,expected_witness_bytes, test_name):
  #print("witness_internal_format",witness_internal_format)
  bytes_ = bytearray([])
  gen_Block_Witness(bytes_,witness_internal_format)
  if verbose: print("bytes_:\n",bytes_)
  if verbose: print("expected_witness_bytes:\n",expected_witness_bytes)
  if len(expected_witness_bytes) != len(bytes_):
    print("ERROR: doesn't match length",test_name)
    return False
  for i in range(len(bytes_)):
    if expected_witness_bytes[i] != bytes_[i]:
      print("ERROR: bytes don't match at index", i,test_name)
      return False
  return True
  
# executes the json test file
def test(filename):
  if verbose: print("test",filename)
  print("test",filename)
  stream = open(filename, 'r')
  tests = yaml.load_all(stream)
  tests = next(tests)
  #print(tests)
  passed = 1
  for t in tests:
    #print("t:",t)
    test_name = t["test name"]
    if verbose: print("\n\n"+t["test name"]+":")
    test_types = {tt.strip() for tt in t["test types"].split(',')}
    root_hashes = t["root hashes"]
    witness_bytes = bytearray.fromhex(t["witness"][2:])
    if "error" in test_types:
      if verbose: print("testing ERROR case")
      try:
        idx,trees = test_parse(witness_bytes, test_name)
        print(idx,trees)
      except AssertionError:
        if verbose: print("There was an AssertionError, as desired")
      except:
        print("ERROR with test case",test_name)
        passed = 0
    else:
      # test 1: parse
      try:
        idx,trees = test_parse(witness_bytes, test_name)
      except:
        print("ERROR with test case",test_name)
        passed = 0
        continue
      if trees==None:
        print("ERROR with test case",test_name)
        passed = 0
        continue
      # test w: check if match witness merkle hash
      for idx,tree in enumerate(trees):
        computed_hash = ethereum_spec.merkleize(tree,0,0)
        expected_hash = root_hashes[idx][2:]
        if computed_hash.hex() != expected_hash:
          print("hash mismatch", computed_hash.hex(), expected_hash)
      # generate and test if matches input
      witness_internal_format = ["Ethereum 1x witness",("version", 1)] + [["tree",tree] for tree in trees]
      ret = test_gen(witness_internal_format, witness_bytes, test_name)
      if not ret:
        print("ERROR with test case",test_name,"generated witness doesn't match input witness")
        passed = 0
  return passed







if __name__ == '__main__':

  if len(sys.argv)!=3:
    print("usage: python3 test_converter.py <operation> <test_name.yaml>")
    print("where <operation> is one of: fill, test, test2sexpr")

  if sys.argv[1] == "fill":
    fill(sys.argv[2])
  elif sys.argv[1] == "test2sexpr":
    test2sexpr(sys.argv[2])
  elif sys.argv[1] == "test":
    passed = test(sys.argv[2])
    if passed:
      print("passed")
    else:
      print("FAILED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


