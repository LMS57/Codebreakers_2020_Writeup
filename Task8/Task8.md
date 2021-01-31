# Codebreakers 2020 

# Task 8 - Rescue & Escape (Part 1) - (Reverse Engineering, Network Protocol Analysis)

### Points: 1700

### Description

```
The team is ready to go in to rescue the hostage. With your help they will be able to escape safely. There is no doubt the team will be detected once they find the hostage, so they will need help reaching the evacuation site. We need you to destroy all of the drones. Physically crashing the drone(s) at just the right moment will both disable any surveillance and distract the guards. This should give the team just enough time for escape to the evacuation site.

This will complicated...

We've done some more analysis looking at the strings and symbols in the drone binaries, and our technical team thinks the best approach is to send a 'restart' or 'poweroff' command to the power module in each of the drones. If the command is executed, the drone will lose power and drop out of the sky (and likely be destroyed).

But, it looks like the commands may not be executed when the drone is in-flight. Solving that will be the next step, but for now, focus on figuring out how to send a command to the power module, even if the command is rejected because the drone is in flight.

In this case, it would be best if you can determine a single message which can be sent to the controller so it can be be broadcast to all of the drones at exactly the same time. We dont know what other monitoring or safety mechanisms are in place if a drone malfunction is detected, and we cannot affort to disable only some of the drones.

Once you've determined the buffer that needs to be sent, upload it here We will use the './hello.py send_packet ' functionality to attempt to send the message to verify it
```

### Files

Same as Task 8

### Solution

For this challenge we just need the packet to successfully cause a power off if we have the ability to.

Before we go into looking at the `netsvc` binary, we are going to look at one more bit from the `router`. In particular we are going to check the flag byte, changing this to a `1` you may find that it does correspond to a reply packet, this is also lines up with some of the debug strings we can see in `handle_received_frame`. There is also this bit of code in the same area:

```assembly
        00104068 00  1c  00  12    and        mux ,mux ,#0xff
        0010406c 1f  00  00  71    cmp        mux ,#0x0
        00104070 e0  07  9f  1a    cset       mux ,ne
     	00104074 e0  77  01  39    strb       mux ,[sp, #is_routed ]
     	Disassembly:
     		bVar2 = -1 < (char)hdr_00->flags;
```

It appears that the variable `is_routed` is set to `0` or `1` based on if our flags are negative or greater than `0x7f`, we can also confirm this with the debug information by changing our flags on the peers connection from the last challenge to above 0x7f, with errors describing routing

![Routed_Debug](C:\Users\Logan Stratton\Desktop\codebreakers\Task8\Images\Routed_Debug.jpg)

Using the debug information we can go from `handle_received_frame` -> `forward_or_drop_frame` -> `routed_pkt_from_hdr` to hopefully learn about how routing works.

```c
if ((hdr->flags & 0x80) == 0) {
...
}
else {
  if (*remaining < 0xe) {
      ... //fail
  }
...
```

This code from `routed_pkt_from_hdr` shows that the header flag is once again checked, if it is set, `remaining` is checked against `0xe`, based on the value and the debug message below, we can determine that this is referring to the size of the header or packet remaining. This check is done with this assembly,

```assembly
        001076b0 e0  23  40  f9    ldr        hdr ,[sp, #local_30 ]
        001076b4 00  00  40  79    ldrh       hdr ,[hdr->flags ]
        001076b8 1f  34  00  71    cmp        hdr ,#0xd
```

This `remaining` was sent in as an argument as well and even though Ghidra is saying it is `hdr->flags` this is not the actual `hdr` ptr but `hdr` is what Ghidra called the register for this function frame, so get used to it. If we go back we can actually follow and see how the header size is called, this is back in `handle_received_frame` where a call to `pkt_hdr_frome_frame` is called. Based on this function it appears that remaining just refers to how many bytes are left in the packet and not just the header.

Back to `routed_pkt_from_hdr`, we have this code

