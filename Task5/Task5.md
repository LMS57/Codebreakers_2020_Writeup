# Codebreakers 2020 

# Task 5 - Where Has the Drone Been? - (Reverse Engineering, Cryptography)

### Points: 1300

### Description

```
A rescue team was deployed to the criminal safehouse identified by your efforts. The team encountered resistance but was able to seize the location without causalities. Unfortunately, all of the kidnappers escaped and the hostage was not found. The team did find two important pieces of technology left behind: the journalist's Stepinator device, and a damaged surveillance drone. An analyst retrieved some encrypted logs as well as part of the drone's GPS software. Your goal for this task is to identify the location of the criminal organization's base of operations.
```

### Files

gpslogger

logs.tgz

### Solution

All of the files from the logs.tgz file appear to be encrypted in some method so we will need to find a way to decrypt them from the gpslogger file. 

The gpslogger binary is a Go aarch64 binary. We can find this out by running strings and file on the binary itself. If you have never reversed a Go binary before this can be a bit different in the way Go handles parameters and strings.

After opening the binary in Ghidra or any reversing tool you should be able to see a list of the functions, most of the time the important go functions to look at will begin with the prefix of `main.` and in our case this is no different.

![Functions](C:\Users\Logan Stratton\Desktop\codebreakers\Task5\Images\Functions.jpg)

From the functions list we can look into start_logging and see that it will call setup_cipher as well. If you look through the disassembly in Ghidra only, you will miss most of the details as most functions will look like nothing is being passed into them, when in reality Go passes the parameters through the stack instead of by registers first.

To get the correct view of arguments being passed we will need to change the function parameters for each function manually. Right clicking the function then `Edit function Signature` we can change the `Function Attributes` to `Use Custom Storage` and remove anything referencing a register and the first stack parameter, the return address can stay as w0 but most likely will store anything of value by reference. After changing `setup_cipher` I also modified the `poll_for_gga_rmc` before to see if anything stands out between them and we can see that they share a parameter.

![shared_variable](C:\Users\Logan Stratton\Desktop\codebreakers\Task5\Images\shared_variable.jpg)

This allows us to believe that the first parameter is created from the earlier function `poll_for_gga_rmc`, skimming over the poll function we can see that `gps_GPSNMEA` is called, we can't follow the function much further as an external library is referenced for the real data in it. Going back to `setup_cipher` and changing some of the other functions parameters we can see that` strings.getSplit` uses our parameters right away. we can see that the first parameter is used a couple times. 

```
  strings.genSplit(param_1,param_2,&DAT_004e8025,1,0,...);
```

I truncated what is shown above but we see the important parts, now knowing how Go handles strings will help in this part. When passing a string go will also pass the length of the string, as strings are not delaminated by null bytes like in c. `param1` has a length of `param_2` which makes sense, then the data value turns into the string `,`, this means whatever string that is passed into `setup_cipher` is then split by commas.

Next we have these instructions after the `genSplit`

![after_genSplit](C:\Users\Logan Stratton\Desktop\codebreakers\Task5\Images\after_genSplit.jpg)

b0 can't be 0 and b8[1] has to equal 6. Then the value at b8 is checked to the value `0x474e4724` and `0x4147` or the string `$GNGGA`. Searching this string I found this site `https://diy.waziup.io/sensors/GPS/gps.html`, which states that GPGGA or Global Positioning System Fix Data is in this format.

```
$GPGGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh
where llll.ll is the latitude and yyyyy.yy is the longitude
```

From this information we can assume that `b0` is the size of an array returned by the strings function, and b8 is the array of pointers to the strings and the lengths of the strings in alternating order so `b8[1]` is the size of `b8[0]` and so on. Next we have another `strings.genSplit` as well as a storing of the values in b0 and b8,

```
ppiVar2 = local_b0;
local_48 = local_b8;
strings.genSplit(local_b8[4],local_b8[5],&DAT_004e8027,1,...)
```

With b0 and b8 being stored before function calls it could be safe to say the the returned array/values from certain functions will be stored in b0 and b8, repeatedly. Since `genSplit` is on index 4 and index 5 is the size representing it, we can split up the `GPGGA` string from earlier to get a look into what our full array looks like.

