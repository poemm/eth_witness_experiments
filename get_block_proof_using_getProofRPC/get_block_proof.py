import sys
import pprint
import json
import sha3     # pip install pysha3


import requests
head = {"Content-type": "application/json"}



verbose = 0
debug = 0



# this function dumps raw data, which will be needed to create a block witness for stateless block execution
# node: don't know about completeness, maybe there is something missing (eg BLOCKHASH must be handled somehow)
# note: don't know about witness minimalness, since some merkle paths not needed (eg tx creates leaf then deletes leaf)
def getWitnessForBlock(blocknum):


  # STEP 1: eth_getBlockByNumber to get block
  payload = {
    'method': 'eth_getBlockByNumber',
    'params': [hex(blocknum), True],
    'id': 1
  }
  response = requests.post("http://localhost:8545", data=json.dumps(payload), headers=head)
  #print(response.text)
  try:
    block = response.json()['result']
  except:
    print("ERROR with eth_getBlockByNumber, response:",response.json())
    print(response.text)
    sys.exit("ERROR parsing eth_getCode, stopping.")
  print("BLOCK:\n",block)
  if verbose>1: print("gasUsed: {}".format(block['gasUsed']))
  if verbose>1: print("tx count: {}".format(len(block['transactions'])))


  # STEP 2: 
  # for each transaction in block
  #   add from address to some_addresses
  #   if tx 'to' is empty (i.e. deploy code):
  #     add tx hash to list txs_to_trace
  #   otherwise:
  #     eth_getCode of 'to' address at blocknum
  #     if has code, then add tx hash to list txs_to_trace
  #     otherwise, add to addresses to some_addresses

  txs_to_trace = []
  some_addresses = set()

  for idx, tx in enumerate(block['transactions']):
    if verbose>1: print("transaction",idx,":",tx)
    some_addresses.add(tx['from'])
    some_addresses.add(tx['to'])
    if tx['to'] is None:
      if verbose>1: print("deploy contract")
      txs_to_trace.append(tx['hash'])
    else:
      payload = {
        'method': 'eth_getCode',
        'params': [tx['to'], hex(blocknum)],
        'id': 1
      }
      if verbose>1: print("getting code with RPC call",payload)
      response = requests.post("http://localhost:8545", data=json.dumps(payload), headers=head)
      try:
        code = response.json()['result']
      except:
        print("ERROR with eth_getCode, response:",response.json())
        print(response.text)
        sys.exit("ERROR parsing eth_getCode, stopping.")
      if len(code) > 2:
        if verbose>1: print("tx", idx, tx, "has code", code)
        txs_to_trace.append(tx['hash'])

  if verbose>1: print("txs_to_trace",txs_to_trace)
  if verbose>1: print("some_accounts",some_accounts)


  # STEP 3:
  # for each tx:
  #   get witness data

  witness_data_by_address = {}
  for txhash in txs_to_trace:
    # STEP 3.1: debug_traceTransaction on tx and tracer script
    if verbose>1: print("getting trace for tx",txhash)
    # curl --header "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"debug_traceTransactionWitness","params":["0x6c919fd479697e59df670501c8cce85e1bcbe7a20af193baba8acb7ab6a59e30", {"tracer": "{ data: [], step: function(log) { if (log.op.toString() == \"SSTORE\" || log.op.toString() == \"SLOAD\") { var location = log.stack.peek(0); this.data.push( {op: log.op.toString(), location: location.toString(16), contract: toHex(log.contract.getAddress())} ); } }, fault: function() { return \"error\"; }, result: function() { return this.data; } }"}],"id":5}' http://localhost:8545
    # debug_traceTransaction script to get all touched storage locations for a tx

    # The tracer script copied from: https://github.com/ethereum/go-ethereum/blob/0218d7001d2a566b35072ee21b9f84f6b2711bbe/eth/tracers/internal/tracers/prestate_tracer.js
    # but I added some stuff, see comments
    tracer_script = """
    // Copyright 2017 The go-ethereum Authors
    // This file is part of the go-ethereum library.
    //
    // The go-ethereum library is free software: you can redistribute it and/or modify
    // it under the terms of the GNU Lesser General Public License as published by
    // the Free Software Foundation, either version 3 of the License, or
    // (at your option) any later version.
    //
    // The go-ethereum library is distributed in the hope that it will be useful,
    // but WITHOUT ANY WARRANTY; without even the implied warranty of
    // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    // GNU Lesser General Public License for more details.
    //
    // You should have received a copy of the GNU Lesser General Public License
    // along with the go-ethereum library. If not, see <http://www.gnu.org/licenses/>.
    // prestateTracer outputs sufficient information to create a local execution of
    // the transaction from a custom assembled genesis block.
    {
	// prestate is the genesis that we're building.
	prestate: null,
	// lookupAccount injects the specified account into the prestate object.
	lookupAccount: function(addr, db){
		var acc = toHex(addr);
		if (this.prestate[acc] === undefined) {
			this.prestate[acc] = {
				balance: '0x' + db.getBalance(addr).toString(16),
				nonce:   db.getNonce(addr),
				code:    toHex(db.getCode(addr)),
				storage: {}
			};
		}
	},
	// lookupStorage injects the specified storage entry of the given account into
	// the prestate object.
	lookupStorage: function(addr, key, db){
		var acc = toHex(addr);
		var idx = toHex(key);
		if (this.prestate[acc].storage[idx] === undefined) {
			this.prestate[acc].storage[idx] = toHex(db.getState(addr, key));
		}
	},
	// result is invoked when all the opcodes have been iterated over and returns
	// the final result of the tracing.
	result: function(ctx, db) {
		// At this point, we need to deduct the 'value' from the
		// outer transaction, and move it back to the origin
		this.lookupAccount(ctx.from, db);
		this.lookupAccount(ctx.to, db); // paul added this
		var fromBal = bigInt(this.prestate[toHex(ctx.from)].balance.slice(2), 16);
		var toBal   = bigInt(this.prestate[toHex(ctx.to)].balance.slice(2), 16);
		this.prestate[toHex(ctx.to)].balance   = '0x'+toBal.subtract(ctx.value).toString(16);
		this.prestate[toHex(ctx.from)].balance = '0x'+fromBal.add(ctx.value).toString(16);
		// Decrement the caller's nonce, and remove empty create targets
		this.prestate[toHex(ctx.from)].nonce--;
		if (ctx.type == 'CREATE') {
			// We can blibdly delete the contract prestate, as any existing state would
			// have caused the transaction to be rejected as invalid in the first place.
			delete this.prestate[toHex(ctx.to)];
		}
		// Return the assembled allocations (prestate)
		return this.prestate;
	},
	// step is invoked for every opcode that the VM executes.
	step: function(log, db) {
		// Add the current account if we just started tracing
		if (this.prestate === null){
			this.prestate = {};
			// Balance will potentially be wrong here, since this will include the value
			// sent along with the message. We fix that in 'result()'.
			this.lookupAccount(log.contract.getAddress(), db);
		}
		// Whenever new state is accessed, add it to the prestate
		switch (log.op.toString()) {
			case 'EXTCODECOPY': case 'EXTCODESIZE': case 'BALANCE':
				this.lookupAccount(toAddress(log.stack.peek(0).toString(16)), db);
				break;
			case 'CREATE':
				var from = log.contract.getAddress();
				this.lookupAccount(toContract(from, db.getNonce(from)), db);
				break;
			case 'CREATE2':
				var from = log.contract.getAddress();
				// stack: salt, size, offset, endowment
				var offset = log.stack.peek(1).valueOf()
				var size = log.stack.peek(2).valueOf()
				var end = offset + size
				this.lookupAccount(toContract2(from, log.stack.peek(3).toString(16), log.memory.slice(offset, end)), db);
				break;
			case 'CALL': case 'CALLCODE': case 'DELEGATECALL': case 'STATICCALL':
				this.lookupAccount(toAddress(log.stack.peek(1).toString(16)), db);
				break;
			case 'SSTORE':case 'SLOAD':
				this.lookupStorage(log.contract.getAddress(), toWord(log.stack.peek(0).toString(16)), db);
				break;
		}
	},
	// fault is invoked when the actual execution of an opcode fails.
	fault: function(log, db) {}
    }
    """

    payload = {
      'method': 'debug_traceTransaction',
      'params': [txhash, {'tracer': tracer_script}],
      'id': 1
    }
    response = requests.post("http://localhost:8545", data=json.dumps(payload), headers=head)
    #print(response.text)
    try:
      accounts_touched = response.json()['result']
      # accounts_touched is a dict of values: '0x<acct_addy>': {'balance': '0x<number of wei>', 'nonce': <integer>, 'code': '0x<code or nothing>', 'storage': {<dict of 0x<key>:0x<value>>}}
      print("\ntrace for txhash",txhash,"\n",accounts_touched)
    except:
      print("ERROR parsing debug_traceTransaction response!", sys.exc_info()[0])
      print(response.text)
      sys.exit("ERROR parsing debug_traceTransaction response. stopping.")
    
    # STEP 3.2:
    #   for each touched location
    #     append to dict touches_by_contract(address:{'op': touch['op'], 'location': touch['location']})
    #     if there is a address+location collision, SLOAD overwrites SSTORE
    # i.e. sort traces into dict, indexed by account address
    for addy in accounts_touched:
      if addy in witness_data_by_address:
        for storage_loc in accounts_touched[addy]['storage']:
          #if storage_loc not in witness_data_by_address[addy]['storage']:
          witness_data_by_address[addy]['storage'][storage_loc] = accounts_touched[addy]['storage'][storage_loc]
      else:
        witness_data_by_address[addy] = accounts_touched[addy]

  # STEP 4: get block reward beneficiaries
  # mining reward recipient
  some_addresses.add(block['miner'])
  unclesheaders = []
  # uncle reward recipients
  for idx,unclehash in enumerate(block['uncles']):
    payload = {
      'method': 'eth_getUncleByBlockHashAndIndex',
      'params': [block['hash'], hex(idx)],
      'id': 1
    }
    response = requests.post("http://localhost:8545", data=json.dumps(payload), headers=head)
    #print("proofs for contract {}".format(contract))
    #print(response.text)
    try:
      uncle = response.json()['result']
      print("\nuncleheader:",uncle)
    except:
      print("ERROR parsing eth_getUncle... response!", sys.exc_info()[0])
      print(response.text)
      sys.exit("ERROR parsing eth_getUncle... response. stopping.")
    some_addresses.add(uncle['miner'])
    uncleheaders.append(uncle)


  # STEP 5: get merkle proofs
  #   for address in witness_data_by_address:
  #     eth_getProof for address
  #     for each location in address's storage
  #       eth_getProof for location
  for addy in some_addresses:
    if addy not in witness_data_by_address:
      witness_data_by_address[addy] = {}
  for address in witness_data_by_address:
    if 'storage' in witness_data_by_address[address]:
      keys_touched = [k for k in witness_data_by_address[address]['storage']]
    else:
      keys_touched = []
    # curl --header "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_getProof","params":["0xea38eaa3c86c8f9b751533ba2e562deb9acded40",["0x52419b386ce9c40b298ef864f6f9232f796eabab80a3f81a2a24d8e1018caa14","0xc4cba991f74e7ac769beca22e8f2aeca08a2ba638096cc15d357d1ca5f87a8e7"],"0x6b23ea"],"id":1}'  http://localhost:8545
    payload = {
      'method': 'eth_getProof',
      'params': [address, keys_touched, hex(blocknum-1)],   # note: subtract 1 from blocknum, since want pre-state
      'id': 1
    }
    response = requests.post("http://localhost:8545", data=json.dumps(payload), headers=head)
    #print("proofs for contract {}".format(contract))
    #print(response.text)
    try:
      proof = response.json()['result']
      print("\nproof for address",address,"\n",proof)
    except:
      print("ERROR parsing eth_getProof response!", sys.exc_info()[0])
      print(response.text)
      sys.exit("ERROR parsing eth_getProof response. stopping.")
    witness_data_by_address[address]['proof'] = proof


  return witness_data_by_address










