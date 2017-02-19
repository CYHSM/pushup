import sys
import wa_parser as wap

import pandas as pd


def count_over_days(df):
    """
    Counts occurences of #N for each sender per day

    Inputs:
    - df: pandas dataframe with date - sender - message

    Returns:
    - Pandas dataframe with columns as sender names and rows as Dates
    """
    # Find occurences of #d
    df = df[df['Message'].str.contains(r'#\d')]
    df.is_copy = False  # Get rid of chain warning.
    # Replace # and convert to number
    df['Message'] = pd.to_numeric(df['Message'].str.extract('#(\d*)'))
    # Add column with just the day
    df['Date'] = df['Datetime'].dt.date
    # Sum over dates and sender. Awesome pandas
    df_sum = pd.pivot_table(df, values='Message', index='Date',
                            columns='Sender', aggfunc='sum')
    df_sum.fillna(value=0, inplace=True)
    # Anonymize sender names
    df_sum = replace_names(df_sum)
    # Add cumsum dataframe
    df_cumsum = df_sum.cumsum()
    # Add row with total sum
    df_sum.loc['Total'] = df_sum.sum(axis=0, numeric_only=True)

    return df, df_sum, df_cumsum


def replace_names(df):
    """
    Anonymize sender names

    Inputs:
    - df : pandas dataframe with real names
    """
    replace_dict = {'CYHSM': 'Gandalf', 'Simon Malik': 'Boromir',
                    'Robert Skotschi': 'Legolas', 'Jannis Plöger': 'Aragorn'}
    return df.rename(columns=replace_dict)


def analyse_chatlog(filepath):
    """
    Analyses new chatlog

    Inputs:
    - filepath : Path to chatlog
    """
    parsed_df = wap.parse_chat_log(filepath)
    df, df_sum, df_cumsum = count_over_days(parsed_df)

    return df, df_sum, df_cumsum


if __name__ == "__main__":
    analyse_chatlog(sys.argv[1])
