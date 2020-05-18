# NOTE: This script needs the exported chat in JSON format. Pass the location of the file as the first argument.
print('TELEGRAM GROUP STATS')

import sys
import json

json_path = sys.argv[1]
print(f'Importing chat export from {json_path}', end=' ')
json_dict = json.load(open(json_path, 'r', encoding='utf-8'))
print('done.')

n_messages = len(json_dict)

print(f'Parsing through {n_messages} messages.')
members = {}
hashtags = {}
for m in json_dict:
    sender = json_dict[m].get('sender', None)
    if sender:
        if sender not in members.keys():
            members[sender] = 1
        else:
            members[sender] += 1

    text = json_dict[m].get('content', None)
    if text:
        # Replace newlines with whitespace
        text = text.replace('\\n',' ').lower()

        # Look for hashtags in message text
        text = text.split()

        for word in text:
            if word.startswith('#') and len(word) > 1:
                if word not in hashtags.keys():
                    hashtags[word] = 1
                else:
                    hashtags[word] += 1
    
print(f'Found {len(members)} people who wrote a message and {len(hashtags)} unique hashtags.')
print('')

# Sorting and printing...
def sort_and_print(items, percentages=False):
    sorted_items = sorted(items, key=lambda key_value: key_value[1], reverse=True)

    if not percentages:
        for name, number in sorted_items:
            print(f'{name}: {number}')
    else:
        total = percentages
        for name, number in sorted_items:
            print(f'{name}: {number} ({round(100 * number / total, 2)}%)')

print('HASHTAGS')
sort_and_print(hashtags.items())
print(' ')

print('USERS')
sort_and_print(members.items(), percentages=n_messages)