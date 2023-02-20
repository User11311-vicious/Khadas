#!/usr/bin/python3
from math import *
from curses import COLOR_BLACK
from cv2 import CAP_V4L2, rectangle, putText, VideoCapture, VideoWriter, VideoWriter_fourcc, CAP_PROP_FOURCC, CAP_V4L, resize, FONT_HERSHEY_SIMPLEX, LINE_AA, destroyAllWindows, imshow, waitKey, CAP_PROP_FPS
from bluetooth import *
from datetime import datetime
import csv
import serial
from multiprocessing import Process, shared_memory
from time import *
import socket
#from RPi import GPIO

#settings_of_memory___and___gpio
pedal = shared_memory.ShareableList([0, 0, 0, 0, 0, 0], name="pedadl") #pedals
indi = shared_memory.ShareableList([0, ' '*128, ' '*128, ' '*128, ' '*128, ' '*128, ' '*128], name="indikd")
end = shared_memory.ShareableList([0, 0, 0, 0, True], name="edn")
#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(14, GPIO.OUT) #memory_zoomer
#GPIO.setup(16, GPIO.OUT) #memory_diod
#GPIO.setup(19, GPIO.OUT) #esp_zoomer
#GPIO.setup(20, GPIO.OUT) #esp_diod
#GPIO.setup(17, GPIO.OUT) #video_zoomer
#GPIO.setup(18, GPIO.OUT) #video_diod
#GPIO.setup(5, GPIO.OUT) #power_diod
#GPIO.setup(6, GPIO.OUT) #mpu_and_gps_diod
##################################

def dates():
    #excel_nastroyki
    fieldnames = ['Date', 'Speed, km/h', 'X-axis acceleration, m/s^2', 'Y-axis acceleration, m/s^2', 'Angular acceleration, rad/s^2', 'Gas', 'Brake', 'GPS']
    #nastroyki_bluetooth
    addr = "24:62:AB:E1:96:7A"
    channel = 1
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    s.connect((addr, channel))
    ##########################
    #nastroyka gps
    ser = serial.Serial('/dev/ttyUSB0')
    ser.baudrate = 115200
    prob = ''
    gas, tormos, velocity, info_gps, v0, a_x, g_x, a_y, r, gps_vel_2, info_gps_1 = '', '', 0, '', 0, 0.0, 0.0, 0.0, 0.0, '', ''
    ##############################################
    if end[1] == 0:
        # GPIO.output(6, True)
        # sleep(1)
        # GPIO.output(6, True)
        # sleep(1)
        # GPIO.output(6, True)
        sleep(1)
        end[1] = 1
    while 1:
        try:
            if end[4] == True:
                csv_main = '/home/ldprpc15/f/' + datetime.today().strftime('%Y-%m-%d %H_%M_%S') + '.csv'
                end[4] = 2
            if indi[0] == 1:
                addr = "24:62:AB:E1:96:7A"
                channel = 1
                s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                s.connect((addr, channel))
                indi[0] = 0
            ##################
            data_gps = ser.readline().decode('ISO-8859-1')
            if '$GNVTG' in data_gps:
                info_gps += data_gps
                info_gps = info_gps.split(',')
                velocity = float(info_gps[7])
                a_x = round((velocity - v0)/0.36, 1)
                v0 = velocity
                info_gps = ''
            if 'GNRMC' in data_gps:
                gps_vel_2 += data_gps
                g_x = float(gps_vel_2[9])
                g_x = round((g_x/180)*pi, 1)
                if g_x != 0:
                    r = a_x/(g_x/0.25)
                a_y = round(g_x**2*r, 1)
                gps_vel_2 = ''
            pedal[2] = a_x
            pedal[3] = a_y
            pedal[4] = g_x
            pedal[5] = int(velocity)
            #########
            data = s.recv(1024)
            data = data.decode('utf-8')
            data = data.split('|')
            if data == '' or data == None:
                end[3] = 1
            # GPIO.output(20, True)
            #tormos_starts...
            if 'Brake depressed' in data:
                tormos = 'Brake depressed'
                pedal[0] = 1
            elif 'Brake pressed' in data:
                tormos = 'Brake pressed'
                pedal[0] = 2
            elif 'Brake ready' in data:
                tormos = 'Brake ready'
                pedal[0] = 3
            #gas_starts...
            if 'Gas depressed' in data:
                gas = 'Gas depressed'
                pedal[1] = 1
            elif 'Gas pressed' in data:
                gas = 'Gas pressed'
                pedal[1] = 2
            elif 'Gas ready' in data:
                gas = 'Gas ready'
                pedal[1] = 3
            info_gps_1 += data_gps
            if info_gps_1 == '' or info_gps_1 == None:
                end[2] = 1
            with open(csv_main, mode="a+", encoding='ISO-8859-1') as a:
                writer = csv.DictWriter(a, fieldnames=fieldnames)
                if end[4] == 2:
                    writer.writeheader()
                    end[4] = False 
                writer.writerows([{'Date': datetime.now(), 'Speed, km/h': str(velocity), 'X-axis acceleration, m/s^2': a_x, 'Y-axis acceleration, m/s^2': a_y, 'Angular acceleration, rad/s^2': str(g_x), 'Gas': gas, 'Brake': tormos}])
                if 'BDGSA' in info_gps_1:
                    writer.writerows([{'Date': datetime.now(), 'Speed, km/h': str(velocity), 'X-axis acceleration, m/s^2': a_x, 'Y-axis acceleration, m/s^2': a_y, 'Angular acceleration, rad/s^2': str(g_x), 'Gas': gas, 'Brake': tormos, 'GPS': info_gps_1}])        
                    info_gps_1 = ''
        except OSError:
            indi[0] = 1
            if end[3] == 1:
                # GPIO.output(19, True)
                # GPIO.output(20, True)
                # GPIO.output(19, False)
                # GPIO.output(20, False)
                print('ok')
                end[3] = 0
                # sleep(0.25)
        except UnicodeDecodeError:
            if end[2] == 1:
                print('well')
                # GPIO.output(6, True)
                # GPIO.output(6, False)
                # sleep(0.25)
                end[2] = 0
    
