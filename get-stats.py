# NOTE: This script needs the exported chat in JSON format. Pass the location of the file as the last argument.
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

def strip_formatting(input):
    if type(input) is list:
        text = ""

        for text_part in input:
            if type(text_part) is dict:
                text += text_part['text']
            else:
                text += text_part

        return text
    else:
        return input

# Parsing arguments
json_paths = []
export_csv = False
export_json = False
show_visualization = False
export_visualization = False
for argument in sys.argv[1:]:
    if argument == '-csv':
        export_csv = True
    elif argument == '-json':
        export_json = True
    elif argument == '-v':
        show_visualization = True
    elif argument == '-png':
        export_visualization = True
    else:
        if not argument.startswith('-'):
            json_paths.append(argument)

# Importing chat exports
messagelist = []
for json_path in json_paths:
    print(f'Importing chat export from {json_path}', end=' ')
    json_dict = json.load(open(json_path, 'r', encoding='utf-8'))
    chat_name = json_dict['name']
    json_dict = json_dict['messages']
    for m in json_dict:
        messagelist.append(m)
    print('done.')

n_messages = len(messagelist)

print(f'Parsing through {n_messages} messages.')
members = {}
hashtags = {}
memberzahl_log = {}
for m in messagelist:
    log_memberzahl = False

    sender = m.get('from', None)
    if sender:
        if sender not in members.keys():
            members[sender] = 1
        else:
            members[sender] += 1

    text = m.get('text', None)
    if text:
        # Strip formatting
        text = strip_formatting(text)

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

                if word == '#memberzahl':
                    log_memberzahl = True
        
        if log_memberzahl and len(text) == 2:
            # Contains #memberzahl and only two words. One is the hashtag, the other is the number
            try:
                if text[0] == "#memberzahl":
                    memberzahl = int(text[1].replace('.', ''))
                else:
                    memberzahl = int(text[0].replace('.', ''))

                timestamp = m.get('date')
                
                memberzahl_log[timestamp] = memberzahl
            except:
                print('Unexpected occurence of #memberzahl; skipped')

    
print(f'Found {len(members)} people who wrote a message and {len(hashtags)} unique hashtags.')
print(f'Found {len(memberzahl_log)} times #memberzahl.')
print('')

# Sorting and printing...
print('HASHTAGS')
sort_and_print(hashtags.items())
print(' ')

print('USERS')
sort_and_print(members.items(), percentages=n_messages)

members_file = json_path.split('\\')[-1][0:-5] + '_members'
hashtags_file = json_path.split('\\')[-1][0:-5] + '_hashtags'
memberzahl_file = json_path.split('\\')[-1][0:-5] + '_memberzahl'

# Export json files
if export_json:
    print('Exporting json files...')
    json.dump(members, open(members_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(hashtags, open(hashtags_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(memberzahl_log, open(memberzahl_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)

# Export csv files
if export_csv:
    print('Exporting csv files...')
    save_csv(members, members_file + '.csv')
    save_csv(hashtags, hashtags_file + '.csv')
    save_csv(memberzahl_log, memberzahl_file + '.csv')

if show_visualization:
    print('Showing visualizations...')
    import matplotlib.pyplot as plt

    print('   Users')
    members = {k: v for k, v in sorted(members.items(), key=lambda item: item[1])}
    keys = [k for k in members.keys()]
    for k in keys:
        if members[k] < 250:
            members.pop(k)

    plt.bar([x + 1 for x in range(len(members))], [members[x] for x in members.keys()])
    plt.xticks([x + 1 for x in range(len(members))], [x for x in members.keys()], rotation='vertical', fontsize='x-small')
    plt.title(f"User-Aktivität in {chat_name}")
    plt.show()
    if export_visualization:
        plt.savefig(members_file + '.png')

    print('   Hashtags')
    hashtags = {k: v for k, v in sorted(hashtags.items(), key=lambda item: item[1])}
    keys = [k for k in hashtags.keys()]
    for k in keys:
        if hashtags[k] < 75:
            hashtags.pop(k)

    plt.bar([x + 1 for x in range(len(hashtags))], [hashtags[x] for x in hashtags.keys()])
    plt.xticks([x + 1 for x in range(len(hashtags))], [x for x in hashtags.keys()], rotation='vertical', fontsize='x-small')
    plt.title(f"Hashtags in {chat_name}")
    plt.show()
    if export_visualization:
        plt.savefig(hashtags_file + '.png')

    print('   Memberzahl')
    plt.plot([x for x in memberzahl_log.keys()], [y for y in memberzahl_log.values()])
    plt.title(f"User-Entwicklung in {chat_name}")
    ticks = [x for x in memberzahl_log.keys()]
    ticks = [ticks[0], ticks[-1]]
    plt.xticks(ticks)
    plt.ylim(bottom=0)
    plt.show()
    if export_visualization:
        plt.savefig(memberzahl_file + '.png')