############################################################################################
############################################################################################
## The following code is to convert the dumped block witness data into a more useful form ##
############################################################################################
############################################################################################


#######
# Utils

def keccak256(bytes_):
  return sha3.keccak_256(bytes_).digest()

def parse_json_file(filename):
  with open(filename, 'r') as f:
    data = f.read()
    f.close()
    return json.loads(data)
  return None



########################
# Yellowpaper Appendix B
# RLP inverse, needed to read geth proofs

def RLP_inv(b):
  if verbose: print("RLP_inv(",b.hex(),")")
  if len(b)==0:
    return bytearray([0x80])
  if b[0]<0xc0 : # bytes
    return R_b_inv(b)
  else:
    return R_l_inv(b)

def R_b_inv(b):
  if verbose: print("R_b_inv(",b.hex(),")")
  if len(b)==1 and b[0]<0x80:
    return b #bytearray([b[0]-0x80])
  elif b[0]<=0xb7:
    return b[1:1+b[0]-0x80]
  else:
    len_BElenx = b[0] - 183
    lenx = BE_inv(b[1:len_BElenx+1]) #TODO lenx unused
    return b[len_BElenx+1:len_BElenx+1+lenx]

def BE_inv(b):
  if verbose: print("BE_inv(",b.hex(),")")
  x=0
  for n in range(len(b)):
    #x+=b[n]*2**(len(b)-1-n)
    x+=b[n]*2**(8*(len(b)-1-n))
    #print("debug in BE_inv",x,b[n],len(b)-1-n)
  return x


