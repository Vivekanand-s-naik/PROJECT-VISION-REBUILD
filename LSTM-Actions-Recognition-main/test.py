# [
#  [1],
#  [1,1],
#  [1,2,1],
#  [1,3,3,1],
#  [1,4,6,4,1]
# ]

def print_stars(num):
	for i in range(1, num):
		print(i, end=", ")
		for j in range(i):
			print(j, end=", ")
		print()
# print_stars(10)
class Bird:
    def sound(self):
        print("Bird sound")

class Cat:
    def sound(self):
        print("Meow")

for obj in (Bird(), Cat()):
    obj.sound()
