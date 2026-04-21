import time
from fifo import Fifo


class Processing:
    def __init__(self):
        self.cur_min = 65535
        self.cur_max = 0
        self.threshold = None
        self.prev_val = 65535
        self.last_beat_time = 0
        self.beat_intervals = Fifo(6, typecode='i')
        self.intervals_sum = 0
        self.intervals_count = 0
        self.bpm = 0
        self.sample_count = 0
        self.sma_buffer = []
        self.SMA_WINDOW = 5

    def process_sample(self, raw_value):
        # sliding window
        self.sma_buffer.append(raw_value)
        if len(self.sma_buffer) > self.SMA_WINDOW:
            self.sma_buffer.pop(0)
        value = sum(self.sma_buffer) / len(self.sma_buffer)
        is_beat = False
        self.sample_count += 1

        # find max min
        if value < self.cur_min:
            self.cur_min = value
        if value > self.cur_max:
            self.cur_max = value

        # recalibrate every 2 sec
        if self.sample_count >= 500:
            self.threshold = (self.cur_max + self.cur_min) / 2
            self.sample_count = 0
            self.cur_min = 65535
            self.cur_max = 0

        # verify crossing the threshold
        if self.threshold is not None and self.prev_val < self.threshold and value >= self.threshold:
            now = time.ticks_ms()

            # Detect the first beat 
            if self.last_beat_time == 0:
                self.last_beat_time = now
                self.prev_val = value
                return is_beat
            interval = time.ticks_diff(now, self.last_beat_time)

            # detect invalid intervals (too short or too long)
            if interval < 300:
                self.prev_val = value
                return False

            if interval > 2000:
                self.last_beat_time = now
                self.prev_val = value
                return False

            is_beat = True
            
            # Keep moving average of intervals inside the FIFO
            if self.intervals_count == 6:
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
                    self.bpm = calculated_bpm
                    print(f'Heart rate: {self.bpm} bpm')

            self.last_beat_time = now

        self.prev_val = value
        return is_beat