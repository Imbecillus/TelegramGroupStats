# NOTE: This script needs the exported chat in JSON format. Pass the location of the file as the last argument.
print('TELEGRAM GROUP STATS')

# IMPORTS
import sys
import json
import argparse
import random
from datetime import datetime
from datetime import timedelta

custom_stop_words = ['https', 'http', 'schon', 'immer', 'halt', 'wäre', 'mehr', 'heute', 'morgen', 'gestern', 'ganz', 'hätte', 'hast', 'gerade', 'einfach', 'gibt']

# FUNCTIONS
def sort_and_print(items, percentages=False, stop_at=None, replace_member_names=False):
    sorted_items = sorted(items, key=lambda key_value: key_value[1], reverse=True)

    n = 0

    if not percentages:
        for name, number in sorted_items:
            if replace_member_names:
                name = name_from_uid[name]

            print(f'{n+1} -- {name}: {number}')

            n += 1
            if stop_at is not None:
                if n == stop_at:
                    return
    else:
        total = percentages
        for name, number in sorted_items:
            if replace_member_names:
                name = name_from_uid[name]

            print(f'{n+1} -- {name}: {number} ({round(100 * number / total, 2)}%)')

            n += 1
            if stop_at is not None:
                if n == stop_at:
                    return

def save_csv(dictionary, csv_path, replace_member_names=False):
    with open(csv_path, 'w+', encoding='utf-8') as f:
        f.write('Entry;Count\n')
        for k in dictionary.keys():
            if not replace_member_names:
                f.write(f'{k};{dictionary[k]}\n')
            else:
                f.write(f'{name_from_uid[k]};{dictionary[k]}\n')
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
parser.add_argument('--from', dest='starting_time', nargs='?', help='Starting timestamp. Format: "YYYY/MM/DD-HH:MM:SS"')
parser.add_argument('--to', dest='stopping_time', nargs='?', help='Stopping timestamp. Format: "YYYY/MM/DD-HH:MM:SS"')
parser.add_argument('--hashtag', dest='hashtag_export', action='append', help='Specify a hashtag. The script will find each occurence of the hashtag and the message it was used in reply to and export it as a csv list. Can be used multiple times for multiple hashtags.')
parser.add_argument('--wc', dest='word_cloud', action='store_true', help='Generate word cloud.')
parser.add_argument('--wcu', dest='word_cloud_users', type=str, metavar='uid', action='append', help='Generate word cloud for user [uid]. Can be used multiple times for multiple word clouds.')
parser.add_argument('--e', dest='emojis', action='store_true', help='Count emoji stats')
parser.add_argument('--d', dest='directions', action='store_true', help='Count stats for directions')
parser.add_argument('--image', dest='image', nargs='?', help='An image to be used for wordcloud generation')
parser.add_argument('--in', dest='config', type=str, help='A config file which contains one json path per line')
parser.add_argument('--user_dict', dest='userdict', type=str, help='A json file which contains a dictionary of user ids and names')

arguments = parser.parse_args(sys.argv[1:])

show_visualization = arguments.vis
export_visualization = arguments.png
export_csv = arguments.csv
export_json = arguments.json
if arguments.hashtag_export is not None:
    export_hashtags = [x.lower() for x in arguments.hashtag_export]
else:
    export_hashtags = []
    json_paths = []
if arguments.config:
    with open(arguments.config, 'r', encoding='utf-8') as f:
        line = f.readline()
        while line:
            json_paths.append(line.replace('\n', ''))
            line = f.readline()
if arguments.json_paths:
    for x in arguments.json_paths:
        json_paths.append(x)
print(json_paths)
p = arguments.print
generate_wordcloud = arguments.word_cloud
if generate_wordcloud:
    from stop_words import safe_get_stop_words
    stop_words = safe_get_stop_words('de')
    for word in custom_stop_words:
        stop_words.append(word)
    print('Stop words:')
    print(stop_words)
    if arguments.image:
        import numpy as np
        from PIL import Image
        wordcloud_mask = np.array(Image.open(arguments.image))
        use_mask = True
    else:
        wordcloud_mask = None
        use_mask = False