```c
      uVar2 = ntohs((uint16_t)hdr[1]);
      *remaining = *remaining;
      *remaining = *remaining - 2;
      __stream = stderr;
      if (*remaining < uVar2) {
```

This refers back to the original `hdr` now and grabs 2 bytes from the second bytes address and compares this value to `remaining-2`, this is a clear sign that these two bytes are the responsible for describing the remaining size of the header vs content of a packet.

```c
      else {
        *remaining = *remaining - uVar2;
        *(pkt_hdr_t **)next = hdr + 2;
        *next = *next + uVar2;
        _Var1 = validate_treeroute_hdr((treeroute_hdr_t *)&hdr[2].msgtype,*next);
```

The above code will change the remaining value based on this header size, move next to the same value, and call `validate_tree_route_hdr`. Since hdr is at an offset we can use the `treeroute_hdr_t` structure along with the function math to fill in the rest of what the header will look like 

![treeroute_struct](C:\Users\Logan Stratton\Desktop\codebreakers\Task8\Images\treeroute_struct.jpg)

From the struct we have 4 bytes for a `path_code_n`, 1 byte for `addr_count` then `union_for_addrs`, and since the math in the function is checking this:

```c
    if ((anon_union_for_addrs *)next ==
        (anon_union_for_addrs *)((longlong)&thdr->addrs + (longlong)(int)(uint)thdr->addr_count* 2)
       ) {
      uVar1 = 1;
    }
```

We can see that based on the number of `addrs` each at a size of 2 bytes, out header can be variable length total.

With all this information our final packet header should look something like this then:

```
1 byte: flags
1 byte: message type
2 bytes: size remaining of header
1 byte: ? Questionable, not mentioned
4 bytes: path code
1 bytes: addr_count
addr_count*2 bytes: addrs
```

The 1 byte `?` could mess you up if you miss it but above when `validate_treeroute_hdr` is called `hdr[2]` is used as the address, you would need to look at the assembly to see that the value is added by 3 to get the address to work with. Meaning there is an extra byte hidden in there we need to account for.

Modifying the `make_peers` function from `peers.py` from the last task we can now attempt a routed message.

```
def make_routed_peers(nodetype, name):
    name = name.encode('utf-8')
    name = name[:31]
    name = name + b'\x00' * (32 - len(name))
    flags = 0x80
    msg = 1
    mystery_byte = 0
    path_code = 0
    addr = [0]
    addr_count = len(addr) #dynamic for a list of addrs
    size = 6 + len(addr)*2 #dynamic size

    pkt = struct.pack('>BBHBIB',flags,msg,size,mystery_byte,path_code,addr_count)
    for x in addr:
        pkt += struct.pack('>H', x)
    pkt+=name

    return pkt
```

Using this we still get the same information as sending a regular `PEERS` packet to the controller, but the debug information gives us more to view.![routed_peers_debug](C:\Users\Logan Stratton\Desktop\codebreakers\Task8\Images\routed_peers_debug.jpg)

Now by changing some of the values we can see how these values change in the debug, such as figuring out what the mysterious byte is used for, after testing we can see that the mysterious byte is actually the `index` of the `addrs` to choose from. Next we need to figure out how to use the `addrs`, if you changed the path_code value you may have noticed that some errors appeared relating to the `addrs` list. An example is setting the `path_code` to 1 and having 2 or more values in the `addrs` list, giving us this error `destination peer not found for addr: 0x0002`. Now to find the correct addresses, if you looked closely, when we ran `docker-compose up` you may have noticed a message like this `+PEER - id:2 fd:4 addr:0x9803`. Now looking back to the initial peers message we received from the controller in task 6, we see that this same 0x9803 shows up before the hostname. Testing this we set the second addr to 0x9803 and see that our packet was successfully routed and we received a peers communication from back from the drone.

