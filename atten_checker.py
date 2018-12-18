import getpass
import telnetlib
import time
import re
import csv
from termcolor import colored, cprint

host = input("Enter OLT IP: ")
user = 'zte'  # input("Enter username: ")
password = 'zte'  # getpass.getpass()

tn = telnetlib.Telnet(host)
tn.read_until(b"Username:")
tn.write(user.encode('ascii') + b"\n")
if password:
    tn.read_until(b"Password:")
    tn.write(password.encode('ascii') + b"\n")

tn.write("terminal length 0".encode('ascii') + b"\n")
time.sleep(1)
tn.write("sho run".encode('ascii') + b"\n")
time.sleep(1)

output_str = ''
fetch = ''
while fetch.find('\nend') == -1:
    fetch = str(tn.read_very_eager().decode('ascii'))
    output_str += fetch
    if output_str.__contains__('More'):
        tn.write(" ".encode('ascii') + b"\n")
        time.sleep(0.1)

output_file = open('telnet_output.txt', 'w')
output_file.write(output_str)
output_file.close()

data = output_str.splitlines()

onus = re.findall('interface gpon-onu_\d+/\d+/\d+:\d+', output_str)
names = re.findall('(?<=name ).*', output_str)

results = []
with open('attenuation.csv', 'w', newline='') as csvfile:
    atten_writer = csv.writer(csvfile, delimiter=',')
    atten_writer.writerow(['Name', 'Port', 'Attenuation UP', 'Attenuation Down'])
    for o in onus:
        try:
            name = re.search('(?<=name ).*', output_str[output_str.find(o):]).group(0).replace('\r', '')
            cmd = "show pon power attenuation " + o[10:]
            tn.write(cmd.encode('ascii') + b"\n")
            time.sleep(0.5)
            fetch = str(tn.read_very_eager().decode('ascii'))
            up_db = re.search('\d\d.\d\d\d(?=\(dB\))', fetch).group(0).replace('\r', '')
            down_db = re.search('\d\d.\d\d\d(?=\(dB\))', fetch).group(0).replace('\r', '')

            result = "%s: %s: Up: %s Down: %s" % (name, o, up_db, down_db)

            if((float(up_db) <= 28) and (float(down_db) <= 28)):
                print(colored("%s: %s: Up: %s Down: %s" % (name, o, up_db, down_db), 'green'))
            elif((float(up_db) <= 30) and (float(down_db) <= 30)):
                print(colored("%s: %s: Up: %s Down: %s" % (name, o, up_db, down_db), 'yellow'))
            elif((float(up_db) > 30) or (float(down_db) > 30)):
                cprint("%s: %s: Up: %s Down: %s" % (name, o, up_db, down_db), 'white', 'on_red')

            results.append(result)
            atten_writer.writerow([name, o, up_db, down_db])
        except Exception as ex:
            print(colored("%s: %s: seems to be offline!" % (name, o), 'red'))