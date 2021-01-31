#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>

#define NUMBITS 17
void tobin(unsigned n)
{
    unsigned i;
    for (i = 1; i < (1 << NUMBITS); i = i * 2)
        (n & i) ? printf("1") : printf("0");
    puts("");
}

int pos[1<<NUMBITS];
int main(){

	int start = 0;
	int f = open("./sig.out",0,0);
	int total = 9587048;
	//total = 2000;
	unsigned char *test = malloc(total*2);
	unsigned int *nums = malloc(total*2);
	unsigned char *nums2 = malloc(total*2);
	read(f,nums2,total);
	close(f);

	int counter = 0;
	unsigned int tmp = 0;
	int tmp2 = 0;
	int val;
	for(int x = start; x < total+start;x++){
		tmp |= ((int)nums2[x]) << ((x-start)%NUMBITS);
		if(((x-start)%NUMBITS)==(NUMBITS-1))
		{
			if(counter % 3 == 0){
				test[counter++] = tmp &0xff;
				tmp2 = (tmp&0xf00)>>8;
			}
			else{
				tmp2 |= ((tmp&0x0f)<<4);
				test[counter++] = tmp2;
				test[counter++] = (tmp>>4);
				
			}
			tmp = 0;
		}
	}

	write(1, test,counter);

		
}

