# Codebreakers 2020 

## 4 - Follow That Car! - (Graph Algorithms, Computer Science)

### Points: 500

### Description

```
By using the credentials in the decrypted file, we were able to download the journalist's accelerometer data from their Stepinator device from the time of the kidnapping. Local officials have provided us with a city map and traffic light schedule. Using these along with the journalist's accelerometer data, find the closest intersection to where the kidnappers took their hostage.
```

### Files

README.txt

stepinator.json

maps.zip

### Solution

After reading the provided README we are given the situation, of the reporter being kidnapped at the location marked on the map and the kidnappers directly heading east. As well as the logic behind the traffic lights, and the speed limit in the town, and the sizes of the streets.

While the problem gives us the acceleration for a given moment in the stepinator.json file it is not an easy way to perceive the current speed/velocity that may be occurring in a moment of time, but we can easily convert it to the current velocity. The below script will converts the json data to the velocity as well as printing the current time, distance traveled, current velocity, and current acceleration. While there is a json library in python I was too lazy to use it for a one time file read.

```python
fp = open('./stepinator.json').read()[1:-1].split(',') #just treat data as list instead of json
t = 0
d = 0
v = 0
for x in fp:
    t+=1
    x = x.strip()
    a = float(x)
    v += a
    d += v
    print t,int(d),"{:.2f}".format(v),a
```

The above script is just more of a visual help more than anything else.

Based on the logic of traffic laws, we know that the velocity will decrease in 2 scenarios they were approaching a red light or they were turning, in the second scenario this could leave us with two possibilities left/right turn on green, if they want to turn on a red they would need to wait for the light to change back to green again. 

For example a turn may look like the data below from readings 12-16

```
#  Dis Vel  Acc
12 102 8.65 -4.0
13 106 4.65 -4.0
14 113 6.15 1.5
15 120 7.65 1.5
16 129 9.15 1.5
```

As we came to about the 100m mark we see a decrease in speed then an acceleration again, this most likely means that the kidnappers took a turn on a green light as they never came to a full stop.

Modifying the python script above we can create a list of all possible positions based on the json data given to us, this script does not incorporate the traffic lights or how the city is laid out, but just a possibility of any turns that could occur after a stop.

```python
#python2
A = open('./stepinator.json').read()[1:-1].split(',') #just treat data as array instead of json
A = map(float,A)

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

        #do turning possibilities
        if test == 0: #vehicle has not shown signs of slowing down
            if A[i] < 0: #vehicle is slowing down
                test = 1
        else:#vehicle shows signs of possibly turning
            if A[i] > 0: #vehicle is speeding up again, recurse could have turned or could be going the same direction
                #the reason I'm passing pos[:] instead of just pos is that we want to pass a copy or pos and not use the same item, just how python works with objects
                poss(pos[:],x,y,(direction+1)%4,i+1,vel,dis)#turned left
                poss(pos[:],x,y,(direction-1)%4,i+1,vel,dis)#turned right
                test = 0 #will account for going the same direction continue with same loop
    #we completed a path
    print pos

poss([],13,6,1,0,0,0) #start at location 13,6 going east 0,index
```

After running the script I am left with a bit over 700 possibilities.

Next is just a process of elimination, some of the early possible paths can be removed by impossible locations such as `(13, 3)`. Others will have to be walked through to make sure that they are possible with the given traffic lights maps, but after working through it I am left with one possibility,  

```
[(13, 7), (14, 7), (14, 6), (14, 5), (14, 4), (15, 4), (15, 5), (15, 6), (15, 7), (15, 8), (16, 8)]
```

Meaning that we lost track of the target at the corner of 16th and H. 