#Martin O'Hanlon
#stuffaboutcode.com

import mpd

from piplayboard import PiPlayBoard
from time import sleep
from Queue import Queue
from threading import Thread

#Generic class to hold an event
#Events are queued and handled FIFO
class Event():
    class EventType():
        ONOFF = 1
        PLAYLIST = 2
        TRACK = 3
        VOL = 4
        PLAYPAUSE = 5
        SHUTDOWN = 6
        VOLCHANGED = 7
        PINGMPD = 8
        
    def __init__(self, eventType, value = None):
        self.eventType = eventType
        self.value = value

#Class to manage an event
class Amp():
    def __init__(self, mutePin):
        self.mutePin = mutePin

        #setup pins
        GPIO.setup(mutePin, GPIO.OUT)

    @property
    def muted(self):
        if GPIO.input(self.mutePin) == 1:
            return True
        else:
            return False

    def unmute(self):
        GPIO.output(self.mutePin, 1)

    def mute(self):
        GPIO.output(self.mutePin, 0)

class MPDStatusMonitor(Thread):
    def __init__(self, mpd_host, mpd_port, eventQ, interval = 0.1):
        #setup threading
        Thread.__init__(self)

        self.mpd_host = mpd_host
        self.mpd_port = mpd_port
        self.eventQ = eventQ
        self.interval = interval

        self.running = False
        self.stopped = True

    def run(self):
        self.running = True
        self.stopped = False

        self.mpd = mpd.MPDClient()
        self.mpd.connect(self.mpd_host, self.mpd_port)

        self.mpdstatus = self.mpd.status()
        self.eventQ.put(Event(Event.EventType.VOLCHANGED, int(self.mpdstatus["volume"])))
        
        while(not self.stopped):
            #keep getting the status
            mpdstatusnow = self.mpd.status()

            #whats changed?
            #volume?
            if self.mpdstatus["volume"] != mpdstatusnow["volume"]:
                self.eventQ.put(Event(Event.EventType.VOLCHANGED, int(mpdstatusnow["volume"])))

            self.mpdstatus = mpdstatusnow
            
            sleep(self.interval)

        self.mpd.close()
        self.running = False

    def stop(self):
        self.stopped = True
        while(self.running):
            sleep(0.01)

class MPDKeepAlive(Thread):
    def __init__(self, eventQ, interval = 1):
        #setup threading
        Thread.__init__(self)
        
        self.eventQ = eventQ
        self.interval = interval

        self.running = False
        self.stopped = True

    def run(self):
        self.running = True
        self.stopped = False
        while(not self.stopped):
            self.eventQ.put(Event(Event.EventType.PINGMPD))
            sleep(self.interval)

        self.running = False

    def stop(self):
        self.stopped = True
        while(self.running):
            sleep(0.01)

