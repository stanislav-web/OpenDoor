import subprocess

height, width = subprocess.check_output(['stty', 'size']).split()

print w,h