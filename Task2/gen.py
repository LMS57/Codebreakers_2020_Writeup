name = ["sheba","Sheba","SHEBA"]
dates = ["0803","83","083","803","83","0803","803","083","0308","038","308","38","08/03","08/3","8/03","8/3","03/08","03/8","3/08","3/8"]
fd = open('./wordlist','w')
for y in name:
    for x in dates:
        fd.write(y + str(x) + '\n')
