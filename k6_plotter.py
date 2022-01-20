from dateutil import parser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import datetime
import json
import sys


DEFAULT_METRIC = "http_req_waiting"


def round_seconds(date_time_object):
    new_date_time = date_time_object

    if new_date_time.microsecond >= 500000:
       new_date_time = new_date_time + datetime.timedelta(seconds=1)

    return new_date_time.replace(microsecond=0)


def round_minutes(date_time_object):
    new_date_time = date_time_object

    if new_date_time.second >= 30:
       new_date_time = new_date_time + datetime.timedelta(minutes=1)

    return new_date_time.replace(second=0)


def load_data(file_name):
    data = {}
    with open(file_name, "r") as f:
        for line in f.readlines():
            line_data = json.loads(line)
            if line_data["type"] == "Point":
                metric = line_data["metric"]
                metric_data = data.get(metric, [])
                metric_data.append((line_data["data"]["value"], parser.parse(line_data["data"]["time"])))
                data[metric] = metric_data
    return data

def get_metric_data(data, watched_metric):
    metric_data = data[watched_metric]

    return ([time for (value, time) in metric_data], [value for (value, time) in metric_data])


def get_avg_and_max_from_data(metric_data_raw):
    # prepare dicts for (sum, count) and max
    metric_data_sum_count = {}
    metric_data_max = {}

    for (time, value) in zip(metric_data_raw[0], metric_data_raw[1]):
        # round the time to seconds
        # time = round_minutes(round_seconds(time))
        time = round_seconds(time)

        # find the current entry
        entry = metric_data_sum_count.get(time, (0, 0))
        # and update its sum and count
        metric_data_sum_count[time] = (entry[0] + value, entry[1] + 1)
        
        # find the current maximum value
        max_wait = metric_data_max.get(time, 0)
        # and update it
        metric_data_max[time] = max(max_wait, value)

    # compute data avg
    metric_data_avg = [val / count for (_, (val, count)) in metric_data_sum_count.items()]

    return (metric_data_avg, metric_data_max)

def display_chart(metric_data_avg, metric_data_max, vus_data, watched_metric):
    # the chart will have two Y axes
    fig, ax1 = plt.subplots()

    # x axis displays time
    ax1.set_xlabel("Time")

    # first Y axis displays duration in milliseconds
    ax1.set_ylabel(watched_metric + " (ms)")

    # plot avg metric data values
    plot_1 = ax1.plot(metric_data_max.keys(), metric_data_avg, color="blue", label=f"avg {watched_metric}")

    # plot max metric data values
    plot_1 = ax1.plot(metric_data_max.keys(), metric_data_max.values(), color="red", linestyle="dashed", label=f"max {watched_metric}")

    # display legend of the first Y axis
    ax1.legend(loc=1)

    # make a second Y axis that will display the number of active VUs
    ax2 = ax1.twinx()
    ax2.set_ylabel("VUs")
    
    # plot the VU count data
    plot_2 = ax2.plot(vus_data[0], vus_data[1], color="green", label="VU count")
        
    # display legend of the second Y axis
    ax2.legend(loc=2)

    # do autoformat the X axis
    plt.gcf().autofmt_xdate()

    # show the chart
    plt.title("k6 load test results chart")
    
    # TODO save the plot to a file (file name from arguments)
    # plt.savefig("test.svg", format="svg")

    plt.show()


def display_hist(metric_data_values):
    n_bins = 20

    # We can set the number of bins with the *bins* keyword argument.
    # axs.hist(metric_data_values, bins=n_bins)
    plt.hist(metric_data_values)

    plt.show()


def process_file(file_name, watched_metric):
    # load data from the file
    print(f"Processing {file_name} for {watched_metric}...")
    data = load_data(file_name)
    print(f"File processed...")

    print("Parsing data...") 
    # get raw metric data
    metric_data_raw = get_metric_data(data, watched_metric)

    # get avg and max values from data
    (metric_data_avg, metric_data_max) = get_avg_and_max_from_data(metric_data_raw)

    # get VU count data
    vus_data = get_metric_data(data, "vus")
    
    print("Displaying chart...") 

    # display a chart
    display_chart(metric_data_avg, metric_data_max, vus_data, watched_metric)
    
    # display_hist(metric_data_raw[1])


if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_file(sys.argv[1], sys.argv[2])
    else:
        process_file(sys.argv[1], DEFAULT_METRIC)

