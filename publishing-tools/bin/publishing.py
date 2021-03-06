from datetime import datetime, timedelta
import csv


class Interval:

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, dt):
        return ((self.start is None or self.start < dt) and
                (self.end is None or dt <= self.end))

    def __eq__(self, obj):
        return (isinstance(obj, Interval) and
                self.start == obj.start and
                self.end == obj.end)

    def __repr__(self):
        return repr((self.start, self.end))


def make_interval_list(events):
    intervals = []

    for event in sorted(events, key=lambda e: e['timestamp']):
        if event['event'] in ['commissioned']:
            start = event['timestamp']
            if len(intervals) == 0 or intervals[-1].end is not None:
                intervals.append(Interval(start, None))

        if event['event'] in ['decommissioned', 'retired']:
            end = event['timestamp']
            if len(intervals) > 0 and intervals[-1].end is None:
                intervals[-1].end = end

    return intervals


def load_nodes_metadata(filename):
    events = []

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
            except ValueError:
                continue

            events.append({
                'node_id': row['node_id'][-12:].lower(),
                'project_id': row['project_id'],
                'vsn': row['vsn'].upper(),
                'address': row['address'],
                'lat': lat,
                'lon': lon,
                'description': row['description'],
            })

    return events


def load_timestamp(timestamp):
    return datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S')


def load_events_metadata(filename):
    events = []

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            events.append({
                'node_id': row['node_id'][-12:].lower(),
                'timestamp': load_timestamp(row['timestamp']),
                'event': row['event'].lower(),
                'comment': row['comment'],
            })

    return events


# NOTE mutates nodes. may change in future.
def join_metadata(nodes, events):
    nodes_by_id = {node['node_id']: node for node in nodes}

    for node in nodes:
        node['events'] = []

    for event in events:
        try:
            node = nodes_by_id[event['node_id']]
        except KeyError:
            continue

        node['events'].append(event)

    for node in nodes:
        node['commissioned'] = make_interval_list(node['events'])

    return nodes


def load_project_metadata(basepath):
    nodes = load_nodes_metadata(basepath + '/nodes.csv')
    events = load_events_metadata(basepath + '/events.csv')
    return join_metadata(nodes, events)


def load_sensor_metadata(filename):
    sensors = {}

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            try:
                minval = float(row['minval'])
            except ValueError:
                minval = None

            try:
                maxval = float(row['maxval'])
            except ValueError:
                maxval = None

            # hold over until after field conversion
            try:
                sensor_id = row['sensor_id']
            except KeyError:
                sensor_id = row['sensor'] + '.' + row['parameter']

            sensors[sensor_id] = {
                'range': Interval(minval, maxval)
            }

    return sensors


def daterange(start, end):
    for i in range((end - start).days + 1):
        yield start + timedelta(days=i)


def published_dates(project_metadata):
    for node in project_metadata:
        for interval in node['commissioned']:
            start = interval.start.date()
            end = (interval.end or datetime.now()).date()
            for date in daterange(start, end):
                yield node, date


def filter_view(metadata, reader, writer):
    nodes_by_id = {node['node_id']: node for node in metadata}

    def isviewable(fields):
        node_id = fields[0]
        timestamp = load_timestamp(fields[1])

        if node_id not in nodes_by_id:
            return False

        node = nodes_by_id[node_id]

        return any(timestamp in interval for interval in node['commissioned'])

    csvreader = csv.reader(reader, delimiter=';')
    csvwriter = csv.writer(writer, delimiter=';')
    csvwriter.writerows(filter(isviewable, csvreader))


def filter_sensors(metadata, reader, writer):
    def isvalid(fields):
        sensor = fields[4]
        param = fields[5]

        try:
            value = float(fields[6])
        except ValueError:
            return False

        name = '.'.join([sensor, param])

        if name not in metadata:
            return False

        params = metadata[name]
        return value in params['range']

    csvreader = csv.reader(reader, delimiter=';')
    csvwriter = csv.writer(writer, delimiter=';')
    csvwriter.writerows(filter(isvalid, csvreader))
