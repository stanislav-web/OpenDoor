"""
Shuffle lines in a [big] file
shuffle.py <input_file> <output_file> [<preserve headers?>] [<max. lines in memory>] [<random seed>]
"""

import sys
import random

input_file = sys.argv[1]
output_file = sys.argv[2]

try:
    preserve_headers = int(sys.argv[3])
except IndexError:
    preserve_headers = 0

try:
    lines_in_memory = int(sys.argv[4])
except IndexError:
    lines_in_memory = 27000

print "caching %s lines at a time..." % (lines_in_memory)

try:
    random_seed = sys.argv[5]
    random.seed(random_seed)
    print "random seed: %s" % (random_seed)
except IndexError:
    pass

# first count

print "counting lines..."

i_f = open(input_file)
o_f = open(output_file, 'wb')

if preserve_headers:
    headers = i_f.readline()
    o_f.write(headers)

counter = 0
for line in i_f:
    counter += 1

    if counter % 100000 == 0:
        print counter

print counter

print "shuffling..."

order = range(counter)
random.shuffle(order)

epoch = 0

while order:

    current_lines = {}
    current_lines_count = 0

    current_chunk = order[:lines_in_memory]
    current_chunk_dict = {x: 1 for x in current_chunk}  # faster "in"
    current_chunk_length = len(current_chunk)

    order = order[lines_in_memory:]

    i_f.seek(0)
    if preserve_headers:
        i_f.readline()

    count = 0

    for line in i_f:
        if count in current_chunk_dict:
            current_lines[count] = line
            current_lines_count += 1
            if current_lines_count == current_chunk_length:
                break
        count += 1
        if count % 100000 == 0:
            print count

    print "writing..."

    for l in current_chunk:
        o_f.write(current_lines[l])

    lines_saved = current_chunk_length + epoch * lines_in_memory
    epoch += 1
    print "pass %s complete (%s lines saved)" % (epoch, lines_saved)