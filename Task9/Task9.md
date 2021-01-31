# Codebreakers 2020 

# Task 9 - Rescue & Escape (Part 2) - (Reverse Engineering, Cryptography, Vulnerability Analysis)

### Points: 2500

### Description

```
Now that you have a working power command, you need to make changes to the drones so the command will be accepted. This string in the power module gives us some hope: 'New Flight Monitor Available. Allowing forced power command'

Find a vulnerability in the updater module that allows you to update the flightmonitor to a new version. Exploit the vulnerability on all of the drones to prepare them. Then, send your power command validated in the previous task. Once all the drones are unresponsive, let us know by submitting the word 'READY' in the field below. We will confirm and then send in the team to rescue the hostage!

Additional Notes: This will require a better understanding of the netsvc module than you needed for the power command. The update process looks like it requires a long running 'session' and the netsvc may have some protection mechanisms to guard against bruteforce attempts which you will need to abide by.
```

### Files

Same as Task 7

### Solution

Having created the final packet, we need to find a way to make it happen successfully, as the description says we will need to use the `update` module and will need to understand the `netsvc` module's `session` functionality better. Since we know how to theoretically open a session we can start by working with that. From reversing we can see that when a session request is sent, the function `new_session` is called. While statically reversing is possible it will help now and in the future to start looking at the binaries in a more dynamic sense. 

Using qemu-aarch64-static the same way that is done inside the docker allows us to run the `netsvc` binary locally as well as add the `-g` flag to connect gdb to follow with the assembly. Personally I ran into some problems using the latest version of `gdb-multiarch` in general, but was able to get version `8.3` to work. I recommend loading the `netsvc` binary into gdb as well to help break at different functions, but it is not needed overall. The binary is loaded at address `0x5500000000`, and should be every time it is ran.

Even though we are running qemu locally and not through the docker instance we can still connect to the drone by using the ip `192.168.24.3`, in my case. Making the full command, `qemu-aarch64 -g 2222 netsvc/1.0/netsvc 192.168.24.3 9000 fake_hostname updater/1.0/libupdateter.so api 100`. To talk to this qemu instance we will still need to route through both the controller and the drone but we already have a script to do most of the work.

First set a breakpoint at `new_session` so we can break there on opening the session, walking through the function and can see at the call to `SessionManager::check_pow` we have our 32 bytes of data being sent in with register `x1`. 

Looking at `check_pow` in Ghidra we can see a reference to a timestamp value and if you look at the structure setup for `SessionManager.pow_t` we can see multiple variables we might need to work with.

![pow_t_structure](C:\Users\Logan Stratton\Desktop\codebreakers\Task9\Images\pow_t_structure.jpg)

When the memcmp happens in `check_pow` we get a comparison of the 0x18 bytes

```
Sent data:
0x5501827d20:	0x0101010101010101	0x0101010101010101
0x5501827d30:	0x0101010101010101	0x0101010101010101
Compared data:
0x5501827f50:	0x010101013fab1401	0x0000000000000064
0x5501827f60:	0x96da08489522d58c	0x0000000000000000
```

If we expand the above compared data to the structure we get this

```
version: 0x01
bits: 0x14
salt_namespace: 0x3fab
timestamp: 0x01010101
salt_high: 0x0000000000000064
salt_low: 0x96da08489522d58c
counter: 0x0000000000000000
```

The timestamp may look familiar because before the memcmp our timestamp is stored into the comparison object, this is important because if we pass the memcmp then the local time is grabbed and compared to our time value. Before we can get to this check though we need to pass the memcmp, after noticing the data sent to the memcmp function you may notice that this is the same 0x18 bytes that are sent back to us in the bottom 32 bytes of the packet when we try to create open a session, if we use that as a reference we can make a packet that passes this check. Passing the comparisons, we can see that the sha256 of our data is taken then a check happens on it. We could try to reverse this and find exactly what is happening but it is most likely just making sure our hash has a certain structure before it works, to figure it out I set a breakpoint at the inner most if statement and tried a couple different hashes, and found that this for loop will return a 0 if the first 3 bytes of our sha256 are not all `00`. To bypass this I created a little side function that should create a hash that passes.

```python
import hashlib
def create_hash():
    counter = 0
    a = bytes.fromhex('01142b40')	#Version and bits should stay the same but salt_namespace changes every start 
    b = bytes.fromhex('64000000000000008cd522954808da96') #always stays the same, this is the salt
    while 1:
        m = hashlib.sha256()
        if counter % 2000 = 0:
            print(counter) #just a printing loop and also grabs a new time
            tim = time.time()
        check = a+struct.pack('>I',int(tim)+b+struct.pack('>Q',counter)
        m.update(check)
        hash = m.digest()
        
        if hash[:3] == b'\x00'*3:
            #found a hash
            break

        counter += 1
    
    return check
```

After passing the checks we get a new string returned to us `Bad update request: failed`, following the control flow after we can find a call to `api_dispatch` which seems to call the api loaded. Loading `libupdater` into Ghidra we can find that we are in the `api` function, inside this api function there is a call to `updater::pkt_entry` which because this is a rust binary might show up as `h3fc559b8f1092691`. Looking into `pkt_entry` you will find several math operations to start, if you search the consts you can find that a sip hash occurs, and after some more searching that is one of the default hashes used in some rust hashing functions. Overall we can just skip over this part though. At offset `0x7788` in the library, you can see that here are some comparisons starting to happen though, we should be able to set breakpoints at this address with gdb, for me this offset turns into the address `0x5501ad6788`. If we follow the execution we should get to point where we call `updater::start_update`, inside here is where most of the logic we want is located. Following the flow we see several calls to `updater::safe_path` with no strings passed into them. Scanning through this function it appears to just make sure any strings sent in are os safe. Continuing on we find that there is a check for path exists, then path join, then a final path exists, then we jump to an error path as the data we sent did not create a path that exists. If we look through the assembly in Ghidra we can see that if we passed this path exists check, we have another path join and path exists check. This time we want to fail it though, because if it passes then we enter the error display functionality. Continuing we get another 2 path joins, but this time with the string `key.pub`. This for now should be enough to get an idea of what the binary is looking for.

