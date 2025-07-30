from .echo import echo_tool
from .time import tell_time
from .calendar import calendar_tool
from .calendar_query import calendar_query_tool
from .calendar_delete import calendar_delete_tool

all_tools = [echo_tool, tell_time, calendar_tool, calendar_query_tool, calendar_delete_tool]
