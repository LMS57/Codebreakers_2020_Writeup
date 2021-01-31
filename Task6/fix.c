#include <stdio.h>
#include <stdlib.h>

//LET'S GO!!!, It is the first matrix


#define NUMBITS 17

void tobin(unsigned n)
{
    unsigned i;
    for (i = 1; i < (1 << NUMBITS); i = i * 2)
        (n & i) ? printf("1") : printf("0");
    puts("");
}

int result[16];//?

int h[4][16];
int m[16];

int multiplyMatrices(){
   // Initializing elements of matrix mult to 0.
   for (int i = 0; i < 16; ++i) {
         result[i]= 0;
      }

   int counter = 0;
   // Multiplying first and second matrices and storing it in result
   for (int i = 0; i < 4; ++i) {
 	for (int k = 0; k < 16; ++k) {
	   result[i] += h[i][k] * m[k];
	 }
      
	if(result[i]%2==1)
	{
	      counter++;
	}
   }

   if(counter){
	   int find = 0;
	for(int i = 0; i < 16; i++){
		int issame = 1;
		for(int j = 0; j < 4; j++){
			if((result[j]%2) != h[j][i]){
				issame = 0;
				break;
			}
		}
		if(issame){
			m[i] ^= 1;
			find = 1;
		}
	}
	if(find == 0){
		printf("\nFailure\n");
		exit(0);
	}
   }

   return counter;
}

int pos[4] = {1483,1964,1658,861};

void creatematrix(z){
	for(int x = 0; x < 4; x++){
		for(int y = 0; y < 16; y++){
			h[x][y] = (pos[x]>>y)&1;
		}
	}

	h[0][12] = 1;
	h[1][13] = 1;
	h[2][14] = 1;
	h[3][15] = 1;

}

int main(){
	
	int f = open("./bits.out",0,0);
	int total = 9587048;
	unsigned int *nums = malloc(total*2);  
	unsigned char *nums2 = malloc(total*2);
	read(f,nums2,total);
	close(f);

	int counter = 0;
	unsigned int tmp = 0;
	int val;
	int start = 0;
	for(int x = start; x < total+start;x++){
		tmp |= ((int)nums2[x]) << ((x-start)%NUMBITS);
		if(((x-start)%NUMBITS)==(NUMBITS-1))
		{
			nums[counter++] = tmp;
			tmp = 0;
		}
	}

	char *out = malloc(counter);
	int count2 = 0;
	
	creatematrix();
	int c = 0;
	for(int y = 0; y < counter; y++){
		for(int z = 0; z < 16; z++){
			m[z] = (nums[y]>>z)&1;
		}
		
		multiplyMatrices();

		//print out all as a string of bits, can handle from there
		for(int z = 0; z < 11; z++){
			printf("%d",m[z]);
		}
	}


}