def save_video(number, vid, name_vid, tiime):
    if end[1] == 1:
        if vid == '_v1':
            end[4] = True
        tiime += vid
        title_video = "/home/ldprpc15/f/" + tiime + '.avi'
        cap = VideoCapture(number)
        fourcc = VideoWriter_fourcc('M','J','P','G')
        cap.set(CAP_PROP_FOURCC,VideoWriter_fourcc('M','J','P','G'))
        out = VideoWriter(title_video, fourcc, 25.0, (1080, 720))   
        i = 0
        print('start')
        while 1:
            try:
                ret, frame = cap.read()
                if ret == 0:
                    continue
                re_frame = resize(frame, (1080,720))
                putText(re_frame, name_vid, (980,20), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 6)
                putText(re_frame, name_vid, (980,20), FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 1)
                if indi[0] == 1:
                    rectangle(re_frame, pt1=(0,30), pt2=(220,50), color=(255, 255, 255), thickness= -1)
                    putText(re_frame, 'Sensor error', (0,50), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                else:
                    if pedal[0] == 1:
                        rectangle(re_frame, pt1=(0,30), pt2=(190,50), color=(255, 255, 255), thickness= -1)
                        putText(re_frame, 'Brake depressed', (0,50), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                    elif pedal[0] == 2:
                        rectangle(re_frame, pt1=(0,30), pt2=(160,50), color=(0, 0, 255), thickness= -1)
                        putText(re_frame, 'Brake pressed', (0,50), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                    elif pedal[0] == 3:
                        rectangle(re_frame, pt1=(0,30), pt2=(135,50), color=(0, 255, 255), thickness= -1)
                        putText(re_frame, 'Brake ready', (0,50), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                    if pedal[1] == 1:
                        rectangle(re_frame, pt1=(0,5), pt2=(165,25), color=(255, 255, 255), thickness= -1)
                        putText(re_frame, 'Gas depressed', (0,20), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                    elif pedal[1] == 2:
                        rectangle(re_frame, pt1=(0,5), pt2=(140,25), color=(0, 0, 255), thickness= -1)
                        putText(re_frame, 'Gas pressed', (0,20), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                    elif pedal[1] == 3:
                        rectangle(re_frame, pt1=(0,5), pt2=(110,25), color=(0, 255, 255), thickness= -1)
                        putText(re_frame, 'Gas ready', (0,20), FONT_HERSHEY_SIMPLEX, 0.7, COLOR_BLACK, 2)
                putText(re_frame, 'X: ' + str(pedal[2]) + ' m/s^2', (0,95), FONT_HERSHEY_SIMPLEX, 0.6, COLOR_BLACK, 6)
                putText(re_frame, 'Y: ' + str(pedal[3]) + ' m/s^2', (0,127), FONT_HERSHEY_SIMPLEX, 0.6, COLOR_BLACK, 6)
                putText(re_frame, str(pedal[4]) + ' rad/s^2', (0,155), FONT_HERSHEY_SIMPLEX, 0.6, COLOR_BLACK, 6)
                putText(re_frame, str(pedal[5]) + ' km/h', (0,185), FONT_HERSHEY_SIMPLEX, 0.6, COLOR_BLACK, 6)
                putText(re_frame, 'X: ' + str(pedal[2]) + ' m/s^2', (0,95), FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
                putText(re_frame, 'Y: ' + str(pedal[3]) + ' m/s^2', (0,127), FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
                putText(re_frame, str(pedal[4]) + ' rad/s^2', (0,155), FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
                putText(re_frame, str(pedal[5]) + ' km/h', (0,185), FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 1)
                out.write(re_frame)
                if waitKey(1) == ord(' ') or i == 4500:
                    print('end')
                    print(str(i))
                    end[0] = 1
                    break
                i += 1
            except:
                # GPIO.output(18, True)
                # GPIO.output(17, False)
                print('videooo')
                sleep(0.25)
        cap.release()
        out.release()
        destroyAllWindows()

for i in range(3):
    # GPIO.output(5, True)
    # GPIO.output(5, False)
    sleep(1)
# GPIO.output(5, True)
head = True
sleep(1)
# output = subprocess.check_output(['sudo', 'chmod', '666', '/dev/ttyUSB0'])
for i in range(30000):
    while 1:
        st = os.statvfs('/home/ldprpc15/f/')
        du = st.f_bsize * st.f_bavail / 1024 / 1024 / 1024
        if du > 0.01:
            # GPIO.output(16, True)
            p1 = Process(target=dates)
            ms = datetime.today().strftime('%f') + '0000'
            ms = ms[:3]
            name = datetime.today().strftime('%Y-%m-%d %H_%M_%S')
            tiime = name + '_' + ms
            p3 = Process(target=save_video, args=('rtsp://192.168.1.50:554/user=admin_password=tlJwpbo6_channel=1_stream=0&protocol=unicast.sdp?real_stream', '_v3', 'ID003', tiime))
            p5 = Process(target=save_video, args=('rtsp://192.168.1.149:554/user=admin_password=dyRSSRmL_channel=1_stream=0&protocol=unicast.sdp?real_stream', '_v2', 'ID002', tiime))
            p7 = Process(target=save_video, args=('rtsp://192.168.1.35:554/user=admin_password=tlJwpbo6_channel=1_stream=0&protocol=unicast.sdp?real_stream', '_v1', 'ID001', tiime))
            if head == True:
                p1.start()
            p3.start()
            p5.start()
            p7.start()
            p3.join()
            p5.join()
            p7.join()
            head = False
            if head == False:
                break
        else:
            while True:
                # GPIO.output(19, True)
                # GPIO.output(20, True)
                # GPIO.output(19, False)
                print('memoryyy')
                sleep(0.25)

pedal.shm.close()
pedal.shm.unlink()
indi.shm.close()
indi.shm.unlink()
end.shm.close()
end.shm.unlink()
