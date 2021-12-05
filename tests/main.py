import sys
import os
import json
import time

_this_dir = os.path.dirname(__file__)
_impl_dir = os.path.abspath(os.path.join(_this_dir,"..","impl"))
if not _impl_dir in sys.path:
	sys.path.append(_impl_dir)

import process_queue
import process_handler

def create_env():
	return {
		"PATH" : str(os.environ['PATH'])
	}

def print_dict(d):
	print(json.dumps(d, sort_keys=True, indent=4))

class CustomHandler(process_handler.StdoutHandler):
	def __init__(self, print_result):
		process_handler.StdoutHandler.__init__(self)
		self.print_result = print_result

	def close(self, process_data):
		if self.print_result:
			print_dict(process_data)

class CustomQueue(process_queue.ProcessQueue):
	def __init__(self, workdir, env):
		process_queue.ProcessQueue.__init__(self, workdir, env)

	def create_process_handler(self, _id, _itm, _env):
		return CustomHandler(_itm.get("_print", True))

#########################################################################################

def test_start_stop():
	q = process_queue.ProcessQueue(_this_dir, {})
	q.start()
	print_dict(q.create_env(-1,{}))
	q.stop()

def test_missing_command():
	q = process_queue.ProcessQueue(_this_dir, {})
	
	_itm = {
		"_print" : False,
		"env" : {
			"TEST_ENV_STR" : "asdf",
		}
	}

	q.push_back(1, _itm)

	q.start()

	data = q.wait_for_task_finished(1)

	q.stop()

	print_dict(data)

def test_invalid_command():
	q = CustomQueue(_this_dir, {})
	
	_itm = {
		"cmd" : ["ljkbihyerbjkhj"]
	}

	q.push_back(0, _itm)

	q.start()

	q.wait_for_empty()

	q.stop()

def test_valid_command():
	q = CustomQueue(_this_dir, os.environ.copy())
	q.start()	
	_itm = {
		"_print" : False,
		"cmd" : ["{_SHELL_OPT_}","{_PROCESS_ROOT_DIR_}/scripts_{_SHELL_EXT_}/hello_world.{_SHELL_EXT_}"]
	}

	q.push_back(0, _itm)

	q.wait_for_empty()
	q.stop()

def test_command_with_error():
	q = CustomQueue(_this_dir, {})
	q.start()	
	_itm = {
		"cmd" : ["{_SHELL_OPT_}", "{_PROCESS_ROOT_DIR_}/scripts_{_SHELL_EXT_}/exit_code.{_SHELL_EXT_}"]
	}

	q.push_back(0, _itm)

	q.wait_for_empty()
	q.stop()

def test_wait_pid():
	q = CustomQueue(_this_dir, os.environ.copy())
	q.start()	
	_itm = {
		"_print" : False,
		"env" : {
			"SLEEP_SECONDS" : "2"
		},
		"cmd" : ["{_SHELL_OPT_}", "{_PROCESS_ROOT_DIR_}/scripts_{_SHELL_EXT_}/wait.{_SHELL_EXT_}"]
	}

	q.push_back(0, _itm)
	assert(q.remove_or_kill(1) == None)
	q.push_back(1, _itm)
	q.push_back(2, _itm) #kill be dropped
	print_dict(q.query_items())
	pid,_ = q.wait_for_process(1)
	print("[PID] " + str(pid))

	q.stop()

def test_kill():
	q = CustomQueue(_this_dir, os.environ.copy())
	q.start()	
	_itm = {
		"_print" : False,
		"env" : {
			"SLEEP_SECONDS" : "50"
		},
		"cmd" : ["{_SHELL_OPT_}", "{_PROCESS_ROOT_DIR_}/scripts_{_SHELL_EXT_}/wait.{_SHELL_EXT_}"]
	}

	q.push_back(0, _itm)
	time.sleep(1.0)
	print_dict(q.remove_or_kill(0))

	q.stop()

print("TEST START-STOP ----------------------------------------------------------------------------")
test_start_stop()
print("TEST MISSING COMMAND -----------------------------------------------------------------------")
test_missing_command()
print("TEST INVALID COMMAND -----------------------------------------------------------------------")
test_invalid_command()
print("TEST VALID COMMAND -------------------------------------------------------------------------")
test_valid_command()
print("TEST VALID COMMAND THAT FAILS --------------------------------------------------------------")
test_command_with_error()
print("TEST WAIT FOR PID --------------------------------------------------------------------------")
test_wait_pid()
print("TEST KILL ----------------------------------------------------------------------------------")
test_kill()