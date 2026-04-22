import time
from fifo import Fifo


class Processing:
    def __init__(self):
        self.cur_min = 65535
        self.cur_max = 0
        self.threshold_up = None
        self.prev_val = 65535
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

    def start_collection(self):
        self.bpm_list = []
        self.collecting_30s = True
        self.collection_complete = False
        self.collection_start = time.ticks_ms()

    def sma_update(self, buffer, sample):
        buffer.append(sample)

        if len(buffer) > self.SMA_WINDOW:
            buffer.pop(0)

        return sum(buffer) / len(buffer)
    
    def process_sample(self, raw_value):
        filtered_val = self.sma_update(self.sma_buffer, raw_value)
        is_beat = False
        self.sample_count += 1

        # find max min
        if filtered_val < self.cur_min:
            self.cur_min = filtered_val
        if filtered_val > self.cur_max:
            self.cur_max = filtered_val

        # recalibrate every 2 sec
        if self.sample_count >= 500:
            signal_range = self.cur_max - self.cur_min
            print(signal_range, self.cur_min, self.cur_max)
            if 100 <= signal_range <= 1000:
                new_threshold = self.cur_min + 0.7 * signal_range

                if self.threshold_up is None:
                    self.threshold_up = new_threshold
                else:
                    self.threshold_up = 0.8 * self.threshold_up + 0.2 * new_threshold

            self.sample_count = 0
            self.cur_min = 65535
            self.cur_max = 0

        now = time.ticks_ms()

        # verify crossing the threshold
        if self.threshold_up is not None and self.prev_val < self.threshold_up and filtered_val >= self.threshold_up:
            # Detect the first beat 
            if self.last_beat_time is None:
                self.last_beat_time = now
                self.prev_val = filtered_val
                return False
            
            interval = time.ticks_diff(now, self.last_beat_time)

            # detect invalid intervals (too short or too long)
            if interval < 300:
                self.prev_val = filtered_val
                return False

            if interval > 1500:
                self.last_beat_time = now
                self.prev_val = filtered_val
                return False

            is_beat = True
            
            # Keep moving average of intervals inside the FIFO
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
                # check possibility
                if 40 <= calculated_bpm <= 220:
                    if self.bpm == 0:
                        self.bpm = calculated_bpm
                    else:
                        self.bpm = int(0.8 * self.bpm + 0.2 * calculated_bpm)

            if self.collecting_30s:
                self.bpm_list.append(interval)
                # check 30 second
                if time.ticks_diff(now, self.collection_start) >= 30000:
                    self.collecting_30s = False
                    self.collection_complete = True

            self.last_beat_time = now

        self.prev_val = filtered_val
        return is_beat