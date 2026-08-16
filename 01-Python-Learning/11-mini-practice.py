name = input("Enter your name: ")

skills = ["Python", "Java", "SQL"]

student = {
    "name": name,
    "branch": "CSE"
}

print("Name:", student["name"])
print("Branch:", student["branch"])

print("Skills:")

for skill in skills:
    print("-", skill)