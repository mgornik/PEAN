from collections import namedtuple

SingleRunResult = namedtuple('SingleRunResult', 'name result duration blocker')

TestResults = namedtuple('TestResults', 'name runs passes failures test_fails crashes time_outs total_duration max_duration success score factor executions')