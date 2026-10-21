# def show():
#     print("Start")
#     yield 10
#     print("Middle")
#     yield 20
#     print("End")
#     yield 30
#     print("Finished")
#     yield 40

# g = show()

# print(next(g))
# print(next(g))
# print(next(g))
# print(next(g))
# print(0.2 + 0.2 == 0.4)


# t1 = (1,2,3)
# t2 = (1,2,3)
# l1 = [1,2]
# l2 = [1,2]

# print(t1 is t2)
# print(l1 is l2)

# def bill_split(amount, friends):
#     amount +=(20/100 * amount)
#     amount_per_head = amount/friends
#     return round(amount_per_head, 2)

# print(bill_split(82.10, 3))


# word = 'Faizan Ali'
# vowels = 'aeiou'

# res = [v for v in word.lower() if v in vowels]
# print(res)

# tables = [[i * j for j in range(1,11) ] for i in range(2, 6)]
# print(tables)



# import requests

# respone = requests.head('https://www.w3schools.com/python/demopage.php')
# print(respone.headers)
# with open('main.html', 'w') as file:
#     file.write(respone.headers)


# class Person:
#     species = "Human" # Class property

#     def __init__(self, name):
#         self.name = name # Instance property

#     def print_name(self):
#         print(self.name)

# p1 = Person("Emil")
# p2 = Person("Tobias")

# # print(p1.name)
# # print(p2.name)
# print(p1.species)
# print(p2.species)

# p2.print_name()

# class Teacher(Person):
#     def __init__(self, name):
#         super().__init__(name)

# t = Teacher(name='Faizan')

# t.print_name()




class Car:
  def __init__(self, brand, model):
    self.brand = brand
    self.model = model

  def move(self):
    print("Drive!")

class Boat:
  def __init__(self, brand, model):
    self.brand = brand
    self.model = model

  def move(self):
    print("Sail!")

class Plane:
  def __init__(self, brand, model):
    self.brand = brand
    self.model = model

  def move(self):
    print("Fly!")

car1 = Car("Ford", "Mustang")       #Create a Car object
boat1 = Boat("Ibiza", "Touring 20") #Create a Boat object
plane1 = Plane("Boeing", "747")     #Create a Plane object

# for x in (car1, boat1, plane1):
car1.move()
boat1.move()
plane1.move()