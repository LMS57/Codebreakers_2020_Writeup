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

	for(int x = 0; x < total;x+=2){
		floats[x] = tofloat((int)sig[x]);
	}

	f = open("./signal.float",O_CREAT|O_WRONLY|O_TRUNC,0666);
	write(f, floats,total*4);
	close(f);
		
}