As with go binaries, rust likes to send in the length of a string for most functions, and as such there is a good chance we need to send in these as well to the program. Based on this assumption we need to send in possibly 3 different strings along with our hash opening, one path needs to be there, one path can't be there, then the last path+'key.pub' needs to be there. Using this logic along with the fact that the first join, joins the string `/var/opt/updater/modules` and whatever we pass, the first string should be `flightmonitor`, the second should be the old version we want to replace, and the last should be the new version. From the most recent version, we can see the `key.pub` file as well as `manifest`, `manifest.sig`, and `flightmonitor`. 

Since we are working locally and not through the docker we need to create the valid path in `/var/opt/updater/modules/flightmonitor`, and copy over the version 1.1 directory as well. Now continuing with the assumptions about the size being needed, we will append this string to the end of our packet `\x0dflightmonitorr\x031.1\x031.2`. After sending this, we can see that `safe_path` was called on all three of the strings we sent in, meaning we had the right assumptions so far about sending in three strings. Going to the first call of `Path::exists` we see it searching for the path `/var/opt/updater/modules/flightmonitor` now, next check is for `/var/opt/updater/modules/flightmonitor/1.2`. With failing this check we can make it to the next join where the string `/opt/flightmonitor` is being created, in the docker environment this should be a symbolic link to the most recent version. This brings us to offset `0x5d70` where we have another `join_path` to create `/var/opt/updater/modules/flightmonitor/1.1` then the join with `key.pub`. After this file appears to be checked in `updater::mmap_for_read`, continuing through we can see a temporary directory be made, finally inside this temp directory `manifest.sig` is created and the function returns. With this it appears that a session is finally created and if you are running a local version or even through the docker you should see that a temporary directory was created in `/var/opt/updater/modules/flightmonitor`. With a session created now would be a good time to say that we didn't just get lucky with the guess of what data to send in, but it actually took several me attempts to narrow down correctly what should be passed in. 

Now we have the ability to actually send in data to the program. This part of the program is fairly complex and as such I most likely won't do it justice but instead will just talk about what needs to get sent, to fully grasp what is happening I recommend running through several times, as it took me a full day alone to figure out the data part. But I digress, after reaching the api function with a data packet we can see that we will follow a different branch of logic from the open session request, in this section we see that the amount of data we sent in is compared to the value `0x2000`, and this value is changed, with subsequent data continuously decreasing this value. We can also see that whatever data we send is placed into the `manifest.sig` file in the temporary directory.

After we finish all 0x2000 bytes, without going over as it will reject packets that push it over. After this, if we send in another packet the first 4 bytes will correspond to the remaining data of this packet/file, and similar to `manifest.sig` this one corresponds to the `manifest` file itself. After filling in the manifest file with the size we proclaimed, we need to send an empty file as the manifest data we just sent does not match the signature file and we will receive an error back but the manifest will be parsed, meaning we need to send a valid looking manifest. Looking back at previous versions of manifest files we can determine that the structure of a manifest file is this

```
Sha256 hashes for each file
...							#depends on number of files
Filename size
filename
...							#depends on number of files
Number of files, last byte
```

So we need to create a manifest that lets us upload a new `flightmonitor` and a new `key.pub` file, we need to make sure the sha256 hashes are correct, but besides this it appears we can have whatever data we want in these files. If we uploaded a correct manifest, we now can send the next file it shouldn't matter what order but we will need to have 4 bytes for the total size, one byte be the file name size, then the file name, and then the remaining data to line up with sha256 hash from the manifest file. After sending both files, all that is left is to close the session so the directory is created. Once this is done, the temporary directory is moved to the real name you had given it.

Once this has been completed, we can send a `forced_reboot` to see that the process does reboot, and if you are running through a local qemu this will probably restart your system. All that is left is to enforce this on a remote instance. We can get all the addrs for the updater and use the one large connection to send multiple file creations at once. 

After sending a mass session request to get the initial counter we find that they are couple that may have varying initialization values, since we did a mass send we don't know officially which one is different, while we could modify everything to do one at a time, it isn't worth the time to brute the hash 5 times, when a few should work. When I first did this 4 of the drones them matched, but when doing this writeup only 2 match, so we need to brute force either way. Then if everything works correctly you should be able to send the reboot and get this string back 5 times `Congratulations you completed the challenge!`. 

![reboot](C:\Users\Logan Stratton\Desktop\codebreakers\Task9\Images\reboot.jpg)

I only have 3 in the above image because I had reboot 2 right before.

Now send the team in by signaling the environment is ready and you complete all the challenges from this year.

### Thoughts

This year is the furthest I had ever made it in the codebreakers series and also one of the most enjoyable. I was stuck on the signal analysis for the longest time mostly because I was interpreting the data incorrectly, but that is on me instead of the challenge. As for the final bit, it was an interesting approach needing technical knowledge on how the systems communicate and how to infiltrate, the one downside to it was the need to find a hash that passed the check, at times it would happen within 10 seconds others I waited 30+ minutes to find a hash that would work, just bad luck overall but it really slows you down when you don't want the process to behave incorrectly while getting a working hash. While it is possible to patch the binary to pass regardless of the hash sent in, it could have caused problems down the road. 