#class to control mpd
class MPDControl():
    def __init__(self, inverted = False, mpd_host = "localhost", mpd_port = "6600"):
        #create the pi play board
        self.piplayboard = PiPlayBoard(inverted)
        self.piplayboard.middle.when_pressed = self._playpausebutton
        self.piplayboard.middle.when_held = self._onoffbutton
        self.piplayboard.right.when_pressed = self._volupbutton
        self.piplayboard.right.when_held = self._volupbutton
        self.piplayboard.left.when_pressed = self._voldownbutton
        self.piplayboard.left.when_held = self._voldownbutton
        self.piplayboard.rightdown.when_pressed = self._tracknextbutton
        self.piplayboard.leftdown.when_pressed = self._trackprevbutton
        self.piplayboard.rightup.when_pressed = self._playlistnextbutton
        self.piplayboard.leftup.when_pressed = self._playlistprevbutton

        #create connection to MPD client / volumio
        self.mpd_host = mpd_host
        self.mpd_port = mpd_port
        
        self.stopped = True
        self.running = False
        
        self.eventQ = Queue()

        self.currentplaylist = None

    def start(self):
        
        self.stopped = False
        self.running = True

        self.mpd = mpd.MPDClient()
        self.mpd.connect(self.mpd_host, self.mpd_port)
        mpdkeepalive = MPDKeepAlive(self.eventQ)
        mpdkeepalive.start()

        self.mpdstatusmon = MPDStatusMonitor(self.mpd_host, self.mpd_port, self.eventQ)
        self.mpdstatusmon.start()
        
        self._off()
        
        try:
            while not self.stopped:
                #process events
                while not self.eventQ.empty():
                    event = self.eventQ.get()
                    print(event.eventType)
                    self._processevent(event)
                    
                sleep(0.01)
                
        finally:
            self.mpdstatusmon.stop()
            mpdkeepalive.stop()
            self.mpd.close()
        
        self.running = False

    def stop(self):
        self.stopped = True
        while self.running:
            sleep(0.1)

    #process events in the q
    def _processevent(self, event):

        if (event.eventType == Event.EventType.ONOFF):
            self._onoff()
        elif (event.eventType == Event.EventType.PINGMPD):
            self._pingMPD()
        elif (event.eventType == Event.EventType.VOLCHANGED):
                self._displayvolume(event.value)

        #process on events
        if self.on:
            if (event.eventType == Event.EventType.PLAYPAUSE):
                self._playpause()
            elif (event.eventType == Event.EventType.VOL):
                self._volume(event.value)
            elif (event.eventType == Event.EventType.TRACK):
                self._skiptrack(event.value)
            elif (event.eventType == Event.EventType.PLAYLIST):
                self._skipplaylist(event.value)
            
    #button call backs
    def _onoffbutton(self):
        self.eventQ.put(Event(Event.EventType.ONOFF))

    def _playpausebutton(self):
        self.eventQ.put(Event(Event.EventType.PLAYPAUSE))

    def _volupbutton(self):
        self.eventQ.put(Event(Event.EventType.VOL, 1))

    def _voldownbutton(self):
        self.eventQ.put(Event(Event.EventType.VOL, -1))

    def _tracknextbutton(self):
        self.eventQ.put(Event(Event.EventType.TRACK, 1))

    def _trackprevbutton(self):
        self.eventQ.put(Event(Event.EventType.TRACK, -1))

    def _playlistnextbutton(self):
        self.eventQ.put(Event(Event.EventType.PLAYLIST, 1))

    def _playlistprevbutton(self):
        self.eventQ.put(Event(Event.EventType.PLAYLIST, -1))

    #functions to control mpd
    def _safeMPDExec(self, func, *arg): 
        success = False

        try:
            func(*arg)
            success = True

        except mpd.CommandError as e:
            print "Error({0})".format(e.args)

        finally:
            return success

    def _onoff(self):
        if self.on:
            self._off()
        else:
            self._on()
            
    def _off(self):
        self._stop()
        self.on = False
        self.piplayboard.ledbargraph.turnoff()

    def _on(self):
        self._play()
        self.on = True
        self.piplayboard.ledbargraph.turnon()

    def _playpause(self):
        state = self.mpd.status()["state"]
        
        if state == "play":
            self._safeMPDExec(self.mpd.pause,1)
        elif state == "stop":
            self._safeMPDExec(self.mpd.play)
        elif state == "pause":
            self._safeMPDExec(self.mpd.pause,0)

    def _play(self):
        state = self.mpd.status()["state"]
        if state == "stop":
            self._safeMPDExec(self.mpd.play)
        elif state == "pause":
            self._safeMPDExec(self.mpd.pause,0)

    def _stop(self):
        self._safeMPDExec(self.mpd.stop)

    def _volume(self, value):
        volume = int(self.mpd.status()["volume"])
        self._safeMPDExec(self.mpd.setvol, volume + value)

    def _skiptrack(self, value):
        if value == 1:
            self._safeMPDExec(self.mpd.next)
        elif value == -1:
            self._safeMPDExec(self.mpd.previous)

    def _skipplaylist(self, value):
        self._selectplaylist(value)
        self._play()
    
    def _selectplaylist(self, value):
        #if a playlist is selected, save it
        if self.currentplaylist != None:
            self._saveplaylist(self.currentplaylist)
        
        #get the playlists
        playlists = self.mpd.listplaylists()
        
        #find the current playlist position
        playlistpos = 0
        for pos in range(0, len(playlists)):
            if playlists[pos]["playlist"] == self.currentplaylist:
                playlistpos = pos
                break

        #which playlist are we skipping to
        playlistpos = playlistpos + value

        #are we on the last playlist?
        if playlistpos == len(playlists): playlistpos = 0

        #are we past the first playlist?
        if playlistpos == -1: playlistpos = len(playlists) - 1

        #load the playlist
        self._loadplaylist(playlists[playlistpos]["playlist"])
            
    def _loadplaylist(self, playlistname):
        self._safeMPDExec(self.mpd.clear)
        if not self._safeMPDExec(self.mpd.load, playlistname):
            print "Failed to load playlist ({})".format(playlistname)
        self.currentplaylist = playlistname
        #set repeat on
        self._safeMPDExec(self.mpd.repeat, 1)
        
    def _saveplaylist(self, playlistname):
        #remove the playlist
        self._safeMPDExec(self.mpd.rm, playlistname)
        self._safeMPDExec(self.mpd.save, playlistname)

    def _pingMPD(self):
        self._safeMPDExec(self.mpd.ping)

    #functions to update the LED bargraph
    def _displayvolume(self, volume):
        #set the value on the led bargraph
        self.piplayboard.ledbargraph.value = volume / 100.0
        
if __name__ == "__main__":
    mpdcontrol = MPDControl()
    mpdcontrol.start()
