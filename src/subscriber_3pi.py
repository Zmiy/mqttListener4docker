import json
import ssl
import datetime
import paho.mqtt.client as mqtt
import psycopg2
import base64

with open("config/CommonConfig.json", 'r') as f:
    config = json.load(f)

# This is the Subscriber
# hostname
broker =  config['mqttClientOptions']['host'];  
print(broker)
# port
port = config['mqttClientOptions']['port'];
certPath = config['mqttCertificatePath'];
# time to live
timelive = 40;
# subscribe topic
print(config['mqttPlaceID'] + "/" + config['mqttGroupID'] + "/" + config['mqttTOPIC']);
mqttTopic = config['mqttPlaceID'] + "/" + config['mqttGroupID'] + "/" + config['mqttTOPIC'];

mqttUsr = config['mqttClientOptions'].get('mqttUsr',None);
mqttPsw = config['mqttClientOptions'].get('mqttPsw', None);
mqttUsr = None if mqttUsr == "" else mqttUsr;
print (mqttUsr);

dic_lastValues = {}


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(mqttTopic)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed ", client.topic, userdata);
    pass 

def on_publish(client, userdata, result):
    print("An alarm message was published.")
    pass


def count_of_rfid(data):
    count = 0
    data_base64 = base64.decodebytes(data.encode("ascii"))  # int.from_bytes(base64.b64decode(data.encode()), 'big')
    print(data_base64, " ", len(data_base64) / 8)
    for i in range(0, 256, 8):
        val = 0
        for j in range(8):
            val += data_base64[i + j]
        if val > 0:  # Tag founded
            count += 1
    return count


def data_manipulation(count, trayid):
    if trayid in dic_lastValues:
        lastcount = dic_lastValues[trayid]
        if count != lastcount:
            dic_lastValues[trayid] = count
            # do Alert (lastCount, Count)
            alert_msg_json = {"message": "Count of Rfid was changed", "oldValue": lastcount, "newValue": count}
            ret = client.publish(config['mqttPlaceID'] + "/" + trayid + "/" + "Alert", json.dumps(alert_msg_json))
            print("ret= ", ret)
            print("Send Alert: ", alert_msg_json)
    else:
        dic_lastValues[trayid] = count


def on_message(client, userdata, msg):
    # global connection
    connection = None
    dt = datetime.datetime.now()
    print(dt, ' Topic: ', msg.topic)
    topic = msg.topic.split('/')

    # print(dt, " ", type(topic[1]))
    data_in = msg.payload.decode("utf-8", "ignore")
    data_in_sql = json.dumps({"hotelname": topic[0], "trayId": topic[1], "data": data_in})
    # print("Type of received data", type(data_in))
    print("Received data", data_in)
    # print("Convert to JSON", json.loads(data_in))
    count = count_of_rfid(data_in)
    data_manipulation(count, topic[1])
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="password",
                                      host="db",
                                      port="5432",
                                      database="loging")
        cursor = connection.cursor()

        insert_query = '''INSERT INTO loging (time, data, trayid, countofrfid)
        VALUES (%s, %s, %s, %s)'''
        cursor.execute(insert_query, (dt, data_in_sql, topic[1], count,))
        connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(dt, " Error while insert dat to the 'loging' table", error)
    finally:
        # closing database connection.
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")


client = mqtt.Client('pythonClient');
print(certPath);
print(certPath + '/server.crt',certPath + '/client.crt', certPath + '/client.key');
client.tls_set(certPath + '/server.crt', certPath + '/client.crt', certPath + '/client.key', ssl.CERT_REQUIRED,
               ssl.PROTOCOL_TLSv1_2)
if mqttUsr != None:
    print("user/password: ",mqttUsr,"/", mqttPsw)
    client.username_pw_set(mqttUsr, mqttPsw)
client.connect(broker, port, timelive)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_subscribe = on_subscribe
client.loop_forever()
