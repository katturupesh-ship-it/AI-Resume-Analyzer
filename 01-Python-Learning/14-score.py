skills = ["Python", "Java", "SQL", "HTML", "CSS"]

score = 0

resume = input("Paste your resume text: ")

for skill in skills:
    if skill.lower() in resume.lower():
        score = score + 1

percentage = (score / len(skills)) * 100

print("Skills found:", score)
print("Skill score:", percentage, "%")