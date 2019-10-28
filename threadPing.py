''' Partial credit to https://gist.github.com/ariesmcrae/64c69a020335892b00d4
	Edited by Jeremy Reynolds for UALR COSMOS Team
	This is a threaded version of ping.py (Line 19 contains worker count)
	Supports Windows Only
'''

from queue import Queue
from datetime import datetime
from threading import Thread
import pandas as pd, subprocess, time, csv, os

def readFile(filename):				# Opens sitelist file, appends all items to jobs[], calls ping()
	file = open(filename)
	reader = csv.reader(file)
	for item in reader:
		jobs.append(item[0].strip())
	file.close()

	for i in range(30):				# Start threads, each one will process one job from the jobs[] queue
		t = Thread(target=ping, args=(queue,))
		t.setDaemon(True)
		t.start()
	for job in jobs:				# For each item in jobs[], put each into the queue in FIFO sequence
		queue.put(job)
	queue.join()					# Wait until all jobs are processed before quitting

def ping(queue):					# Calls ping as subprocess with count=2 and timeout=2 seconds
	while True:
		hostname = queue.get()		# Retrieves item from queue
		p = subprocess.Popen('ping -n 2 -w 2000 ' + hostname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		pingStatus = 'active'		# Sets pingStatus to 'active' if the following logic is false
		for line in p.stdout:
			output = line.rstrip().decode('UTF-8')
			if(output.endswith('unreachable.')):
				pingStatus = 'unreachable'			# No route from the local system (network cable unplugged)
				break
			elif(output.startswith('Ping request could not find host')):
				pingStatus = 'host_not_found'		# Requested host name cannot be resolved to its ip address
				break
			if(output.startswith('Request timed out.')):
				pingStatus = 'timed_out'			# No echo reply messages were received within time limit
				break
		global counter, logFile
		time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		statusSum.append(pingStatus)				# Appends 'pingStatus' to statusSum[] to calculate totals
		counter += 1								# Advances counter and prints info to screen
		print(time, hostname.ljust(36), str(counter).ljust(7), pingStatus)
		outList.append([time, hostname, pingStatus])
		queue.task_done()							# Appends row to outList[] and stops current queue worker

counter = 0
while(True):
	filename = 'sitelist.csv'							# CSV file that contains hostname list
	sleepLength = 86400									# Sleep length in seconds 86400 = 1 Day
	logFile = 'log.csv'									# CSV output file
	queue = Queue()										# Initializes Queue
	statusSum = []										# List of current pingStatus to calculat 'Current Totals'
	outList = []										# List of final items to be sorted and saved to output file
	jobs = []											# List of hostnames to use for threading

	start_time = time.time()							# Starts a timer for entire script

	if not os.path.exists(logFile):						# Creates log file if it does not exist
		with open(logFile, 'a', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['time','host','status'])	# Writes column headers
	readFile(filename)									# Starts ping checker by calling readFile()

	df = pd.DataFrame(outList)							# Creates dataframe from outList[] items
	df.columns = ['time', 'host', 'status']				# Renames column headers

	#df2 = pd.read_csv(filename, header=None)			# Uncomment to sort based on input url list instead of by time
	#df = df.set_index('host')
	#df = df.reindex(index=df2[0])
	#df = df.reset_index()
	#df.rename(columns = {0: 'host'}, inplace=True)
	#df = df[['time','host','status']]

	df.to_csv(logFile, index=False, header=None, mode='a', encoding='utf-8')

	activeSum1 = sum(1 for item in statusSum if item == 'active')
	timed_outSum1 = sum(1 for item in statusSum if item == 'timed_out')
	unreachableSum1 = sum(1 for item in statusSum if item == 'unreachable')
	host_not_foundSum1 = sum(1 for item in statusSum if item == 'host_not_found')

	activeSum2 = sum(1 for row in csv.reader(open(logFile)) if row[2] == 'active')
	timed_outSum2 = sum(1 for row in csv.reader(open(logFile)) if row[2] == 'timed_out')
	unreachableSum2 = sum(1 for row in csv.reader(open(logFile)) if row[2] == 'unreachable')
	host_not_foundSum2 = sum(1 for row in csv.reader(open(logFile)) if row[2] == 'host_not_found')

	print('\nFinished ping test of', sum(1 for line in open(filename)), 'urls in', time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
	print('\nActive:\t\t', activeSum1, '\t*Current Totals*', '\nTimed Out:\t', timed_outSum1, '\nUnreachable\t', unreachableSum1, '\nHost Not Found:\t', host_not_foundSum1)
	print('\nActive:\t\t', activeSum2, '\t*Cumulative Totals*', '\nTimed Out:\t', timed_outSum2, '\nUnreachable\t', unreachableSum2, '\nHost Not Found:\t', host_not_foundSum2,'\n')

	for i in reversed(range(0, sleepLength)):			# Updating sleep function in seconds
		print(' Sleeping for', i, 'seconds...', end='\r')
		time.sleep(1)
