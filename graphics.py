import matplotlib.pyplot as plt
with open('data.txt') as f:
    lines = f.readlines()
    x = [int(line.split()[0]) for line in lines]
    y1 = [int(line.split()[1]) for line in lines]
    y2 = [int(line.split()[2]) for line in lines]
    y3 = [int(line.split()[3]) for line in lines]
    y4 = [int(line.split()[4]) for line in lines]

# print(x)
# print(y1)
# print(y2)
print(max(x))
fig = plt.figure()

ax1 = fig.add_subplot(111)

ax1.set_xlim([0,int(max(x)) + 10])
ax1.set_ylim([0,int(max([max(y1), max(y2)]) + 10)])
ax1.set_title("number of cells over steps(time)")    
ax1.set_xlabel('steps')
ax1.set_ylabel('num of cells')

ax1.plot(x, y1, c='purple', label='Purple Cancer Cells (Normal)')
ax1.plot(x, y2, c='blue', label='Blue Cancer Cells (Nonagressive)')
ax1.plot(x, y3, c='orange', label='Orange Cancer Cells (Aggressive)')
ax1.plot(x, y4, c='red', label='Capillary Cells')

leg = ax1.legend()

plt.show()