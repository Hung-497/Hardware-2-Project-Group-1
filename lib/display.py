from hardware import hw
from fifo import Fifo
import micropython
micropython.alloc_emergency_exception_buf(200)


class Display:
    def __init__(self, processor):
        self.processor = processor
        self.reset()

    def reset(self):
        self.prev_block = Fifo(250,typecode='h')
        
        # collect 5 samples at a time n cal its mean into 1 graph point
        self.current_group = []
        self.group_total = 0
        
        # list of y positions to draw on screen, max 128
        self.new_values = []
        
        # a copy of processor min n max; n only update ưhen have vaid value
        self.min_val = None
        self.max_val = None

    def update_min_max(self):
        
        cur_min = self.processor.cur_min
        cur_max = self.processor.cur_max
        
        # reset values from processing
        if cur_min != 65535 and cur_max != 0 and cur_max > cur_min:
            self.min_val = cur_min
            self.max_val = cur_max

    def add_sample(self, sample):
        sample = int(sample)
        
        # if buffer is damn like too long, keep only last 250 samples
        self.prev_block.put(sample)
        if not self.prev_block.empty():
            self.prev_block.get()

        # try to update copy of min/max from processor
        self.update_min_max()
        
        # collect samples into a group of 5
        self.current_group.append(sample)
        self.group_total += sample
        
        # once have 5 samples, cal 1 graph point
        if len(self.current_group) == 5:
            
            # means 5 samples
            avg_val = self.group_total / 5

             # scale avg_val to 0-63 pixels using min n max
            if self.min_val is None or self.max_val == self.min_val:
                scaled = 31
            else:
                scaled = int((avg_val - self.min_val) * 63 / (self.max_val - self.min_val))
                if scaled < 0:
                    scaled = 0
                if scaled > 63:
                    scaled = 63

            y = 63 - scaled
            self.new_values.append(y)
            
            # keep only 128 points, one per pixel column on OLED
            while len(self.new_values) > 128:
                self.new_values.pop(0)
                
            # reset for next 5 samples
            self.current_group = []
            self.group_total = 0

    def draw_graph(self, col, row, width, height):
        
        # need 2 points to draw a line
        if len(self.new_values) < 2:
            return
        
        # take the last 'width' points to fill the screen
        points = self.new_values[-width:]
        
        prev_y = None
        for x in range(len(points)):
            y = row + int(points[x] * (height - 1) / 63)
            if prev_y is None:
                hw.oled.pixel(col + x, y, 1)
            else:
                hw.oled.line(col + x - 1, prev_y, col + x, y, 1)
            prev_y = y
