# TelegramGroupStats
Obtain usage stats from any telegram group or chat.

## How to:
1. Export the telegram chat to html files using the telegram desktop client. Copy / save the files into the telegram-export-converter directory.

2. Run "telegram-export-converter.py" from within the directory. The script has been modified to create a json file instead of csv.

3. Run "get-stats.py" and pass the path to the json file.