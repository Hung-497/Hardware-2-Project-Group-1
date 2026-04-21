import time
from fifo import Fifo


class Processing:
    def __init__(self):
        self.cur_min = 65535
        self.cur_max = 0
        self.threshold = None
        self.prev_val = 65535
        self.last_beat_time = None
        self.beat_intervals = Fifo(6, typecode='i')
        self.intervals_sum = 0
        self.intervals_count = 0
        self.bpm = 0
        self.sample_count = 0
        self.sma_buffer = []
        self.SMA_WINDOW = 5

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
            self.threshold = (self.cur_max + self.cur_min) / 2
            self.sample_count = 0
            self.cur_min = 65535
            self.cur_max = 0

        # verify crossing the threshold
        if self.threshold is not None and self.prev_val < self.threshold and filtered_val >= self.threshold:
            now = time.ticks_ms()

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

            if interval > 2000:
                self.last_beat_time = now
                self.prev_val = filtered_val
                return False

            is_beat = True
            
            # Keep moving average of intervals inside the FIFO
            if self.intervals_count == 5:
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

        self.prev_val = filtered_val
        return is_beat