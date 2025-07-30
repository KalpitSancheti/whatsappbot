from datetime import datetime

class TellTimeTool:
    name = "time"
    def invoke(self, _):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

tell_time = TellTimeTool()
