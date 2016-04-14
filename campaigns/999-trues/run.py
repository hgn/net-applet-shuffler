
import timetracker
import time


def main(x):

    tt = timetracker.TimeTracker("999-trues")
    print('Starting campaign 999-trues')
    print(tt.get_campaign_runtime()[0])

    time.sleep(1)
    x.exec('999-true')
    time.sleep(1)
    x.exec('999-true')

    time.sleep(3)
    x.exec('999-true')

    print(tt.get_elapsed_runtime()[0])
    print(tt.get_remaining_runtime()[0])

    time.sleep(7)
    x.exec('999-true')

    time.sleep(1)
    x.exec('999-true')

    print(tt.update_campaign_runtime()[0])
