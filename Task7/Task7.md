# Codebreakers 2020 

# Task 7 - Plan for Rescue - (Reverse Engineering)

### Points: 500

### Description

```
With proof the journalist is alive and held inside the compound, the team will make a plan to infiltrate without being discovered. But, they see a surveillance drone and expect more are in the area. It is too risky without knowing how many there are and where they might be. To help the team avoid detection, we need you to enumerate all of the drones around the compound. Luckily we've made some discoveries at the safehouse which should help you. You can find the details in the attached README file. Get to work and give us the list of drone hostnames you discover. This will tell us how many to look for, and hopefully indicate where they might be.
```

### Files

README.txt

wg3.conf (ommitted)

wg4.conf (ommited)

bundle.tar

hello.py

### Information

This challenge was the start of the second phase of challenges, where a user would only have access to submit for them after completing all previous challenges. Also I have ommited the wg vpn conf files as I was requested not to share the private keys and all they contain are the IP's which in my case the target IP is `10.129.130.1/32`, so you have everything now without needing the files.

From the README we get a description of our scenerio. Some of the main points being, that the most recent `flightmonitor` file was corrupt so version `1.1` was replaced with a file of similar size with null bytes. We get a local instance of the drone network through qemu and docker, with the ability to add multiple versions if needed.  There is a main controller that we are able to communicate with on port `9000`. Lastly hello.py contains a valid method to send a hello message to a controller.

Looking through the docker files you can see how everything gets setup and some of the connections. Inside `supervisord.conf` we can see the files that will be ran for each system, such as `/opt/router/router` for the controller and `/opt/netsvc/netsvc` twice for `libupdater` and `libpower`.

### Setup

Using `docker-compose build` and `docker-compose up` will create and run the docker instances for a local test network. From this we can test the hello.py file to make sure everything is connected and working correctly. Everything looks to be running correctly when we get a response printed back to us.

```
/plan# ./hello.py hello
sending HELLO:
0027000000000000
017465726d696e61
6c00000000000000
0000000000000000
0000000000000000
00
RECVing HELLO...
0100000000000274
68655f636f6e7472
6f6c6c6572000000
0000000000000000
00000000000000
connected to: 0 2 b'the_controller'

```

### Reversing

Since the binary itself is decently robust, I most likely will not describe every bit in detail but will try to get to the most important parts, an example will be the description and definition of certain bytes used during the network communications. To be honest, I don't know what makes certain values work, this is more for the last 2 challenges but may also cross over into this region. With that said let's reverse the current network model that we know from the hello.py file.

After going through hello.py we can assume that communications take this appearance:

```
2 bytes: frame header and size of the following packets data
pkt_header: 
	flags, 1 byte: Type of flags sent to the message, from the message above this appears to be 0 or 1 so far.
	msg, 1 byte: possibly the message type
	zeros, 2 bytes: Zeros is all the information we know
content:
	bunkown, 2 bytes: currently 0
	btype, 1 bytes: currently our node_type/terminal_type 1
	name, 32 bytes: padded out to 32 bytes, but currently contains a name we want to be known as
```

With that out of the way, we can move onto the `router` binary itself, since we only want to find the hostnames of the drones and we can only talk to the controller, this is only chance for any communications. Viewing the main of the binary, we see an initial function call to `set_rt_log_level`, exploring this function we see that there are checks for environmental variables and a debug variable being set. Since this checks the environment, we can change the docker-compose file to include this environment variable and hopefully display all debug messages. The docker-compose file that I included has already added the env variable to it, so if you want to run the controller without debug remove the environment variable.

Now if we start the docker environment again we see that we are greeted with verbose information from the controller about all connections made, packets received, and data sent. With this debug information and the `hello.py` we can see what kind of functions are called when we send packets to the controller.

![hello_debug](C:\Users\Logan Stratton\Desktop\codebreakers\Task7\Images\hello_debug.jpg)

It appears that from this information, handle_received_frame will interpret our packet as a `HELLO` message and is a good spot to start. In Ghidra, the function can look a bit complex but around line 50 of the decompiled code we can see this:

```
          if (hdr_00->msgtype == '\0') {
            _Var3 = handle_received_HELLO(mux,muxnode,peer_data,id,hdr_00,&remaining);
          }
          else {
            if (hdr_00->msgtype == '\x01') {
              _Var3 = handle_received_PEERS(mux,muxnode,peer_data,id,hdr_00,&remaining);
            }
```

It appears that if our message type is `0` it corresponds to a `HELLO` packet and if it is `1` we sent a `PEERS` packet. Using this information, the debug info, and tinkering around with hello.py we find that changing the `msg` variable definitely determines the type of packet we sent. If we try to change the `message_type` to anything else but to `HELLO` we continue to get errors about `non-HELLO before HELLO`. To fix this we need to continue our connection after the first hello and send another message, with a different `message_type`. After modifying `hello.py` we can finally send a peers message now and get this:

```
RECVing HELLO...
0100000000000274
68655f636f6e7472
6f6c6c6572000000
0000000000000000
00000000000000
sending PEERS:
RECVing PEERS...
0101000098030374		#the_drone
68655f64726f6e65		
0000000000000000
0000000000000000
00000000000000
```

This appears to be the hostname of the local drone, so what happens when we send this packet to the remote instance.

```
RECVing HELLO...
0100000000000263		#compound_controller
6f6d706f756e645f		
636f6e74726f6c6c		
6572000000000000		
00000000000000
sending PEERS:
RECVing PEERS...
01010000800a0363		#compound_NE_02_33e6e23a23121d82
6f6d706f756e645f
4e455f30325f3333
6536653233613233
3132316438320080
0203636f6d706f75		#compound_NE_01_19018be94aff9ac7
6e645f4e455f3031
5f31393031386265
3934616666396163
3700800603636f6d		#compound_SE_01_0a8192b25d7c8f76
706f756e645f5345
5f30315f30613831
3932623235643763
3866373600800803
636f6d706f756e64		#compound_SW_01_2b5585f0621dd9ba
5f53575f30315f32
6235353835663036
3231646439626100
800403636f6d706f		#compound_NW_01_10b7f2496018a077
756e645f4e575f30
315f313062376632
3439363031386130
373700
```

From this response we can see the list of the hostnames for all the drones and finish the task.