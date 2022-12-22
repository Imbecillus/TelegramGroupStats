import argparse
import json
import sys

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



print('SELECTIVE PARSE')

parser = argparse.ArgumentParser(description='Selective export of messages containing the given phrases.')
parser.add_argument('-p', dest='phrases', action='append', type=str)
parser.add_argument('-i', dest='input_config', type=str)
parser.add_argument('-o', dest='output_path', type=str)

arguments = parser.parse_args(sys.argv[1:])

phrases = arguments.phrases
input_config = arguments.input_config
output_path = arguments.output_path

json_paths = []

with open(input_config, 'r', encoding='utf-8') as f:
        line = f.readline()
        while line:
            json_paths.append(line.replace('\n', ''))
            line = f.readline()

# Importing chat exports
messagelist = {}
for json_path in json_paths:
    print(f'Importing chat export from {json_path}', end=' ')
    json_dict = json.load(open(json_path, 'r', encoding='utf-8'))
    json_dict = json_dict['messages']
    for m in json_dict:
        messagelist[m['id']] = m
    print('done.')

n_messages = len(messagelist)
n = 0

print(f'Parsing through {n_messages} messages and exporting those which contain the following phrases:')
print(phrases)

text_out = ''

for m_id in messagelist.keys():
  n = n + 1
  if n % int(0.05 * n_messages) == 0:
        print(f' {round(n / n_messages * 100, 2)}%')

  message = messagelist[m_id]

  # Skip everything that is not a message
  if message.get('type') != 'message':
    continue

  text = message.get('text')
  sender = message.get('from')
  date = message.get('date')

  # Strip formatting
  text = strip_formatting(text)

  # Replace newlines with whitespace
  text = text.replace('\\n',' ')
  text = text.replace('\n',' ')

  for phrase in phrases:
    if phrase.lower() in text.lower():
      message_text = f'{sender} ({date}): {text}\n\n'
      text_out += message_text

with open(output_path, 'w', encoding='utf-8') as f:
  f.writelines(text_out)
