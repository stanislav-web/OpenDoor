# coding=utf-8
import re
import os
filename = 'setup.cfg'


expression = '^([\/a-z].*?opendoor.*?)\/'
find_dir = re.search(expression, __file__, re.IGNORECASE)
if None is not find_dir:
    os.chdir(find_dir.group())

filepath = os.path.join(os.path.sep, os.getcwd(), filename)
print(filepath)