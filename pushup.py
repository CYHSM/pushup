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
    - df: pandas dataframe with date - sender - message

    Returns:
    - Pandas dataframe with columns as sender names and rows as Dates
    """
    df.is_copy = False  # Get rid of chain warning.
    df.rename(columns={'Message': 'Pushups'}, inplace=True)
    # Replace # and convert to number
    df['Pushups'] = pd.to_numeric(df['Pushups'].str.extract('#(\d*)'))
    df.dropna(inplace=True)
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

    return df, df_sum, df_cumsum, df_weekly


def replace_names(df):
    """
    Anonymize sender names

    Inputs:
    - df : pandas dataframe with real names
    """
    replace_dict = {'CYHSM': 'Gandalf', 'Simon Malik': 'Boromir',
                    'Robert Skotschi': 'Legolas', 'Jannis Plöger': 'Aragorn'}
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
    parsed_df = wap.parse_chat_log(filepath)
    df, df_sum, df_cumsum, df_weekly = count_over_days(parsed_df)
    df_leaderboard = create_leaderboard(df_weekly)

    return df, df_sum, df_cumsum, df_weekly, df_leaderboard


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


def plot_current_week(df_cumsum):
    data = [{
        'x': df_cumsum.index,
        'y': df_cumsum[col],
        'name': col
    } for col in df_cumsum.columns]
    layout = go.Layout(title='Cumulative Sum per Person',
                       xaxis=dict(title='Date'), yaxis=dict(title='Pushup Count'))
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/current_week.html')


def plot_cumulative_all(df):
    df_cumsum = df.cumsum()
    data = [{
        'x': df_cumsum.index,
        'y': df_cumsum[col],
        'name': col
    } for col in df_cumsum.columns]
    layout = go.Layout(title='Total Cumulative Sum',
                       xaxis=dict(title='Date'), yaxis=dict(title='Pushup Count'),
                       showlegend=False,
                       height=350)
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/total_pushups.html')


def plot_distribution(df):
    data = [go.Histogram(x=df['Pushups'], nbinsx=10, opacity=0.75)]
    layout = go.Layout(title='Distribution of Pushups per Set',
                       xaxis=dict(showgrid=True), bargap=0.25)
    fig = go.Figure(data=data, layout=layout)
    plot_offline(fig, './docs/plots/current_distribution.html')


if __name__ == "__main__":
    analyse_chatlog(sys.argv[1])
