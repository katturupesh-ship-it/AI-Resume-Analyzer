resume = input("Paste your resume text: ")

skills = ["Python", "Java", "SQL", "HTML", "CSS"]

for skill in skills:
    if skill.lower() in resume.lower():
        print(skill, "✓")
    else:
        print(skill, "✗")