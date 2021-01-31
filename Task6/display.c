#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

int main(){

	int f = open("./bits.out",0,0);
	int total = 9587048;
	unsigned char *bits = malloc(total);
	read(f,bits,total);
	close(f);

	for(int x = 0; x < total;x++){
		if (x % 17==0)
			puts("");
		printf("%d",bits[x]);
	}

	close(f);
		
}

