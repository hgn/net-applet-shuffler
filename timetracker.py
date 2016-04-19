"""timetracker.py

<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
Email: Daniel Metz <dmetz@mytum.de>
=======
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
Module for keeping track of the estimated time a campaign requires to be run.

Use at the beginning of a campaign:
tt = timetracker.TimeTracker("[campaign_name]")
print(tt.get_campaign_runtime()[0])

Use while campaign:
print(tt.get_elapsed_runtime()[0])
print(tt.get_remaining_runtime()[0])

And at the end of a campaign:
print(tt.update_campaign_runtime()[0])

Alternatively, the public methods from above hold the pure time at position
[1].
"""

import hashlib
import json
import os
import time


class TimeTracker:

    CAMPAIGN_FOUND = True
    CAMPAIGN_NAME = str()
    CAMPAIGN_SHA1 = str()
    CAMPAIGN_START_TIME = int()
    ESTIMATE_AVAILABLE = False
    FILE_NAME = "times.json"

    """Create TimeTracker instance

    Needs the campaign name.
    Will do nothing if the campaign name is wrong.
    """
    def __init__(self, campaign_name):
        # set campaign name
        self.CAMPAIGN_NAME = campaign_name
        self.file_dir = os.path.dirname(__file__)
        # set trackfile.json path
<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
        self.trackfile_path = os.path.join(self.file_dir, self.FILE_NAME)
=======
        self.file_path = os.path.join(self.file_dir, self.FILE_NAME)
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
        # create trackfile if there is none
        self._handle_track_file()
        # create sha1 from campaign
        self._set_campaign_sha1()
        # set campaign start time for updated estimates
        self.CAMPAIGN_START_TIME = int(round(time.time()))

    def _set_campaign_sha1(self):
        campaign_path = os.path.join(self.file_dir, "campaigns",
                                     self.CAMPAIGN_NAME, "run.py")
        try:
            campaign_file = open(campaign_path)
            campaign_str = campaign_file.read()
            campaign_file.close()
            campaign_str_b = bytes(campaign_str, encoding="UTF-8")
            self.CAMPAIGN_SHA1 = str(hashlib.sha1(campaign_str_b).hexdigest())
        except IOError:
            self.CAMPAIGN_FOUND = False

    def _handle_track_file(self):
<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
        if not os.path.exists(self.trackfile_path):
=======
        if not os.path.exists(self.file_path):
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
            file = open(self.FILE_NAME, "w")
            file.write("{\n}")
            file.close()
            return

    def _info_available(self, parsed_json):
        for sha1 in parsed_json:
            if sha1 == self.CAMPAIGN_SHA1:
                return True
        return False

    def _load_track_file_as_json(self):
<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
        file = open(self.trackfile_path, "r")
=======
        file = open(self.file_path, "r")
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
        trackfile_str = file.read()
        file.close()
        return json.loads(trackfile_str)

    def _save_track_file_as_json(self, trackfile_string):
<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
        file = open(self.trackfile_path, "w")
=======
        file = open(self.file_path, "w")
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
        file.write(json.dumps(trackfile_string, indent=4))
        file.close()

    def _set_campaign_runtime(self, time_seconds):
        trackfile_json = self._load_track_file_as_json()
        trackfile_json.update({self.CAMPAIGN_SHA1:
                                   [{"length": str(time_seconds),
                                     "campaign_name": self.CAMPAIGN_NAME}]})
        self._save_track_file_as_json(trackfile_json)

<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
    def _hms_to_int(self, hms_string):
=======
    def _convert_hms_to_int(self, hms_string):
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
        hms_list = hms_string.split(":")
        return int(hms_list[0]) * 3600 + int(hms_list[1]) * 60 + int(hms_list[2])

    def _sec_to_hms(self, int_sec):
        return time.strftime("%H:%M:%S", time.gmtime(int(int_sec)))

    """Return campaign runtime sentence string, return campaign runtime string

    Public method used to get the campaign runtime.
    """
    def get_campaign_runtime(self):
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n"
        trackfile_json = self._load_track_file_as_json()
        if self._info_available(trackfile_json):
            time_formatted = trackfile_json[self.CAMPAIGN_SHA1][0]["length"]
            self.ESTIMATE_AVAILABLE = True
            return "Estimated campaign runtime: {}".format(time_formatted), \
                   time_formatted
        else:
            return "Estimated campaign runtime: not available", "not available"

    """Return remaining campaign runtime sentence string,
    return remaining campaign runtime string

    Public method used to get the remaining campaign runtime.
    """
    def get_remaining_runtime(self):
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n", \
                   "\nerror: wrong campaign path/name\n"
        if not self.ESTIMATE_AVAILABLE:
            return "Estimated remaining campaign runtime: unavailable", "-1"
        _, expected_runtime = self.get_campaign_runtime()
<<<<<<< c8acab6738f96ed53e7ec6a63615a2f6f167f292
        expected_runtime_seconds = self._hms_to_int(expected_runtime)
        _, elapsed_time = self.get_elapsed_runtime()
        elapsed_time_seconds = self._hms_to_int(elapsed_time)
=======
        expected_runtime_seconds = self._convert_hms_to_int(expected_runtime)
        _, elapsed_time = self.get_elapsed_runtime()
        elapsed_time_seconds = self._convert_hms_to_int(elapsed_time)
>>>>>>> adding timetracker module to allow for campaign time display and more fancy stuff
        remaining_runtime = expected_runtime_seconds - elapsed_time_seconds
        if remaining_runtime < 0:
            return "Estimated remaining campaign runtime: unavailable", "-1"
        remaining_runtime_formatted = self._sec_to_hms(remaining_runtime)
        return "Estimated remaining campaign runtime: {}"\
               .format(remaining_runtime_formatted), \
               remaining_runtime_formatted

    """Return elapsed campaign runtime sentence string,
    return elapsed campaign runtime string

    Public method used to get the elapsed campaign runtime.
    """
    def get_elapsed_runtime(self):
        time_now = int(round(time.time()))
        time_elapsed = time_now - self.CAMPAIGN_START_TIME
        elapsed_runtime_formatted = self._sec_to_hms(time_elapsed)
        return "Elapsed campaign runtime: {}"\
               .format(elapsed_runtime_formatted), \
               elapsed_runtime_formatted

    """Return the campaign runtime sentence string,
    return the campaign runtime string

    Update the campaign runtime estimate
    Public method used to save and store the campaign runtime.
    """
    def update_campaign_runtime(self):
        if not self.CAMPAIGN_FOUND:
            return "\nerror: wrong campaign path/name\n", \
                   "\nerror: wrong campaign path/name\n"
        time_now = int(round(time.time()))
        time_elapsed = time_now - self.CAMPAIGN_START_TIME
        time_converted = self._sec_to_hms(time_elapsed)
        self._set_campaign_runtime(time_converted)
        return "Campaign runtime: {}".format(time_converted), time_converted
