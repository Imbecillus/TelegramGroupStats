print('TELEGRAM GROUP STATS - User activity cloud')

import sys
import argparse
from wordcloud import WordCloud
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Creates a user activity cloud from get-stats.py exports.')
parser.add_argument('csv_path', metavar='P', type=str, help='Path to user activity csv')
parser.add_argument('-e', action='append', dest='excluded', help='User to be excluded, e.g. a bot')

arguments = parser.parse_args(sys.argv[1:])
csv_path = arguments.csv_path
excluded = arguments.excluded

# Import the target csv
print(f'Importing {csv_path}...')
userdict = {}
f = open(csv_path, 'r', encoding='utf-8')
f.readline()            # Skip title line
line = f.readline()     # Read first proper line
while line:
  line = line[:-1].split(';')
  user = line[0]
  count = int(line[1])

  if excluded and user in excluded:
    line = f.readline()
    continue
  
  userdict[user] = count
  line = f.readline()

cloud = WordCloud(width=1920, height=1080, background_color='white', min_font_size=24)
cloud.generate_from_frequencies(userdict)

plt.imshow(cloud, interpolation='bilinear')
plt.axis('off')
plt.show()