# Codebreakers 2020 

# Task 6 - Proof of Life - (Signals Analysis)

### Points: 1300

### Description

```
Satellite imaging of the location you identified shows a camouflaged building within the jungle. The recon team spotted multiple armed individuals as well as drones being used for surveillance. Due to this heightened security presence, the team was unable to determine whether or not the journalist is being held inside the compound. Leadership is reluctant to raid the compound without proof that the journalist is there.

The recon team has brought back a signal collected near the compound. They suspect it is a security camera video feed, likely encoded with a systematic Hamming code. The code may be extended and/or padded as well. We've used BPSK demodulation on the raw signal to generate a sequence of half precision floating point values. The floats are stored as IEEE 754 binary16 values in little-endian byte order within the attached file. Each float is a sample of the signal with 1 sample per encoded bit. You should be able to interpret this to recover the encoded bit stream, then determine the Hamming code used. Your goal for this task is to help us reproduce the original video to provide proof that the journalist is alive and being held at this compound.
```

### Files

signal.ham

### Solution

The description to the challenge mostly tells us how to start, saying that every 2 bytes represent a 16 bit float, and that these values have been BPSK demodulated. I'm not going to go into the math or how signals work but looking into BPSK demodulation will tell you that we still need to correctly convert these floats into their binary representation, this is usually done through constellation decoding.

To do this successfully I found that gnu radio was the way to go, there are most likely python was to accomplish this also I just couldn't get anything to work after testing. But all we need to do is read in the values as floats, constellation decode them, and save them to a new file.

Here is an image of the type of what the decoding process will look like in gnuradio-companion.![GRC](C:\Users\Logan Stratton\Desktop\codebreakers\Task6\Images\GRC.jpg)

The main problem here is that the file source can't interpret the original file as it doesn't have a 16 bit float option. Below is a c script to convert the 16 bit floats to 32 bit floats and save them to a new file. 

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

//http://www.fox-toolkit.org/ftp/fasthalffloatconversion.pdf
float tofloat(int n)
{
	return (float)(((n&0x8000)<<16) | (((n&0x7c00)+0x1c00)<<13) | ((n&0x03ff)<<13));
}

int main(){

	int f = open("./signal.ham",0,0);
	int total = 19174096/2;
	unsigned short *sig = malloc(total*sizeof(short));
	float *floats = malloc(total*sizeof(float));
	read(f,sig,total);
	close(f);

	for(int x = 0; x < total;x+=2)
		floats[x] = tofloat((int)sig[x]);

	f = open("./signal.float",O_CREAT|O_WRONLY|O_TRUNC,0666);
	write(f, floats,total*4);
	close(f);
}
```

Once we have them we can use the gnuradio-companion to convert the data to binary.

You may notice that gnuradio doesn't exactly save the data in a way we were hoping but instead each byte is either `01` or `00`. We will just need to factor this in when we try to find the hamming code. 

Now comes the interesting part of figuring out what the hamming code is. After checking some common hamming codes you may come up short of any good solutions. One approach that I wouldn't recommend outside this clean environment is to take the number of bits total into account, what I mean by clean environment is that we can assume that we probably didn't jump into the middle of a signal and that the signal didn't end abruptly. From the size of `bits.out` from gnuradio we have a file of size `9587048`, but this is where every byte is a 1 or a 0 so we need to condense this by a factor of 8. Giving us a size of `1198381` bytes. If you find the factors of this value you get

```
17
157
449
2669
7633
70493
```

Now if we check out the bit 17 by printing out the bits in 17 bit chunks with display.c, by checking the frequency of 0-1 in the 17th bit we get this

```
/signal# ./a.out | cut -b 17 | sort | uniq -c
      1 
 563255 0
    689 1
```

This shows that there is a good chance that the 17th bit is a padding bit and is usually set to 0. This is good now because there is a good chance that the previous bits will interpret the data and the hamming code. Since we know the code is systematic we can brute force to figure out what code is used.

Since there are 16 bits to work with we would need at least 5 bits of parity, if we had 12 bits of data. Which doesn't work so we could have a 16:11 code with an extra bit for parity, this will be what we test for first. 

Using brute.c, we can read in the bits and convert them to 17 bit ints. Then iterate through all possible hamming codes and see which evaluate to true the most out of our test cases. This is possible because the number of possible hamming codes that could occur in an 11 bit data code, is just `1<<11` or `2048` and this can easily be looped through and reset for each potential parity bit. I decided to limit this to 10000 iterations instead of the full 500000, mostly to save time. If you want a better description of how I brute, there are comments in brute.c to describe what is happening. After running brute.c we get a potential parity matrix

```
Z = 0
9913 191 11111101000000000
Z = 1
9912 1483 11010011101000000
Z = 2
9904 1964 00110101111000000
Z = 3
9906 1658 01011110011000000
Z = 4
9909 861 10111010110000000
```

With these values, if they are correct, we should be able to correct and fix the data from the stream. Having one possibility for each bit is a great start but if we continue in the assumption that one of the bits must be an overall parity bit, we need to figure out which it is. Since the parity bit doesn't help you decode but only helps you determine if there are more than one bit errors we can just test each bit for being the parity later on. But based on the appearance you may notice that bit 0 has a different look compared to the other 4 bits. Mainly the large contiguous block of 1's is different from the others, another observation that could be made is that bit 4 and 1 are reversed of each other and bits 2/3 are shifted from each other. This could be entirely coincidence though. 

So using the assumption that bit 12 is the parity or not needed for decryption we can use fix.c to go through the bits and fix any bad bits, then the script saves the entire fixed stream of bits to `final.bit` as converting to characters in c isn't worth the hassle of keeping tack of 11 to 8 bit offsets and such. Using python though, it is relatively easy and convert the bit string to a file. This is all done in fix.py, and recovers the file to recovered.mp4. From here we attempt to play the file and can see that the target is in view.

![target](C:\Users\Logan Stratton\Desktop\codebreakers\Task6\Images\target.jpg)

This proves that the 11th bit was not needed and may have been a parity bit or may have been a random padding bit. But we get a final parity matrix of 

```
[[1,1,0,1,0,0,1,1,1,0,1,0,1,0,0,0],[0,0,1,1,0,1,0,1,1,1,1,0,0,1,0,0],[0,1,0,1,1,1,1,0,0,1,1,0,0,0,1,0],[1,0,1,1,1,0,1,0,1,1,0,0,0,0,0,1]]
```

And we can get the timestamp from the video.