
import datetime
import hashlib
import re

def get_user_host(line):
    line_list = line.split()
    user = ''
    host = ''
    if len(line_list) == 7: 
        user_temp = line_list[2]
        host_temp = line_list[4]
        if re.findall(r'\[.+\]', user_temp):
            user = re.findall(r'\[.+\]', user_temp)[0][1:-1]
        if re.findall(r'\[.+\]', host_temp):
            host = re.findall(r'\[.+\]', host_temp)[0][1:-1]
    elif len(line_list) == 8:
        user_temp = line_list[2]
        host = line_list[4]
        if re.findall(r'\[.+\]', user_temp):
            user = re.findall(r'\[.+\]', user_temp)[0][1:-1]
    else:
        pass
    return user,host
        
    
with open('/tmp/slow.log', 'r') as file:
    log = {}
    first_log = True
    global dbname 
    dbname = ''
    for line in file:
        if re.findall(r'^# Time: ((?:[0-9: ]{15})|(?:[-0-9: T]{19}))', line):
            if first_log:
                first_log = False
            else:
                log = {}
            time = datetime.datetime(int(line[8:12]), int(line[13:15]),
                                                                   int(line[16:18]),
                                                                   int(line[19:21]), int(line[22:24]),
                                                                   int(line[25:27])).strftime('%Y-%m-%d %H:%M:%S')
            log['time'] = time
        elif re.findall(r'# User\@Host: ([^\[]+|\[[^[]+\]).*?@ (\S*) \[(.*)\]\s*(?:Id:\s*(\d+))?', line):
            user,host = get_user_host(line)
            log['user'] = user
            log['host'] = host
        elif re.findall(r'# Query_time: .+', line):
            time = line.split()
            log['query_time'] = float(time[2])
            log['lock_time'] = float(time[4])
            log['rows_sent'] = float(time[6])
            log['rows_examined'] = float(time[8])
        elif re.findall(r'^use ([^;]+)', line):
            dbname = re.findall(r'^use ([^;]+)', line)[0]
            log['database'] = dbname
            
        elif line[0:14] == "SET timestamp=":
            log['timestamp'] = line.split('=')[1][0:-1]
        elif line[0:1] == '/' or line[0:3] == 'Tcp' or line[0:4] == 'Time':
            pass
        else:
            line = line.strip('\n')
            line_d = re.sub(r'\d+', "?", line)
            line_s = re.sub(r'([\'\"]).+?([\'\"])', "?", line_d)
            sql_parttern = re.sub(r'\(\?.+?\)', "(?)", line_s)
            log['sql_parttern'] = sql_parttern
            m1 = hashlib.md5()
            m1.update(str(sql_parttern).encode('utf-8'))
            fingerprint = m1.hexdigest()
            log['fingerprint'] = fingerprint
            log.setdefault('database', dbname)
            print(log)
            
            
