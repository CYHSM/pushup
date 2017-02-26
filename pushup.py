import sys
import wa_parser as wap

import numpy as np
import pandas as pd
import plotly as py
import plotly.figure_factory as FF
import plotly.graph_objs as go


def count_over_days(df):
    """
    Counts occurences of #N for each sender per day

    Inputs:
    - df: Hashtag extracted dataframe

    Returns:
    - Pandas dataframe with columns as sender names and rows as Dates
    """
    # Groupby days
    df_sum = df.groupby([pd.TimeGrouper(freq='d'), 'Name']
                        ).aggregate(np.sum).unstack()
    df_sum.fillna(value=0, inplace=True)
    df_sum.columns = df_sum.columns.droplevel()
    # Anonymize sender names
    df_sum = replace_names(df_sum)
    # Add cumsum dataframe
    df_cumsum = df_sum.cumsum()
    # Group by week to decide winner of week
    df_weekly = df_sum.groupby(pd.TimeGrouper(freq='w')).aggregate(np.sum)

    return df_sum, df_cumsum, df_weekly


def extract_hashtags(df, column_names=['Name', 'Pushups']):
    """
    Extracts hashtags from dataframe

    Inputs:
    - df: pandas dataframe with date - sender - message

    Returns:
    - Pandas dataframe with extracted rows
    """
    df.is_copy = False  # Get rid of chain warning.
    df_name_value = extract_name_value_pairs(df, column_names)
    df.rename(columns={'Message': column_names[1]}, inplace=True)
    # Replace # and convert to number
    df[column_names[1]] = pd.to_numeric(
        df[column_names[1]].str.extract('#(\d*)'))
    df.dropna(inplace=True)

    # Concatenate
    df = pd.concat([df, df_name_value]).sort_index()

    return df


def extract_name_value_pairs(df, column_names):
    """
    Extracts name-value pairs as for example '#Manu#190'

    Inputs:
    - df: pandas dataframe with date - sender - message

    Returns:
    - Pandas dataframe with Name and named column
    """
    df = df['Message'].str.extract('#(\w*)#(\d*)', expand=True)
    df.dropna(inplace=True)
    df.columns = column_names
    df[column_names[1]] = pd.to_numeric(df[column_names[1]])

    return df


def replace_names(df):
    """
    Anonymize sender names

    Inputs:
    - df : pandas dataframe with real names
    """
    # replace_dict = {'CYHSM': 'Gandalf', 'Simon Malik': 'Boromir',
    #                 'Robert Skotschi': 'Legolas', 'Jannis Plöger': 'Aragorn'}
    replace_dict = {'CYHSM': 'Markus', 'Simon Malik': 'Simon',
                    'Robert Skotschi': 'Robert', 'Jannis Plöger': 'Jannis', 'Manu': 'Manuel'}
    return df.rename(columns=replace_dict)


def create_leaderboard(df_weekly, winning_point=1):
    """
    Checks who had the most pu in a week and rewards one point

    Inputs:
    - df_weekly : Dataframe grouped by week
    - winning_point : How many points for one win
    """
    points = df_weekly.idxmax(axis=1).value_counts()
    df_leaderboard = pd.DataFrame(points, index=df_weekly.columns, columns=[
                                  'Points']).fillna(value=0)
    df_leaderboard['Points'] = df_leaderboard['Points'].astype(int)

    return df_leaderboard


def analyse_chatlog(filepath):
    """
    Analyses new chatlog

    Inputs:
    - filepath : Path to chatlog
    """
    df_parsed = wap.parse_chat_log(filepath)
    df_extracted = extract_hashtags(df_parsed)
    df_sum, df_cumsum, df_weekly = count_over_days(df_extracted)
    df_leaderboard = create_leaderboard(df_weekly)
    # Plots
    plot_leaderboard(df_leaderboard)
    plot_cumulative_all(df_extracted)
    plot_current_week_and_total(df_cumsum)
    plot_distribution(df_extracted)
    plot_stats(df_sum)

    return df_extracted, df_sum, df_cumsum, df_weekly, df_leaderboard


# -----------------------------------------------------------------------------
# ----------------------------Plotting-----------------------------------------
# -----------------------------------------------------------------------------
def plot_offline(plot, filename):
    py.offline.plot(
        plot, filename=filename, show_link=False)


def plot_leaderboard(df_leaderboard):
    table = FF.create_table(df_leaderboard, index=True)
    table.layout.autosize = True
    plot_offline(table, './docs/plots/current_leaderboard.html')


def plot_stats(df_sum):
    df_stats = df_sum.describe()
    df_stats.drop(['count', '25%', '50%', '75%'], inplace=True)
    df_stats = df_stats.round(decimals=2)
    df_stats.rename(columns={
                    'mean': 'Mean', 'std': 'Standard Deviation', 'min': 'Minimum', 'Max': 'Maximum'})
    table = FF.create_table(df_stats, index=True)
    table.layout.autosize = True
    plot_offline(table, './docs/plots/current_stats.html')


def plot_current_week_and_total(df_cumsum):
    # Current week
    df_thisweek = df_cumsum[
        df_cumsum.index.week == np.max(df_cumsum.index.week)]
    # Set start to zero
    df_thisweek = df_thisweek - \
        df_cumsum[df_cumsum.index.week == np.max(
            df_cumsum.index.week) - 1].iloc[-1]
    data = [{
        'x': df_thisweek.index,
        'y': df_thisweek[col],
        'name': col
    } for col in df_thisweek.columns]
    layout = go.Layout(title='Cumulative Sum (Current)',
                       xaxis=dict(title='Date'), yaxis=dict(title='Pushup Count'),
                       showlegend=False)
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/current_week.html')

    # Total
    data_total = [{
        'x': df_cumsum.index,
        'y': df_cumsum[col],
        'name': col
    } for col in df_cumsum.columns]
    layout = go.Layout(title='Cumulative Sum (Total)',
                       xaxis=dict(title='Date'), yaxis=dict(title='Pushup Count'))
    fig = go.Figure(data=data_total, layout=layout)
    plot_offline(fig, './docs/plots/total.html')


def plot_cumulative_all(df):
    df_cumsum = df['Pushups'].cumsum()
    data = [{
        'x': df_cumsum.index,
        'y': df_cumsum.values,
        'name': 'Pushups'
    }]
    layout = go.Layout(
        xaxis=dict(title='Date'), yaxis=dict(title='Pushup Count'),
        showlegend=False,
        height=300,
        margin=go.Margin(
            l=50, r=50, b=100, t=20, pad=4
        ))
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/total_pushups.html')


def plot_distribution(df):
    data = [go.Histogram(x=df['Pushups'], nbinsx=10, opacity=0.75)]
    layout = go.Layout(title='Distribution of Pushups per Set',
                       xaxis=dict(showgrid=True), bargap=0.25,
                       margin=go.Margin(
                           l=20, r=20, b=40, t=60, pad=4
                       ))
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/current_distribution.html')


if __name__ == "__main__":
    analyse_chatlog(sys.argv[1])