```
RECVing PEERS...
packet header:
	8101000a00000000
	010298019803 		
packet content:
    08a8				#2 bytes before name
    04					#padding / deliminator
    75706461746572		#updater
    0000000000000000
    0000000000000000
    0000000000000000
    00
    08aa				#2 bytes before name
    04					#padding/ deliminator
    706f7765			#power
    7200000000000000
    0000000000000000
    0000000000000000
    00000000
```

Since the drone uses the same router binary as the drone for public connections, we can use the same method to display debug messages for the drone as well now. Doing this we can see how the drone handles the incoming routed packet and now we can attempt to route a packet one step further into the power module. We know the internal address of the power module is at 0x0854 from the peers message returned from the drone, so we can attempt to modify the earlier function again to get a route to the power module, after some testing I was able to get the following to work.

```python
def make_routed_power(x,nodetype, name):
    name = name.encode('utf-8')
    name = name[:31]
    name = name + b'\x00' * (32 - len(name))
    flags = 0x80
    msg = 1
    index = 2
    path_code = 450
    addr = [0,0,0,0x9803,0x08aa]
    addr_count = len(addr) #dynamic for a list of addrs
    size = 6 + len(addr)*2 #dynamic size

    pkt = struct.pack('>BBHBIB',flags,msg,size,index,path_code,addr_count)
    for x in addr:
        pkt += struct.pack('>H', x)
    pkt+=name

    return pkt
```

I'm not quite sure why this works but I was messing around with the index and offsets with different path_codes and this one worked so I just rolled with it, later on if you are hoping to actually learn where the math behind the path_code lies, you came to the wrong writeup...

Anyways sending this message we get the following data back,

```
Packet hdr:
8105001002000001
c205000098010001
980308aa
Packet Content:
7465726d			#terminal
696e616c00000000
0000000000000000
0000000000000000
0000000001140c00
0000001ec8000000
00000000048be13b
29c3db2000000000
00000000
```

The packet content should look semi familiar as the first 32 bytes seem to reflect whatever we send for our 32 byte message. Then the next 32 bytes look like some kind of code. To see what is going on now though we will need to look at the `netsrc`  binary. 

Starting to reverse `netsvc`, if you walk through main into run, you will see how the api is loaded, ie. `libpower` or `libupdater`. The main of what we will work with will be in `dispatch_packet`. Sadly our debug environment variable will not display strings printed from `netsvc` binary, we can bypass this by connecting to the docker instance locally and starting our own `netsvc power` instance, just be sure to change the command line option from `power` to something else as this dictates the hostname to use for the service. 

In Ghidra, you may see that there are several if statements all referring to `iVar1`, messing around with the packet structure you may notice that changing the `msg_type` will influence this value and gives us several options:

```
1 - PEERS
2 - Unsupported_type
3 - Open Session
4 - Data
5 - Close Session
```

While sending the the data connection we get this string back `Active Flight Monitor indicates drone is in-flight.  Will not issue power command. (try: forced-...)`, meaning possibly we can just send `forced-reboot` and call it a day. Replacing the name variable with `forced-reboot` gives us the same reply, but what if we still include the first 32 bytes then give our string. We get this string back now, `Flight Monitor is up to date, and indicates drone is in-flight.  Cannot force power command`, meaning we successfully sent what we needed to, to the `power` module to cause a reboot/shutdown if we have an update ready. Now we just need to create a packet that will send this to all connections at once. We can get a list of the hostnames ports and, from there we can go one by one to get all the internal ports used we just need to find a way to send a packet that will send to several nested addresses.

So continuing with bad practice, instead of reversing the `path_code` equation, I just brute forced it until I found a value that would route a packet to every other address. This can be done by viewing the debug information until you find a working solution, then changing the values in the addr list. For this scenario the value `0x19999e` was the winner. 

All that is left is to save the packet and submit it to complete the challenge.

You may be feeling cheated by the lack of reversing or interaction with the `libpower.so` binary so far, and I'm going to say that it isn't going to change as this is all we really need to do with the this binary, and take it as a blessing as this is a rust binary and we will have enough fun in Task 9 looking dynamically going through the other rust binary, `libupdater.so`.