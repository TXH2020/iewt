import matplotlib.pyplot as plt
import numpy as np

with open('res.txt','r') as f:
    file=f.read()
x=file.split('\n')
time=[]
mem=[]
cpu=[]
for i in range(len(x)-1):
    t=x[i].split(' ')
    if(len(t)==4):
        mem.append(float(t[1]))
        cpu.append(float(t[-1]))
    elif(len(t)==5):
        time.append(float(t[1]))

plt.title('RAM vs No. of connections')
plt.xlabel('No. of connections')
plt.ylabel('RAM usage in %')
plt.plot(list(range(5100))[::100],mem)
plt.show()
plt.title('CPU vs No. of connections')
plt.xlabel('No. of connections')
plt.ylabel('CPU usage in %')
plt.plot(list(range(5100))[::100],cpu)
plt.show()
plt.title('Connection time vs No. of connections')
plt.xlabel('No. of connections')
plt.ylabel('Connection time in s')
plt.plot(list(range(len(time))),time)
plt.show()

print("Median time=",np.median(time))
print("Mean time=",np.mean(time))
time.sort()
for i in range(len(time)):
    if(time[i]>3):
        time=time[:i]
        break

plt.title('Connection time boxplot after removal of outliers')
plt.ylabel('Connection time in s')
plt.boxplot(time)
plt.show()
