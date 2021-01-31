A = open('./stepinator.json').read()[1:-1].split(',') #just treat data as array instead of json
A = map(float,A)
'''
t = 0
d = 0
v = 0
V = []
for x in fp:
    t+=1
    x = x.strip()
    a = float(x)
    v += a
    d += v
    V.append(v)
'''

prev = 0

'''
params:
    pos = list of possible movements that have happened
    x = current x position
    y = current y position
    direction = current direction, north=0 east=1 south=2 west=3
    cur = current index to read from for recursiveness
    vel = current velocity, only needs to be sent in case that a turn occurs without stopping
    dis = current traveled distance, probably between 0-95
'''
def poss(pos,x,y,direction,cur, vel,dis):
    test = 0
    for i in range(cur,len(A)):
        #do distance math first
        vel+= A[i]
        tmp = dis+vel
        if dis//95 != tmp//95:#crappy way to determine a block having been traveled
            if direction == 0:
                x+=1
            elif direction == 1:
                y+=1
            elif direction ==2:
                x-=1
            else:
                y-=1
            #append tupple
            pos.append((x,y))

        dis = tmp

        #do turning math
        if test == 0: #vehicle has not shown signs of slowing down
            if A[i] < 0: #vehicle is slowing down
                test = 1
        else:#vehicle shows signs of possibly turning
            if A[i] > 0: #vehicle is speeding up again, recurse could have turned or could be going the same direction
                #the reason I'm passing pos[:] instead of just pos is that we want to pos a copy and not use the same item, just how python works with objects
                poss(pos[:],x,y,(direction+1)%4,i+1,vel,dis)#turned left
                poss(pos[:],x,y,(direction-1)%4,i+1,vel,dis)#turned right
                test = 0 #will account for going the same direction continue with same system
    #we completed a path
    print pos



        

poss([],13,6,1,0,0,0) #start at location 13,6 going east 0,index
