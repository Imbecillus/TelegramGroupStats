# NOTE: This script needs the exported chat in JSON format. Pass the location of the file as the last argument.
print('TELEGRAM GROUP STATS')

# IMPORTS
import sys
import json
import argparse
from datetime import datetime

# FUNCTIONS
def sort_and_print(items, percentages=False, stop_at=None):
    sorted_items = sorted(items, key=lambda key_value: key_value[1], reverse=True)

    n = 0

    if not percentages:
        for name, number in sorted_items:
            print(f'{n} -- {name}: {number}')

            n += 1
            if stop_at is not None:
                if n == stop_at:
                    return
    else:
        total = percentages
        for name, number in sorted_items:
            print(f'{n} -- {name}: {number} ({round(100 * number / total, 2)}%)')

            n += 1
            if stop_at is not None:
                if n == stop_at:
                    return

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

parser = argparse.ArgumentParser(description='Analyses json exported Telegram chats for user activity, frequency of hashtags and #memberzahl.')
parser.add_argument('json_paths', metavar='P', type=str, nargs=argparse.REMAINDER, help='path(s) to the json exports')
parser.add_argument('--json', action='store_true', help='Save json exports')
parser.add_argument('--csv', action='store_true', help='Save csv exports')
parser.add_argument('--vis', dest='vis', action='store_true', help='Create visualizations')
parser.add_argument('--png', action='store_true', help='Save png exports of visualizations')
parser.add_argument('--member_history', nargs='?', help='Import a json file of past #memberzahl values')
parser.add_argument('--log', action='store_true', help='Logarithmic scales for visualizations')
parser.add_argument('--p', dest='print', nargs='?', type=int, help='Print p stats to command line. Set to -1 to print everything.')

arguments = parser.parse_args(sys.argv[1:])

show_visualization = arguments.vis
export_visualization = arguments.png
export_csv = arguments.csv
export_json = arguments.json
json_paths = arguments.json_paths
p = arguments.print

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
n = 0

print(f'Parsing through {n_messages} messages.')
members = {}
hashtags = {}
memberzahl_log = {}

# Importing memberzahl history (if given)
if arguments.member_history is not None:
    memberzahl_log = json.load(open(arguments.member_history, 'r', encoding='utf-8'))

newest_message = -1

for m in messagelist:
    log_memberzahl = False

    n = n + 1
    if n % int(0.05 * n_messages) == 0:
        print(f' {round(n / n_messages * 100, 2)}%')

    # Skip message, if the id is already logged in parsed_messages
    mid = int(m.get("id"))
    if mid < newest_message:
        print(f'  Message {mid} double; skipping')
        continue
    else:
        newest_message = mid

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
                print('  Unexpected occurence of #memberzahl; skipped')

    
print(f'Found {len(members)} people who wrote a message and {len(hashtags)} unique hashtags.')
print(f'Found {len(memberzahl_log)} times #memberzahl.')
print('')

# Sorting and printing...
print('HASHTAGS')
if p >= 0:
    sort_and_print(hashtags.items(), stop_at=p)
print(' ')

print('USERS')
if p >= 0:
    sort_and_print(hashtags.items(), percentages=n_messages, stop_at=p)

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
    plt.grid(True, axis='y', linestyle='--')
    if arguments.log:
        plt.yscale('log')
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
    if arguments.log:
        plt.yscale('log')
    plt.title(f"Hashtags in {chat_name}")
    plt.grid(True, axis='y', linestyle='--')
    plt.show()
    if export_visualization:
        plt.savefig(hashtags_file + '.png')

    print('   Memberzahl')
    plt.plot([datetime.strptime(x, '%Y-%m-%dT%H:%M:%S') for x in memberzahl_log.keys()], [y for y in memberzahl_log.values()])
    plt.title(f"User-Entwicklung in {chat_name}")
    plt.ylim(bottom=0)
    plt.grid(True, axis='both', linestyle='--')
    plt.show()
    if export_visualization:
        plt.savefig(memberzahl_file + '.png')