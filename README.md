# TelegramGroupStats
Obtain usage stats from any telegram group or chat.

## How to:
1. Export the telegram chat to a json file using the telegram desktop client. Copy / save the files into the TelegramGroupStats directory.

2. Run "get-stats.py" and pass the path to the json file. (Paths to multiple files may be given and will be combined.)

3. The script will parse the json exports and give: The list of most active users, a list of most-used hashtags and the number of users in the group over time (provided it has regularly been protocolled using the hashtag #memberzahl).

## Required arguments:
* --p: How many entries to print for each list.


## Optional arguments:
* --csv: Export stats as csv files
* --e: Count emoji stats.
* --from: Specify a starting timestamp (format: YYYY/MM/DD-HH:MM:SS)
* --hashtag: Specify a hashtag. The script will find each occurence of the hashtag and the message it was used in reply to and export it as a csv list. Multiple hashtags can be specified.
* --json: Export stats as json files
* --log: Use logarithmic scales for visualizations
* --member_history [PATH]: Import a json file of past #memberzahl values.
* --png: Export the visualizations
* --to: Specify a stopping timestamp (format: YYYY/MM/DD-HH:MM:SS)
* --v: Create and display visualizations
* --wc: Generate a word cloud.
* --wcu [uid]: Additionally specify a user id. The script will also generate a word cloud for just this user.
* --image [PATH]: Specify the path to an image to be used as a mask for the shapes of the word clouds.