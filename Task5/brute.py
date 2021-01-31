from Crypto.Cipher import AES
from threading import Thread

enc = open('./Logs/20200628_153027.log').read(128)

alphabet = [chr(x) for x in range(32,127)] + ['\n','\r','\t','\0']

#0524 2429
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