def R_l_inv(b):
  if verbose: print("R_l_inv(",b.hex(),")")
  if b[0] <= 0xf7:
    lensx = b[0]-0xc0
    sx = b[1:1+lensx]
  else:
    len_lensx = b[0] - 247
    lensx = BE_inv(b[1:1+len_lensx])
    sx = b[1+len_lensx : 1+len_lensx+lensx]
  return s_inv(sx)

def s_inv(b):
  if verbose: print("s_inv(",b.hex(),")")
  x=[]
  i=0
  len_=len(b)
  while i<len_:
    len_cur, len_len_cur = decode_length(b[i:])
    x += [RLP_inv(b[i:i+len_len_cur+len_cur])]
    i += len_cur + len_len_cur
    if debug: print("  s_inv() returning",x)
  if debug: print("  s_inv() returning",x)
  return x

# this is a helper function not described in the spec
# but the spec does not discuss the inverse to he RLP function, so never has the opportunity to discuss this
# returns the length of an encoded rlp object
def decode_length(b):
  if verbose: print("length_inv(",b.hex(),")")
  if len(b)==0:
    return 0,0 # TODO: this may be an error
  length_length=0
  first_rlp_byte = b[0]
  if first_rlp_byte < 0x80:
    rlp_length=1
    return rlp_length, length_length
  elif first_rlp_byte <= 0xb7:
    rlp_length = first_rlp_byte - 0x80
  elif first_rlp_byte <= 0xbf:
    length_length = first_rlp_byte - 0xb7
    rlp_length = BE_inv(b[1:1+length_length])
  elif first_rlp_byte <= 0xf7:
    rlp_length = first_rlp_byte - 0xc0
  elif first_rlp_byte <= 0xbf:
    length_length = first_rlp_byte - 0xb7
    rlp_length = BE_inv(b[1:1+length_length])
  return rlp_length, 1+length_length


