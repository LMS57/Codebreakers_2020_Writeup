data = open('./final.bit').read() 

data = [data[x:x+8] for x in range(0,len(data),8)]

final = ""
for x in data:
    final += (chr(int(x,2)))

open('./recovered.mp4','w').write(final)

