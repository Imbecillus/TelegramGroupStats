# NOTE: This script needs the exported chat in JSON format. Pass the location of the file as the first argument.
print('TELEGRAM GROUP STATS')

# IMPORTS
import sys
import json

# FUNCTIONS
def sort_and_print(items, percentages=False):
    sorted_items = sorted(items, key=lambda key_value: key_value[1], reverse=True)

    if not percentages:
        for name, number in sorted_items:
            print(f'{name}: {number}')
    else:
        total = percentages
        for name, number in sorted_items:
            print(f'{name}: {number} ({round(100 * number / total, 2)}%)')

def save_csv(dictionary, csv_path):
    with open(csv_path, 'w+', encoding='utf-8') as f:
        f.write('Entry;Count\n')
        for k in dictionary.keys():
            f.write(f'{k};{dictionary[k]}\n')
        f.close()
        
# Like str.strip(), but removes the entire rest of the string after a char has been found
def advanced_strip(word, characters):
    for i in range(len(characters)):
        c = characters[i]
        ix = word.find(c)
        if ix is not -1:
            word = word[:ix]

    return word


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
            if word.startswith('#'):
                # Find and remove characters that can't be part of hashtags
                word = advanced_strip(word, '()[]/\\?!%&.,;:-')

                # If there's more than the '#' left, add to the dictionary
                if len(word) > 1:
                    if word not in hashtags.keys():
                        hashtags[word] = 1
                    else:
                        hashtags[word] += 1
    
print(f'Found {len(members)} people who wrote a message and {len(hashtags)} unique hashtags.')
print('')

# Sorting and printing...
print('HASHTAGS')
sort_and_print(hashtags.items())
print(' ')

print('USERS')
sort_and_print(members.items(), percentages=n_messages)

# Export to csv
print('')
print('Saving stat json and csv files.')
members_file = json_path.split('\\')[-1][0:-5] + '_members'
hashtags_file = json_path.split('\\')[-1][0:-5] + '_hashtags'

# Export json files
json.dump(members, open(members_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(hashtags, open(hashtags_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)

# Export csv files
save_csv(members, members_file + '.csv')
save_csv(hashtags, hashtags_file + '.csv')