# Appendix C

def HP_inv(bytes_):
  nibbles = ""
  odd_length = (bytes_[0]>>4)%2==1 #sixth lowest bit
  t = (bytes_[0]>>5)%2!=0 #fifth lowest bit
  if odd_length:
    nibbles += bytes_[0:1].hex()[1]
  for b in bytes_[1:]:
    nibbles += bytes([b]).hex()
  return nibbles, t

"""

In block 10389730, the prestate for account 0x8a91c9a16cd62693649d80afa85a09dbbdcb8508 storage location 0x611b1497668bd572905cf80563a332e3f35eabc62d7194de0ffb000459b4c6d0 has geth proof which includes a node encoded as RLP: f84f80a01de39cd769836b28d87550d4ac3b8d339a46c7e802735ace42605a6acefe0e6b8080de9c31a86aab069d130e7f183a8dfb818845b43273f826fa01a2d253cb1d03808080808080808080808080.

curl --header "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_getProof","params":["0x8a91c9a16cd62693649d80afa85a09dbbdcb8508",["0x611b1497668bd572905cf80563a332e3f35eabc62d7194de0ffb000459b4c6d0"],"0x9e88e1"],"id":1}'  http://localhost:8545

After decoding this RLP, it resembles a branch node, but the fifth child is strange.

f8 - list with length of lenth is 1 byte
 4f - bytelength of list is 79
  80
  a0
    1de39cd769836b28d87550d4ac3b8d339a46c7e802735ace42605a6acefe0e6b
  80
  80
  de - list of bytelength 30
   9c - bytes of length 28
    31a86aab069d130e7f183a8dfb818845b43273f826fa01a2d253cb1d
   03
  80
  80
  80808080808080808080.


f8 - list and length of length is 1
 4f - list has bytelength 79
  80 - empty
  a0 - length 32
   1de39cd769836b28d87550d4ac3b8d339a46c7e802735ace42605a6acefe0e6b
  80
  80
  de - list with bytelength 30
   9c - bytes of length 28
    31a86aab069d130e7f183a8dfb818845b43273f826fa01a2d253cb1d
   03
  80
  80
  80
  808080808080808080

f84f
 80
 a0 1de39cd769836b28d87550d4ac3b8d339a46c7e802735ace42605a6acefe0e6b
 80
 80
 de 9c31a86aab069d130e7f183a8dfb818845b43273f826fa01a2d253cb1d 03
 80
 8080808080808080808080


node just before the branch it is in
e4 - list of bytelength 32
 82 - bytearray of bytelength 2
  00de - hex prefix of 2 nibble extension
 a0 - bytearray of bytelength 32
  36f97d0f0bba9aa6ed26d26b52b2d34687141307ef9df664b29fd66109fb4f91
"""


