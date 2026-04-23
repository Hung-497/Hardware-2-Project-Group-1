from hardware import hw


class Display:
    def __init__(self):
        # Call reincarnation when object is created
        self.reincarnation()

    def clear_data(self):
        # Previous block of 250 samples
        # This block is used to get min and max for scaling
        self.block_prev = []

        # Current block of 250 samples
        # When this block is full, it becomes the new previous block
        self.block_curr = []

        # Used to average 5 samples into 1 graph point
        self.sum_5 = 0
        self.count_5 = 0

        # This list stores graph points to draw on OLED
        self.graph = []

    def scale_to_y(self, sample, top, height):
        # If there is no previous block yet,
        # just put the point in the middle of the graph area
        if len(self.block_prev) == 0:
            return top + height // 2

        # Get min and max from previous 250 samples
        min_val = min(self.block_prev)
        max_val = max(self.block_prev)

        # Avoid division by zero
        if max_val == min_val:
            return top + height // 2

        # Scale sample into graph height range
        y = int((sample - min_val) * (height - 1) / (max_val - min_val))

        # Limit y so it stays inside the graph area
        if y < 0:
            y = 0
        if y > height - 1:
            y = height - 1

        # OLED y-axis goes downward, so flip it
        y = top + (height - 1 - y)
        return y

    def add_sample(self, sample):
        # First, collect the first 250 samples
        # These samples are used as the first scaling block
        if len(self.block_prev) < 250:
            self.block_prev.append(sample)
            return

        # Add sample into current 250-sample block
        self.block_curr.append(sample)

        # Add sample into 5-sample averaging group
        self.sum_5 = self.sum_5 + sample
        self.count_5 = self.count_5 + 1

        # When we have 5 samples, calculate average
        if self.count_5 == 5:
            avg = self.sum_5 // 5

            # Save averaged point into graph list
            self.graph.append(avg)

            # Keep only the latest 128 points for OLED width
            if len(self.graph) > 128:
                self.graph.pop(0)

            # Reset 5-sample group
            self.sum_5 = 0
            self.count_5 = 0

        # When current block reaches 250 samples,
        # replace previous block with current block
        if len(self.block_curr) == 250:
            self.block_prev = self.block_curr
            self.block_curr = []

    def draw_graph(self, top, height):
        # If not enough graph points yet, show waiting text
        if len(self.graph) < 2:
            hw.oled.text("WAIT...", 40, top + 12)
            return

        # Draw line between consecutive graph points
        x = 1
        while x < len(self.graph):
            y1 = self.scale_to_y(self.graph[x - 1], top, height)
            y2 = self.scale_to_y(self.graph[x], top, height)

            hw.oled.line(x - 1, y1, x, y2, 1)
            x = x + 1