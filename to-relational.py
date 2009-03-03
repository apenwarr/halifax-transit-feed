#!/usr/bin/python
import syck
from time import strptime, strftime

d = syck.load(open('hfxtable.yml').read())
options = d['options']
stops = d['stops']
routes = d['routes']

def join(between, l):
    return between.join([str(i) for i in l])

def headings(f,l):
    f.write(join(",", l) + "\r\n")

def rec(f, dict, direct, indirect, types = None):
    if types == None:
	types = [None]*len(direct+indirect)
    l = direct + [dict[k] for k in indirect]
    out = []
    for (val, typ) in zip(l, types):
	if typ == 'd':
	    out.append(strftime("%m/%d/%Y", strptime(str(val), "%Y%m%d")))
	elif typ == 't':
	    if val == '-':
		out.append('')
	    else:
		try:
		    t = strptime(val, '%H%Ma')
		    h = t[3]
		    m = t[4]
		except ValueError:
		    try:
			t = strptime(val, '%H%Mp')
			h = t[3]+12
			m = t[4]
		    except ValueError:
			# FIXME: what does the 'x' mean?
			t = strptime(val, '%H%Mx')
			h = t[3]
			m = t[4]
		out.append('%02d:%02d:00' % (h, m))
	else:
	    out.append(val)
    f.write(join(",", out) + "\r\n")

f = open('r-Global.csv', 'w')
headings(f, ['ID', 'StartDate', 'EndDate', 'RemoveDate',
	     'AgencyName', 'AgencyURL', 'AgencyTimezone'])
rec(f, options, [1],
    ['start_date', 'end_date', 'remove_date',
     'agency_name', 'agency_url', 'agency_timezone'],
    [None, 'd', 'd', 'd', None, None, None])
f.close()

f = open('r-Stop.csv', 'w')
headings(f, ['StopCode', 'Name', 'Latitude', 'Longitude'])
for s in stops:
    rec(f, s, [], ['stop_code', 'name', 'lat', 'lng'])
f.close()

rf = open('r-Route.csv', 'w')
headings(rf, ['RouteId','ShortName','LongName'])
ri = 0

rsf = open('r-Route_Stop.csv', 'w')
headings(rsf, ['RouteStopId', 'Route', 'Sort', 'StopCode'])
rsi = 0

tpf = open('r-TimePoint.csv', 'w')
headings(tpf, ['TimePointId', 'Route', 'Sort', 'StopCode'])
tpi = 0

runf = open('r-Run.csv', 'w')
headings(runf, ['RunId', 'Route', 'Weekdays', 'Saturday', 'Sunday'])
runi = 0

stf = open('r-Stop_Time.csv', 'w')
headings(stf, ['StopTimeId', 'Run', 'Stop', 'Time'])
sti = 0

def betweens_after(between_stops, tp):
    for bs in between_stops.keys():
	if bs.startswith('%s-' % tp):
	    return between_stops[bs]
    return []

for r in routes:
    print 'Route: %s: %s' % (r['short_name'], r['long_name'])
    
    ri += 1
    rec(rf, r, [ri], ['short_name', 'long_name'])

    i = 0
    time_points = r['time_points']
    between_stops = r['between_stops']
    for tp in time_points:
	tpi += 1
	
	def do_route_stop(s):
	    global rsi, ri, i, r
	    rsi += 1
	    i += 100
	    rec(rsf, r, [rsi, ri, i, s], [])
	    
	do_route_stop(tp)
	rec(tpf, tp, [tpi, ri, i, tp], [])
	for between in betweens_after(between_stops, tp):
	    do_route_stop(between)

    sat_exists = r.has_key('stop_times_saturday')
    sun_exists = r.has_key('stop_times_sunday')

    runi += 10
    runi -= (runi % 10)
    
    def do_route(stop_times, isweekday, issat, issun):
	global runi, ri, sti, time_points
	for run in stop_times:
	    runi += 1
	    rec(runf, r, [runi, ri, isweekday, issat, issun], [])
	    for x in xrange(len(time_points)):
		sti += 1
		stop = time_points[x]
		time = run[x]
		rec(stf, r, [sti, runi, stop, time], [],
		    [None, None, None, 't'])

    do_route(r['stop_times'], 1, not sat_exists, not sun_exists)
    if sat_exists:
	do_route(r['stop_times_saturday'], 0, 1, 0)
    if sun_exists:
	do_route(r['stop_times_sunday'], 0, 0, 1)
