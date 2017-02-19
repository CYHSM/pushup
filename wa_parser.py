"""
For parsing whatsapp chat logs, exported from an android whatsapp app.
"""
from datetime import datetime

import pandas as pd


def parse_chat_log(filepath):
    """
    Parses an exported whatsapp chatlog

    Inputs:
    - filepath : path to chatlog

    Returns:
    - parsed_df : pandas dataframe with date - sender - message
    """
    parsed_df = []
    lines = open(filepath, 'r')
    for line in lines:
        time, sender, message = parse_line(line.rstrip())
        if message == '':
            print(
                '----------------Did not process following message:---------------------')
            print(line)
            print(
                '-----------------------------------------------------------------------')
            continue
        parsed_df.append(
            {'Datetime': time, 'Sender': sender, 'Message': message})
    return pd.DataFrame(parsed_df)


def parse_line(line):
    """
    Parses one line of the chatlog

    Inputs:
    - line : One line from a whatsapp chatlog

    Returns:
    - tuple (time, sender, message) as strings
    """
    date_sender, sep, message = line.partition(': ')
    date, sep, sender = date_sender.partition(' - ')
    # A message can have a carriage return and then this will fail as the date
    # is the whole message
    try:
        time = datetime.strptime(date, '%d.%m.%y, %H:%M')
    except ValueError:
        return None, None, ''
    return time, sender, message
