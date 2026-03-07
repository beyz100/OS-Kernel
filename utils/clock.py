class Clock:
    def __init__(self):
 
        self.current_tick = 0

    def tick(self):
      
        self.current_tick += 1
        return self.current_tick