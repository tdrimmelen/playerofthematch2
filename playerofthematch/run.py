from webwhatsapi import WhatsAPIDriver
import os
import pickle
from datetime import datetime
import time
from fuzzywuzzy import fuzz, process
import csv
import operator

### Utility functions   
def ensure_dir(file_path):
    if not os.path.exists(file_path):
        os.mkdir(file_path)

def get_player_list():
    with open('input/player_list.csv', 'r') as f:
        return f.read().splitlines()
        
def write_to_csv(file, contents):
    with open(file, 'w', encoding="utf-8") as f:
        writer = csv.writer(f)
        for key, value in contents:
            writer.writerow([key, value])

def write_player_tallies(output_folder, player_tallies):
    ensure_dir(output_folder)
    output_filename = './' + output_folder + '/player_tallies_' + datetime.now().strftime('%H-%M-%S')  + '.csv'
    write_to_csv(output_filename, sorted(player_tallies.items(), key=operator.itemgetter(1), reverse=True))

def write_submission_log(output_folder, submission_log):
    ensure_dir(output_folder)
    output_filename = './' + output_folder + '/submission_log' + datetime.now().strftime('%H-%M-%S')  + '.csv'
    write_to_csv(output_filename, submission_log.items())

### Parameters
match_name = input('Voer de wedstrijd in:')
start_time = datetime.now()
output_folder = 'output/' + start_time.strftime('%Y-%m-%d') + match_name
sleep_time = 60
match_threshold = 80

submission_log = {}
player_options = get_player_list()
player_tallies = {player: 0 for player in player_options}

# Main loop
profiledir = os.path.join(".", "firefox_cache")
if not os.path.exists(profiledir):
    os.makedirs(profiledir)

driver = WhatsAPIDriver(
    profile=profiledir, client="remote", command_executor=os.environ["SELENIUM"]
)
driver.wait_for_login()
#driver = WhatsAPIDriver(loadstyles=True)

while not driver.is_logged_in():
    print('Waiting for login...')
    time.sleep(10)

try:
    while True:
        messages_by_sender = driver.get_unread()
        print('{} berichten ontvangen. Verwerken...'.format(len(messages_by_sender)))
        for contact in messages_by_sender:
            for message in contact.messages:
                try:
                    best_player_match, match_value = process.extractOne(message.content, player_options)
                    print('Message received from: {}. Match value: {}. Text: {}'.format(message.sender.id, match_value, message.content))
                    print(message.sender.id)
                except AttributeError:
                    best_player_match = "Player match failed: AtrributeError"
                    match_value = 0
                    print('Message received from: {}. Match failed due to AttributeError'.format(message.sender.id))

                if (match_value > match_threshold):
                    if (message.sender.id not in submission_log.keys()):
                        #print "Bedankt voor het stemmen op The Erima Player Of The Match! Je hebt gestemd op {}. Je kunt niet nog een keer stemmen.".format(best_player_match)
                        player_tallies[best_player_match] += 1
                        submission_log[message.sender.id] = (message.content, best_player_match, match_value)

        write_player_tallies(output_folder, player_tallies)
        write_submission_log(output_folder, submission_log)
        print('Logs geschreven.')
        print('Wachten voor {} seconden...'.format(sleep_time))
        time.sleep(sleep_time)
except KeyboardInterrupt:
    print('Onderbroken door gebruiker. Laatste records wegschrijven...')
    write_player_tallies(output_folder, player_tallies)
    write_submission_log(output_folder, submission_log)
    print('Logs geschreven.')
    print('Klaar! Succesvol afgesloten.')
