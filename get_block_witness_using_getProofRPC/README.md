THIS IS A WORK IN PROGRESS! WORKS ON MANY BLOCKS, STILL WORKING THROUGH BUGS.

Need an ethereum node exposing rpc debug api (default should work locally, otherwise edit port, etc in the python script). Then execute:
```
python3 get_block_proof.py <blocknum>
```

Output is an ethereum block witness. The witness is in a json text format, for example the following witness for ethereum block 1.
```
 ["branch", [
   ["hash", "90dcaf88c40c7bbc95a912cbdde67c175767b31173df9ee4b0d733bfdd511c43"],
   ["hash", "babe369f6b12092f49181ae04ca173fb68d1a5456f18d20fa32cba73954052bd"],
   ["hash", "473ecf8a7e36a829e75039a3b055e51b8332cbf03324ab4af2066bbd6fbf0021"],
   ["hash", "bbda34753d7aa6c38e603f360244e8f59611921d9e1f128372fec0d586d4f9e0"],
   ["branch", [
     ["hash", "a9317a59365ca09cefcd384018696590afffc432e35a97e8f85aa48907bf3247"],
     ["hash", "e0bc229254ce7a6a736c3953e570ab18b4a7f5f2a9aa3c3057b5f17d250a1cad"],
     ["hash", "a2484ec8884dbe0cf24ece99d67df0d1fe78992d67cc777636a817cb2ef205aa"],
     ["hash", "12b78d4078c607747f06bb88bd08f839eaae0e3ac6854e5f65867d4f78abb84e"],
     ["hash", "359a51862df5462e4cd302f69cb338512f21eb37ce0791b9a562e72ec48b7dbf"],
     ["hash", "13f8d617b6a734da9235b6ac80bdd7aeaff6120c39aa223638d88f22d4ba4007"],
     ["hash", "02055c6400e0ec3440a8bb8fdfd7d6b6c57b7bf83e37d7e4e983d416fdd8314e"],
     ["hash", "4b1cca9eb3e47e805e7f4c80671a9fcd589fd6ddbe1790c3f3e177e8ede01b9e"],
     ["hash", "70c3815efb23b986018089e009a38e6238b8850b3efd33831913ca6fa9240249"],
     ["hash", "7084699d2e72a193fd75bb6108ae797b4661696eba2d631d521fc94acc7b3247"],
     ["hash", "b2b3cd9f1e46eb583a6185d9a96b4e80125e3d75e6191fdcf684892ef52935cb"],
     ["branch", [
       ["hash", "cc947d5ebb80600bad471f12c6ad5e4981e3525ecf8a2d982cc032536ae8b66d"],
       ["hash", "e80e52462e635a834e90e86ccf7673a6430384aac17004d626f4db831f0624bc"],
       ["hash", "59a8f11f60cb0a8488831f242da02944a26fd269d0608a44b8b873ded9e59e1b"],
       ["hash", "1ffb51e987e3cbd2e1dc1a64508d2e2b265477e21698b0d10fdf137f35027f40"],
       "",
       ["hash", "ce5077f49a13ff8199d0e77715fdd7bfd6364774effcd5499bd93cba54b3c644"],
       ["hash", "f5146783c048e66ce1a776ae990b4255e5fba458ece77fcb83ff6e91d6637a88"],
       ["hash", "6a0558b6c38852e985cf01c2156517c1c6a1e64c787a953c347825f050b236c6"],
       ["hash", "56b6e93958b99aaae158cc2329e71a1865ba6f39c67b096922c5cf3ed86b0ae5"],
       "",
       ["hash", "50d317a89a3405367d66668902f2c9f273a8d0d7d5d790dc516bca142f4a84af"],
       ["hash", "c72ca72750fdc1af3e6da5c7c5d82c54e4582f15b488a8aa1674058a99825dae"],
       ["hash", "e1a489df7b18cde818da6d38e235b026c2e61bcd3d34880b3ed0d67e0e4f0159"],
       ["hash", "b58d5062f2609fd2d68f00d14ab33fef2b373853877cf40bf64729e85b8fdc54"],
       "",
       ""]],
     ["hash", "34d9ff0fee6c929424e52268dedbc596d10786e909c5a68d6466c2aba17387ce"],
     ["hash", "7484d5e44b6ee6b10000708c37e035b42b818475620f9316beffc46531d1eebf"],
     ["hash", "30c8a283adccf2742272563cd3d6710c89ba21eac0118bf5310cfb231bcca77f"],
     ["hash", "4bae8558d2385b8d3bc6e6ede20bdbc5dbb0b5384c316ba8985682f88d2e506d"]]],
   ["hash", "a5f3f2f7542148c973977c8a1e154c4300fec92f755f7846f1b734d3ab1d90e7"],
   ["hash", "e823850f50bf72baae9d1733a36a444ab65d0a6faaba404f0583ce0ca4dad92d"],
   ["hash", "f7a00cbe7d4b30b11faea3ae61b7f1f2b315b61d9f6bd68bfe587ad0eeceb721"],
   ["hash", "7117ef9fc932f1a88e908eaead8565c19b5645dc9e5b1b6e841c5edbdfd71681"],
   ["hash", "69eb2de283f32c11f859d7bcf93da23990d3e662935ed4d6b39ce3673ec84472"],
   ["hash", "203d26456312bbc4da5cd293b75b840fc5045e493d6f904d180823ec22bfed8e"],
   ["hash", "9287b5c21f2254af4e64fca76acc5cd87399c7f1ede818db4326c98ce2dc2208"],
   ["hash", "6fc2d754e304c48ce6a517753c62b1a9c1d5925b89707486d7fc08919e0a94ec"],
   ["hash", "7b1c54f15e299bd58bdfef9741538c7828b5d7d11a489f9c20d052b3471df475"],
   ["hash", "51f9dd3739a927c89e357580a4c97b40234aa01ed3d5e0390dc982a7975880a0"],
   ["hash", "89d613f26159af43616fd9455bb461f4869bfede26f2130835ed067a8b967bfb"]]]

```