wordcloud_users = arguments.word_cloud_users
if arguments.starting_time is not None:
    starting_time = datetime.strptime(arguments.starting_time, '%Y/%m/%d-%H:%M:%S')
else:
    starting_time = None
if arguments.stopping_time is not None:
    stopping_time = datetime.strptime(arguments.stopping_time, '%Y/%m/%d-%H:%M:%S')
else:
    stopping_time = None
emojis = arguments.emojis
directions = arguments.directions

# Importing chat exports
messagelist = {}
for json_path in json_paths:
    print(f'Importing chat export from {json_path}', end=' ')
    json_dict = json.load(open(json_path, 'r', encoding='utf-8'))
    chat_name = json_dict['name']
    json_dict = json_dict['messages']
    for m in json_dict:
        messagelist[m['id']] = m
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

# Initialize member dictionary and import (if given)
name_from_uid = {}
if arguments.userdict is not None:
    name_from_uid = json.load(open(arguments.userdict, 'r', encoding='utf-8'))

# Initialize dictionary of hashtag histories
hashtag_history = {}
for hashtag in export_hashtags:
    hashtag_history[hashtag] = []

# Initialize dictionaries for wordclouds
all_words = {}
user_wordclouds = {}

# Initialize dictionary for emojis
if emojis:
    dict_emojis = {}
    emoji_names = {}
    import demoji
    demoji.download_codes()

# Initialize dictionary for directions
if directions:
    dict_directions = {}

newest_message = -1

for m_id in messagelist.keys():
    m = messagelist[m_id]
    log_memberzahl = False

    n = n + 1
    if n % int(0.05 * n_messages) == 0:
        print(f' {round(n / n_messages * 100, 2)}%')

    # Skip message if it is from before the set starting time
    if starting_time is not None:
        m_time = m.get('date')
        m_time = datetime.strptime(m_time, '%Y-%m-%dT%H:%M:%S')
        difference = m_time - starting_time
        if (difference / timedelta(seconds=1)) < 0:
            continue
        else:
            print(f'  Reached starting time ({starting_time})')
            starting_time = None

    # Skip message if it is from after the set stopping time
    if stopping_time is not None:
        m_time = m.get('date')
        m_time = datetime.strptime(m_time, '%Y-%m-%dT%H:%M:%S')
        difference = stopping_time - m_time
        if (difference / timedelta(seconds=1)) <= 0:
            print(f'  Reached stopping time ({stopping_time})')
            break

    # Get sender id, but ignore "user" prefix for compatibility with old exports
    sender = str(m.get('from_id', None)).replace('user', '')
    if sender:
        if sender not in members.keys():
            members[sender] = 1
        else:
            members[sender] += 1

        if sender not in name_from_uid.keys():
            name_from_uid[sender] = m.get('from', None)

    text = m.get('text', None)
    if text:
        # Strip formatting
        text = strip_formatting(text)

        # Replace newlines with whitespace
        text = text.replace('\\n',' ').lower()
        text = text.replace('\n',' ').lower()

        # Get emojis in message text
        if emojis:
            msg_emojis = demoji.findall(text)
            for e in msg_emojis.keys():
                if e in dict_emojis:
                    dict_emojis[e] += 1
                else:
                    dict_emojis[e] = 1
                    emoji_names[e] = msg_emojis[e]

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

                if word[1:] in export_hashtags:
                    hashtag_message = strip_formatting(m.get('text', None)).replace('\n', ' ')
                    
                    replied_to_message = m.get('reply_to_message_id', None)
                    if replied_to_message is not None:
                        replied_to_message = messagelist.get(replied_to_message, None)
                        if replied_to_message is not None:
                            replied_to_message = strip_formatting(replied_to_message.get('text', None)).replace('\n', ' ')

                    tagging_user = m.get('from', None)

                    new_entry = [tagging_user, replied_to_message, hashtag_message]
                    hashtag_history[word[1:]].append(new_entry)
            elif directions and word.startswith('*') and word.endswith('*'):
                if word not in dict_directions:
                    dict_directions[word] = 1
                else:
                    dict_directions[word] += 1
            else:
                word = advanced_strip(word, '()[]/\\?!%&.,;:-')
                if generate_wordcloud:
                    if len(word) > 3 and word not in stop_words:
                        if word not in all_words:
                            all_words[word] = 1
                        else:
                            all_words[word] += 1

                    if wordcloud_users and sender in wordcloud_users:
                        if sender not in user_wordclouds:
                            user_wordclouds[sender] = {}

                        if len(word) > 3 and word not in stop_words and not word.startswith('@'):
                            if word not in user_wordclouds[sender]:
                                user_wordclouds[sender][word] = 1
                            else:
                                user_wordclouds[sender][word] += 1

        
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
    sort_and_print(members.items(), percentages=n_messages, stop_at=p, replace_member_names=True)

