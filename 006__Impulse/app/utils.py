def dataframe_processing(_df_raw_,
                         _sheet_index_,
                         _columns_):
    import pandas as pd
    from constants import mapping

    sheets = list(_df_raw_.keys())

    cdf = pd.DataFrame(_df_raw_[sheets[_sheet_index_]][_columns_])

    cdf = cdf.rename(columns=mapping)

    import hashlib
    import numpy as np

    cdf['hash'] = np.nan

    for index_, row_ in cdf.iterrows():
        if not pd.isnull(row_['name']):
            row_string = ''.join(str(value_) for value_ in row_.values)
            cdf.at[index_, 'hash'] = hashlib.sha256(row_string.encode('utf-8')).hexdigest()[:32]

    cdf.loc[cdf['name'].notnull(), cdf.columns != 'name'] = \
        cdf.loc[cdf['name'].notnull(), cdf.columns != 'name'].fillna("__EMPTY__")

    cdf = cdf.ffill(axis=0)

    cdf['click_to'] = cdf['click_to'].str.split(', ')
    cdf = cdf.explode('click_to')

    cdf = cdf[cdf['webinar_to'] != "__EMPTY__"].dropna()

    cdf[['Button_Name', 'Button_Time']] = cdf['click_to'].str.split(' в ', expand=True)

    cdf = cdf.replace({'__EMPTY__': '', None: ''})

    cdf['date'] = pd.to_datetime(cdf['date'])

    try:
        cdf['webinar_from'] = pd.to_datetime(cdf['webinar_from'], format='%H:%M').dt.time
        cdf['webinar_to'] = pd.to_datetime(cdf['webinar_to'], format='%H:%M').dt.time
    except ValueError:
        cdf['webinar_from'] = pd.to_datetime(cdf['webinar_from'], format='%H:%M:%S').dt.time
        cdf['webinar_to'] = pd.to_datetime(cdf['webinar_to'], format='%H:%M:%S').dt.time

    cdf['interval_from'] = pd.to_datetime(cdf['interval_from'], format='%H:%M:%S').dt.time
    cdf['interval_to'] = pd.to_datetime(cdf['interval_to'], format='%H:%M:%S').dt.time

    from datetime import datetime

    cdf['Button_Time'] = cdf['Button_Time'].apply(
        lambda x: datetime.strptime(str(x), '%H:%M').time() if x != '' else '')

    return cdf


def time_plus(_time_, _timedelta_):
    from datetime import datetime

    start = datetime(2000, 1, 1,
                     hour=_time_.hour,
                     minute=_time_.minute,
                     second=_time_.second)
    end = start + _timedelta_
    return end.time()


def webinar_time_range(_df_):
    from datetime import timedelta
    import pandas as pd

    min_webinar = time_plus(_df_.webinar_from.min(), timedelta(minutes=-1))
    max_webinar = time_plus(_df_.webinar_to.max(), timedelta(minutes=3))
    webinar_range_ = pd.date_range(str(min_webinar), str(max_webinar), freq="1min").time
    return webinar_range_


def result_grabbing(_current_df_):
    from constants import result_columns, names, timeshift
    import pandas as pd

    webinar_range = webinar_time_range(_current_df_)
    result_ = pd.DataFrame(columns=result_columns, index=webinar_range).reset_index()
    result_ = result_.rename(columns={'index': 'time'})

    for index_, row_ in result_.iterrows():
        try:
            result_.at[index_, 'INCOME'] = _current_df_.loc[(_current_df_['interval_from'] >= webinar_range[index_]) &
                                                            (_current_df_['interval_from'] <= webinar_range[
                                                                index_ + 1]) &
                                                            (_current_df_['duration'] >= timeshift)].reset_index()[
                'hash'].nunique()

            result_.at[index_, 'OUTCOME'] = _current_df_.loc[(_current_df_['interval_to'] >= webinar_range[index_]) &
                                                             (_current_df_['interval_to'] <= webinar_range[
                                                                 index_ + 1]) &
                                                             (_current_df_['duration'] >= timeshift)].reset_index()[
                'hash'].nunique()
        except IndexError:
            result_.at[index_, 'INCOME'] = 0
            result_.at[index_, 'OUTCOME'] = 0

        for key_, value_ in names.items():
            try:
                result_.at[index_, key_] = _current_df_.loc[(_current_df_['Button_Time'] == webinar_range[index_]) &
                                                            (_current_df_['interval_from'] <= webinar_range[index_]) &
                                                            (webinar_range[index_] <= _current_df_['interval_to']) &
                                                            # (_current_df_['duration'] >= timeshift) &
                                                            (_current_df_['Button_Name'] == value_)].reset_index()[
                    'hash'].nunique()
            except IndexError:
                result_.at[index_, key_] = 0

    return result_


def plotting(_result_, _title_=None):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.set_title(_title_)
    _result_.plot(ax=ax)
    plt.savefig(str('data/' + _title_ + '__figure.png'))
    plt.show()
