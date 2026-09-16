import codecs

with open('src/ui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'show="●", font=PRO_FONT, height=36)' in line and 'entry =' not in line and 'placeholder' not in line:
        continue # skip the duplicated broken line
    new_lines.append(line)

with open('src/ui.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed!')