##################################################
# functions to convert geth proofs to nested nodes


root_node = None

def merge_path_witness_to_witness(path_node, witness_node):
  #print()
  #print("merge_path_witness_to_witness",path_node,witness_node)
  #print("merge_path_witness_to_witness")
  #print(len(witness_node))
  #print("merge_path_witness_to_witness")
  #print("path_node",path_node)
  #print("witness_node")
  #pprint.pprint(witness_node,width=300)
  #print("merge_path_witness_to_witness",witness_node)
  #pprint.pprint(path_node,width=300)
  if witness_node[0]=="branch": # branch node
    if path_node[0]!="branch": # branch node
      print("ERROR BRANCH NODE!!!!!!!!!")
      print("path_node",path_node)
      print("witness_node",witness_node)
      print("ERROR BRANCH NODE!!!!!!!!!")
      sys.exit(1)
    # get child position of path branch
    idx = []
    for i,c in enumerate(path_node):
      if c and c[0] in {"branch","extension","leaf"}:
        idx = [i]
        break
    if idx:
      idx = idx[0]
      #print("idx",idx)
      if witness_node[idx] and witness_node[idx][0]!="hash":
        merge_path_witness_to_witness(path_node[idx], witness_node[idx])
      else:
        witness_node[idx] = path_node[idx]
  elif witness_node[0]=="extension":
    if path_node[0]!="extension":
      print("ERROR EXTENSION NODE!!!!!!!!!")
      sys.exit(1)
    print("HEY EXTENSION!!!!!!!!!")
    #pprint.pprint(path_node,width=300)
    #print(path_node)
    #print(witness_node)
    if witness_node[2][0]!="hash":
      merge_path_witness_to_witness(path_node[2], witness_node[2])
    else:
      witness_node[2] = path_node[2]
    #merge_path_witness_to_witness(path_node[2], witness_node[2])
  elif witness_node[0]=="leaf":
    if path_node[0]!="leaf":
      print("ERROR LEAF NODE!!!!!!!!!")
      sys.exit(1)
    # collision with an existing leaf, happens when a proof-of-exclusion pulled this leaf in
    # add replace it with this updated one, since contract leaf might have to add code or storage
    if len(witness_node)>2:
      witness_node.append(path_node[3:])


