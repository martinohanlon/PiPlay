import mpd
from time import sleep, time
import thread


MPD_HOST = "localhost"
MPD_PORT = "6600"
MPD_PASSWORD = "volumio" # password for Volumio / MPD

LEEPLAYLISTNAME = "Testplaylist"
MARTPLAYLISTNAME = "Testplaylist2"

def safeMPDExecute(func, *arg): 
    success = False
    try:
        func(*arg)
        success = True
    except mpd.CommandError as e:
        print "Error({0})".format(e.args)
    return success

def getplaylist(client):
    while True:
        playlists = client.listplaylists()
        print(playlists[0]["playlist"])
        sleep(0.2)

def getstatus(client):
    while True:
        print(client.status())
        sleep(0.4)

# Connect with MPD
client = mpd.MPDClient()
#client2 = mpd.MPDClient()
connected = False
client.connect(MPD_HOST, MPD_PORT)
#client2.connect(MPD_HOST, MPD_PORT)

#thread.start_new_thread(getplaylist, (client,))
#thread.start_new_thread(getstatus, (client2,))


#print("Connected")
#print(client.status())
#print(client.status()["state"])
#print(client.listplaylists())
#print(client.playlistinfo())
#print(client.playlist())
while True:
    now = time()
    status = client.status()
    print("it took {}".format(now - time()))
    print(status)
    sleep(1)
