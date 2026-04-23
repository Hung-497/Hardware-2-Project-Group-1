import time
from fifo import Fifo


class Processing:
    def __init__(self):
        self.cur_min = 65535
        self.cur_max = 0
        self.prev_val = 65535

        self.threshold_up = None
        self.last_beat_time = None

        self.beat_intervals = Fifo(7, typecode='i')
        self.intervals_sum = 0
        self.intervals_count = 0

        self.bpm = 0
        self.sample_count = 0

        self.sma_buffer = []
        self.SMA_WINDOW = 5

        self.bpm_list = []
        self.collecting_30s = False
        self.collection_start = 0
        self.collection_complete = False

        self.MIN_INTERVAL = 450
        self.MAX_INTERVAL = 1500

        self.mean_hr = 0
        self.rmssd_val = 0
        self.sdnn_val = 0

    def start_collection(self):
        self.bpm_list = []
        self.collecting_30s = True
        self.collection_complete = False
        self.collection_start = time.ticks_ms()

        self.mean_hr = 0
        self.rmssd_val = 0
        self.sdnn_val = 0

        # reset beat detection state when starting new collection
        self.last_beat_time = None
        self.beat_intervals = Fifo(7, typecode='i')
        self.intervals_sum = 0
        self.intervals_count = 0
        self.bpm = 0

        self.sample_count = 0
        self.cur_min = 65535
        self.cur_max = 0
        self.threshold_up = None
        self.prev_val = 65535

    def sma_update(self, buffer, sample):
        buffer.append(sample)
        if len(buffer) > self.SMA_WINDOW:
            buffer.pop(0)
        return sum(buffer) / len(buffer)

    def process_sample(self, raw_value):
        filtered_val = self.sma_update(self.sma_buffer, raw_value)
        is_beat = False
        self.sample_count += 1

        if filtered_val < self.cur_min:
            self.cur_min = filtered_val
        if filtered_val > self.cur_max:
            self.cur_max = filtered_val

        # update threshold every 2 seconds at 250 Hz
        if self.sample_count >= 500:
            signal_range = self.cur_max - self.cur_min
            if 100 < signal_range < 6000:
                new_threshold = self.cur_min + 0.6 * signal_range

                if self.threshold_up is None:
                    self.threshold_up = new_threshold
                else:
                    self.threshold_up = 0.7 * self.threshold_up + 0.3 * new_threshold

            print(signal_range, self.cur_min, self.cur_max, self.threshold_up, self.bpm)

            self.sample_count = 0
            self.cur_min = 65535
            self.cur_max = 0

        if (self.threshold_up is not None and self.prev_val < self.threshold_up and filtered_val >= self.threshold_up):
            now = time.ticks_ms()

            if self.last_beat_time is None:
                self.last_beat_time = now
                self.prev_val = filtered_val
                return False

            interval = time.ticks_diff(now, self.last_beat_time)

            if interval < self.MIN_INTERVAL:
                self.prev_val = filtered_val
                return False

            if interval > self.MAX_INTERVAL:
                self.last_beat_time = now
                self.prev_val = filtered_val
                return False

            is_beat = True

            if self.intervals_count >= 6:
                old_interval = self.beat_intervals.get()
                self.intervals_sum -= old_interval
            else:
                self.intervals_count += 1

            self.beat_intervals.put(interval)
            self.intervals_sum += interval

            mean_ppi = self.intervals_sum / self.intervals_count
            if mean_ppi > 0:
                calculated_bpm = int(60000 / mean_ppi)
                if 40 <= calculated_bpm <= 220:
                    self.bpm = calculated_bpm

            if self.collecting_30s:
                self.bpm_list.append(interval)
                if time.ticks_diff(now, self.collection_start) >= 30000:
                    self.collecting_30s = False
                    self.collection_complete = True

                    # calculate mean HR + mean PPI for kubios
                    if len(self.bpm_list) > 0:
                        mean_interval = sum(self.bpm_list) / len(self.bpm_list)
                        self.mean_hr = int(60000 / mean_interval)
                    else:
                        self.mean_hr = 0

                    # calculate RMSSD for kubios
                    if len(self.bpm_list) >= 2:
                        squared_diff_sum = 0

                        for i in range(len(self.bpm_list)-1):
                            diff = self.bpm_list[i+1] - self.bpm_list[i]
                            squared_diff_sum += diff * diff
                        
                        mean_squared_diff = squared_diff_sum / (len(self.bpm_list) - 1) 
                        self.rmssd_val = mean_squared_diff ** 0.5
                    else:
                        self.rmssd_val = 0

                    # calculate SDNN for kubios
                    if len(self.bpm_list) >= 2:
                        mean_interval = sum(self.bpm_list) / len(self.bpm_list)
                        squared_diff_sum = 0

                        for i in range(len(self.bpm_list)):
                            diff = self.bpm_list[i] - mean_interval
                            squared_diff_sum += diff * diff
                        mean_squared_diff = squared_diff_sum / (len(self.bpm_list))
                        self.sdnn_val = mean_squared_diff ** 0.5
                    else:
                        self.sdnn_val = 0

            self.last_beat_time = now

        self.prev_val = filtered_val
        return is_beat