if emojis:
    print('EMOJIS')
    if p >= 0:
        emoji_name_dict = {}
        for e in dict_emojis:
            emoji_name_dict[emoji_names[e]] = dict_emojis[e]
        sort_and_print(emoji_name_dict.items(), percentages=n_messages, stop_at=p)

if directions:
    print('DIRECTIONS')
    if p >= 0:
        sort_and_print(dict_directions.items(), stop_at=p)

members_file = json_path.split('\\')[-1][0:-5] + '_members'
hashtags_file = json_path.split('\\')[-1][0:-5] + '_hashtags'
memberzahl_file = json_path.split('\\')[-1][0:-5] + '_memberzahl'
words_file = json_path.split('\\')[-1][0:-5] + '_words'
emojis_file = json_path.split('\\')[-1][0:-5] + '_emojis'
directions_file = json_path.split('\\')[-1][0:-5] + '_directions'

# Export json files
if export_json:
    print('Exporting json files...')
    json.dump(members, open(members_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(hashtags, open(hashtags_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(memberzahl_log, open(memberzahl_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(name_from_uid, open(members_file + '_key.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(all_words, open(words_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if emojis:
        json.dump(dict_emojis, open(emojis_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if directions:
        json.dump(dict_directions, open(directions_file + '.json', 'w', encoding='utf-8'), ensure_ascii=False)

# Export csv files
if export_csv:
    print('Exporting csv files...')
    save_csv(members, members_file + '.csv', True)
    save_csv(hashtags, hashtags_file + '.csv')
    save_csv(memberzahl_log, memberzahl_file + '.csv')
    save_csv(all_words, words_file + '.csv')
    if emojis:
        save_csv(dict_emojis, emojis_file + '.csv')
    if directions:
        save_csv(dict_directions, directions_file + '.csv')

for hashtag in export_hashtags:
    print(f'Exporting csv file for {hashtag}...')
    path = json_path.split('\\')[-1][0:-5] + '_' + hashtag + '.csv'
    with open(path, 'w+', encoding='utf-8') as f:
        f.write('Tagger;Feedline;Punchline\n')

        for entry in hashtag_history[hashtag]:
            f.write(f'"{entry[0]}";"{entry[1]}";"{entry[2]}"\n')
        f.close()

if show_visualization:
    print('Showing visualizations...')
    import matplotlib.pyplot as plt

    print('   Users')
    members = {k: v for k, v in sorted(members.items(), key=lambda item: item[1])}
    keys = [k for k in members.keys()]
    for k in keys:
        if members[k] < 100:
            members.pop(k)

    plt.bar([x + 1 for x in range(len(members))], [members[x] for x in members.keys()])
    plt.xticks([x + 1 for x in range(len(members))], [name_from_uid[x] for x in members.keys()], rotation='vertical', fontsize='x-small')
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
        if hashtags[k] < 10:
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

    if emojis:
        print('   Emojis')
        dict_emojis = {k: v for k, v in sorted(dict_emojis.items(), key=lambda item: item[1])}

        plt.bar([x + 1 for x in range(len(dict_emojis))], [dict_emojis[x] for x in dict_emojis.keys()])
        plt.xticks([x + 1 for x in range(len(dict_emojis))], [x for x in dict_emojis.keys()], rotation='vertical', fontsize='x-small')
        if arguments.log:
            plt.yscale('log')
        plt.title(f"Emojis in {chat_name}")
        plt.grid(True, axis='y', linestyle='--')
        plt.show()

    if directions:
        print('   Directions')
        dict_directions = {k: v for k, v in sorted(dict_directions.items(), key=lambda item: item[1])}

        plt.bar([x + 1 for x in range(len(dict_directions))], [dict_directions[x] for x in dict_directions.keys()])
        plt.xticks([x + 1 for x in range(len(dict_directions))], [x for x in dict_directions.keys()], rotation='vertical', fontsize='x-small')
        if arguments.log:
            plt.yscale('log')
        plt.title(f"Directions in {chat_name}")
        plt.grid(True, axis='y', linestyle='--')
        plt.show()

    print('   Memberzahl')
    plt.plot([datetime.strptime(x, '%Y-%m-%dT%H:%M:%S') for x in memberzahl_log.keys()], [y for y in memberzahl_log.values()])
    plt.title(f"User-Entwicklung in {chat_name}")
    plt.ylim(bottom=0)
    plt.grid(True, axis='both', linestyle='--')
    plt.show()
    if export_visualization:
        plt.savefig(memberzahl_file + '.png')

if generate_wordcloud:
    print('Generating word clouds...')
    from wordcloud import WordCloud, ImageColorGenerator
    import matplotlib.colors as clr
    import matplotlib.pyplot as plt

    print(' Overall word cloud')

    cloud_all = WordCloud(width=1920, height=1080, background_color='white', mask=wordcloud_mask)
    cloud_all.generate_from_frequencies(all_words)

    if use_mask:
        the_colors = [[22, 91, 51], [20, 107, 58], [248, 178, 41], [234, 70, 48], [187, 37, 40]]
        def christmas_colors(word, font_size, position, orientation, random_state=None, **kwargs):
            r = random.randint(0, 4)
            return f'rgb({the_colors[r][0]}, {the_colors[r][1]}, {the_colors[r][2]})'
        plt.imshow(cloud_all.recolor(color_func=christmas_colors), interpolation='bilinear')
    else:
        plt.imshow(cloud_all, interpolation='bilinear')
    plt.axis('off')
    plt.show()

    print(' User word clouds...')
    for user in user_wordclouds:
        name = name_from_uid[user]
        print(f'   {name}')
        cloud_dict = user_wordclouds[user]
        cloud_user = WordCloud(width=1920, height=1080, background_color='white', mask=wordcloud_mask, contour_color='black', contour_width=1)
        cloud_user.generate_from_frequencies(cloud_dict)
        if use_mask:
            image_colors = ImageColorGenerator(wordcloud_mask)
            cloud_user.recolor(color_func=image_colors)
            plt.imshow(cloud_user.recolor(color_func=image_colors), interpolation='bilinear')
            plt.axis('off')
            plt.title(name)
            plt.show()
        else:
            plt.imshow(cloud_user, interpolation='bilinear')
            plt.axis('off')
            plt.title(name)
            plt.show()

    if directions:
        print(' Directions word cloud...')
        cloud_directions = WordCloud(width=1920, height=1080, background_color='white', mask=wordcloud_mask)
        cloud_directions.generate_from_frequencies(dict_directions)
        plt.imshow(cloud_directions, interpolation='bilinear')
        plt.axis('off')
        plt.show()