| Index | Value (either a string or an int) |
| :---: | :-------------------------------: |
|   0   |              $GPGGA               |
|   1   |                 6                 |
|   2   |             hhmmss.ss             |
|   3   |                 9                 |
|   4   |              llll.ll              |
|   5   |                 7                 |
|   6   |                 a                 |
|   7   |                 1                 |
|   8   |             yyyyy.yy              |
|   9   |                 8                 |

This will continue on but this should be enough for us to work with.

Looking back at the `genSplit`, now we can see that we are working with the latitude string `llll.ll`, and the `Dat` value is the string `.`, this helps verify that we are working with the right values.

The disassembly checks `b0` against the value `4`, which we claimed `b0` to directly relate to the returned values from the `genSplit` function, but if we look in the assembly we can see that `98` is actually being used and this value is stored from the first `genSplit` from earlier. At this point is may be a good idea to start to follow values stored in the stack from these functions as Ghidra has a difficult time following all the movements between the stack, but the array returned from the most recent `genSplit` is stored in `38` and the size is stored in `88`.

We can go down to the next `genSplit` and see that this one is done on the longitude string `yyyyy.yy` and is stored in `40` and `90` for the array and array size respectively.

Next we can see the `generate_key` and the `generate_iv` function with `38[0]` being used in `generate_key` and `40[0]` being used in `generate_iv`. This means that possibly our key and iv for the AES encryption can be inferred directly from the latitude and longitude alone.

 #### generate_key

Going into the generate_key function and changing the function signature of `string.Repeat` shows that our `param_1` is repeated `4` times. Making `llll` become `"llll"*4` or a 16 byte string, which is a typical size for a key used in AES

#### generate_iv

Inside generate_iv we see a similar instance to `generate_key` but we have the `param_1` repeated `3` times, this would give us a string length of 15 from `yyyyy`. But after we also see a `string.concatstring2` call with a string of `0` so we can guess that we add `0` to make the string length 16 bytes also, or 128 bits. This gives us the type of AES, making it AES-128.

#### Decrypt

We now know how the key and iv are created so we can find a way to effectively decrypt it now.

Knowing that the key and iv have repeated character sequences we can brute force the possible decryption with this script

```python
#python2
from Crypto.Cipher import AES
from threading import Thread

enc = open('./Logs/20200628_153027.log').read(128)

alphabet = [chr(x) for x in range(32,127)] + ['\n','\r','\t', '\0']

def thread_fun(id): 
    for x in range(10*id,10*(id+1)):
        for y in range(100000):
            aes = AES.new(str(x).zfill(4)*4,AES.MODE_CBC,'0'+str(y).zfill(5)*3)
            tmp = aes.decrypt(enc)
            if all(z in alphabet for z in tmp):
                print x,y,tmp.split('\n')[0]
        if id == 0:
            print id,x

num_threads = 10
threads = []

for x in range(num_threads):
    t = Thread(target=thread_fun,args=(x,))
    t.start()
    threads.append(t)

for x in range(num_threads):
    threads[x].join()

```

We could probably guess what kind of data would be stored from a program called `gpslogger` but it is better to just check all possible bytes to make sure they are readable. The above script does take a bit of time and would definitely run faster in c, but this will work for what we need.

After some time we can see that the script output several possible ranges that could work for our solution. This is what some of the output will look like

```
524 1955 $GMJ@M,284<24#7<,0524.073024,N,02429.706995,W,1,12,0.7,57.0,M,-42.0,M,,*77
524 1956 $GMJ@N,284?24#7?,0524.073024,N,02429.706995,W,1,12,0.7,57.0,M,-42.0,M,,*77
524 1957 $GMJ@O,284>24#7>,0524.073024,N,02429.706995,W,1,12,0.7,57.0,M,-42.0,M,,*77
524 1958 $GMJ@@,284124#71,0524.073024,N,02429.706995,W,1,12,0.7,57.0,M,-42.0,M,,*77
```

You could scan through the output until `$GNGGA` shows up in the beginning or you could notice that all the lat and long values are staying the same, and at 524 2429 we see the `$GNGGA` string

```
524 2429 $GNGGA,153027.00,0524.073024,N,02429.706995,W,1,12,0.7,57.0,M,-42.0,M,,*77
```

And with that we have our values to submit