def merge_path_proofs(witnesses):
  #print("merge_path_proofs(",witnesses,")")
  if not witnesses:
    return witnesses
  root = None
  idx = 0
  for addy in witnesses:
    print()
    print(idx)
    idx+=1
    if root==None:
      root = witnesses[addy]
      global root_node
      root_node = root
      continue
    #print("root_node")
    #pprint.pprint(root_node)
    path_root = witnesses[addy]
    #print("__________________________________________________________________________________")
    #print("inserting path")
    #pprint.pprint(path_root)
    #print("addy",addy)
    #path_hex = keccak256(bytes.fromhex(addy[2:]))
    merge_path_witness_to_witness(path_root, root)
  return root

def parse_geth_proof_path(geth_path_proof,address_or_key):
  print("parse_geth_proof_path(",geth_path_proof,address_or_key,")")
  prev_node = None
  root_node = None
  prev_child_idx = None
  #prev_branch = None
  #prev_branch_idx = None
  if geth_path_proof == []:
    node = []
  for i in range(len(geth_path_proof)):
    print()
    print(i)
    nodeRLP = geth_path_proof[i]
    nodeRLPhex = nodeRLP[2:]
    nodeRLPbytes = bytes.fromhex(nodeRLPhex)
    nodehash = keccak256(nodeRLPbytes)
    print("nodehash",nodehash.hex())
    nodedecoded = RLP_inv(nodeRLPbytes)

    if len(nodedecoded)==17: # branch
      node = ["branch"]
      #print("address",address_or_key)
      #print("geth_path_proof",geth_path_proof)
      #print("nodeRLPhex",nodeRLPhex)
      #print("nodedecoded",nodedecoded)
      #print("nodehash",nodehash.hex())
      for i in range(16):
        print(i,nodedecoded[i])
        print(i,nodedecoded[i].hex())
        if nodedecoded[i]:
          node.append(["hash",nodedecoded[i].hex()])
        else:
          node.append("")
    elif len(nodedecoded)==2: # extension or leaf
      #print()
      #print(nodeRLPhex)
      #print(nodedecoded)
      #nodedecoded = RLP_inv(nodedecoded)
      #print(nodedecoded)
      nibbles,flag = HP_inv(nodedecoded[0])
      #print(nibbles,flag)
      if not flag: # extension
        #print("BUILDING EXTENSION")
        childhash = nodedecoded[1]
        #print(nibbles,flag,childhash)
        node = ["extension",(len(nibbles),nibbles),["hash",childhash.hex()]]
        #print(node)
      else: # leaf
        leafdata = RLP_inv(nodedecoded[1])
        if type(leafdata)==bytes:
          leafdata = [leafdata]
        node = ["leaf",address_or_key] + leafdata

    if root_node == None:
      root_node = node
    else: # nest this node inside prev_node
      if prev_node[0]=="branch": # parent is branch
        #print("comparing branch",nodehash.hex(),prev_node)
        for i in range(len(prev_node)):
          if prev_node[i] and prev_node[i][1]==nodehash.hex():
            #print("replacing node hash", i)
            prev_node[i] = node
            break
        #prev_branch = prev_node
        #prev_branch_idx = i
        prev_child_idx = i

      else: # parent is extension
        #print("parent is EXTENSION")
        #print(prev_node)
        prev_node[2] = node
        prev_child_idx = 2

    prev_node = node
  #print("returning_from_parse_geth_proof_path() with root_node")
  #pprint.pprint(root_node)
  #return root_node, prev_branch, prev_branch_idx
  #return root_node, prev_node, prev_child_idx
  return root_node, node

"""
an extension node in 10377970.json
e2 - list of bytelength 34
 1a - first item is byte 1a
 a0 - second item is bytes of bytelength 32
   2bd7a288088104932e9cea940aa02816a21267cfaa94ddd07c928a85d20381de
"""


def parse_geth_dump_into_witness(dump):
  if verbose: print("parse_geth_dump_into_witness address(",dump,")")
  #dump = parse_json_file(filename)

  # For each geth accountProof, create witness path, then merge these paths. Similarly for each geth storageProof.
  account_witness_roots = {}
  for address in dump:
    print()
    print("parse_geth_dump_into_witness address",address)
    # each account in dump looks like:
    #   'balance': '0x1', 'nonce': 1, 'code':'0x...', 'storage': {'0x<key>':'0x<val>', ...}, 'proof': {'address': '0x<address>', 'accountProof': ['0x<blah>','0x<blah>',...], 'balance':'0x<blah>', 'codeHash':'0x<blah>', 'nonce': '0x<blah>', 'storageHash':'0x<blah>', 'storageProof': [{'key':'0x<blah>', 'value':'0x<blah>', 'proof':['0x<blah>','0x<blah>',...]}, {'key': ...}] }
    # or
    #   'proof': ...
    # parse path to account
    #account_witness_roots[address], branch_before_leaf, branch_idx_of_leaf = parse_geth_proof_path(dump[address]['proof']['accountProof'],address)
    account_witness_roots[address], bottom_node = parse_geth_proof_path(dump[address]['proof']['accountProof'],address)
    #account = branch_before_leaf[branck_idx_of_leaf]
    #print("account",account)
    #prefix = RLP_inv(account[0])
    #print("account[0]",prefix)
    #node = RLP_inv(account[1])
    #print("account[1]",node)
    # parse storage proofs
    storage_leaf_witness_roots = {}
    if bottom_node[0]=="leaf":
      for storageProof in dump[address]['proof']['storageProof']:
        #print("parse_geth_dump_into_witness storageProof",storageProof['key'])
        #if '0x611b1497668bd572905cf80563a332e3f35eabc62d7194de0ffb000459b4c6d0'==storageProof['key']:
        #print("parse_geth_dump_into_witness storageProof",storageProof)
        #storage_leaf_witness_roots[storageProof['key']], storage_branch_before_leaf, storage_branch_idx_of_leaf = parse_geth_proof_path(storageProof['proof'],storageProof['key'])
        #print("okok",dump[address])
        storage_leaf_witness_roots[storageProof['key']], storage_bottom_node = parse_geth_proof_path(storageProof['proof'],storageProof['key'])
        if storage_bottom_node and storage_bottom_node[0]=="leaf":
          storage_bottom_node[2] = storage_bottom_node[2].hex()
        #storage_branch_before_leaf[storage_branch_idx_of_leaf] = ["leaf",storageProof['key'],storageProof['value']]
      # merge storage tree witness paths
      #print("proof",dump[address]['proof'])
      #print("balance",dump[address]['proof']['balance'],len(dump[address]['proof']['balance']))
      #balance = dump[address]['proof']['nonce'][2:]
      #if len(balance)%2:
      #  balance = '0'+balance
      #print("balance",balance)
      #leaf["balance"] = bytes.fromhex(balance)
      #leaf["nonce"] = bytes.fromhex(dump[address]['proof']['nonce'][2:])
      if dump[address]['proof']['codeHash'] == "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470" and dump[address]['proof']['storageHash'] == "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421": # externally-owned account
        account = [dump[address]['proof']['nonce'],
                   dump[address]['proof']['balance']
                  ]
      else:
        if storage_leaf_witness_roots:
          storage = merge_path_proofs(storage_leaf_witness_roots)
        else:
          storage = dump[address]['proof']['storageHash']
        code = dump[address]['proof']['codeHash'] # todo: need either code or codelen and codehash
        account = [dump[address]['proof']['nonce'],
                   dump[address]['proof']['balance'],
                   code,
                   storage
                  ]
      bottom_node[2:] = account[:]
      #branch_before_leaf[branch_idx_of_leaf] = account

  # merge paths for accountProofs
  witness_root = merge_path_proofs(account_witness_roots)

  return witness_root







if __name__ == "__main__":

  #START_BLOCK = 7021700
  START_BLOCK = int(sys.argv[1])

  for i in range(START_BLOCK, START_BLOCK+1):
    print("doing block {}...".format(i))
    witness = getWitnessForBlock(i)
    if verbose:
      with open(str(i)+'_dump.json', 'w') as fp:
        fp = open(str(i)+".dat","w")
        fp.write(str(witness))
        fp.close()
    witness_root = parse_geth_dump_into_witness(witness)
    #pprint.pprint(witness_root,width=300)
    with open(str(i)+'_witness.json', 'w') as fp:
      fp.write(json.dumps(parsed, indent=2))
      fp.close()
