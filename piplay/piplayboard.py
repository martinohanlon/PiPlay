from gpiozero import Button, LEDBarGraph
from threading import Timer
from time import sleep

PINS = {"BUT_MID": 26,
        "BUT_L_UP": 4,
        "BUT_L_DOWN": 17,
        "BUT_R_UP": 23,
        "BUT_R_DOWN": 27,
        "BUT_L": 13,
        "BUT_R": 16,
        "LEDBARGRAPH": (24, 25, 10, 9, 11, 8, 7, 5, 6, 12)}

INVERTEDPINS ={"BUT_MID": 26,
               "BUT_L_UP": 27,
               "BUT_L_DOWN": 23,
               "BUT_R_UP": 17,
               "BUT_R_DOWN": 4,
               "BUT_L": 16,
               "BUT_R": 13,
               "LEDBARGRAPH": (12, 6, 5, 7, 8, 11, 9, 10, 25, 24)} 

class HoldableButton(Button):
    def __init__(self, pin=None, pull_up=True, bounce_time=None, hold_time=1, repeat=False): 

        super(HoldableButton, self).__init__(pin, pull_up, bounce_time)

        # Set Button when_pressed and when_released to call local functions
        # cant use super() as it doesn't support setters
        Button.when_pressed.fset(self, self._when_button_pressed)
        Button.when_released.fset(self, self._when_button_released)

        self._when_held = None
        self._when_pressed = None
        self._when_released = None

        self.hold_time = hold_time
        self.repeat = repeat
        self._held_timer = None

    #override button when_pressed and when_released
    @property
    def when_pressed(self):
        return self._when_pressed

    @when_pressed.setter
    def when_pressed(self, value):
        self._when_pressed = value

    @property
    def when_released(self):
        return self._when_released

    @when_released.setter
    def when_released(self, value):
        self._when_released = value

    @property
    def when_held(self):
        return self._when_held

    @when_held.setter
    def when_held(self, value):
        self._when_held = value

    def _when_button_pressed(self):
        if self._when_pressed != None:
            self._when_pressed()

        self._start_hold()

    def _when_button_released(self):
        if self._when_released != None:
            self.when_released()

        self._stop_hold()

    def _start_hold(self):
        if self._when_held != None:
            self._held_timer = Timer(self.hold_time, self._button_held)
            self._held_timer.start()

    def _stop_hold(self):
        if self._held_timer != None:
            self._held_timer.cancel()

    def _button_held(self):
        self._when_held()
        if self.repeat == True and self.is_pressed == True:
            self._start_hold()

class LEDDisplay(LEDBarGraph):
    def __init__(self, *pins, **kwargs):

        self._displayon = True

        super(LEDDisplay, self).__init__(*pins, **kwargs)
        
        self.this_value = self.value
        
    def turnon(self):
        print("turn on")
        if not self._displayon:
            self._displayon = True
            for i in range(0, 11):
                self.value = i / 10.0
                sleep(0.1)
            self.value = self.this_value

    def turnoff(self):
        print("turn off")
        if self._displayon:
            self.this_value = self.value
            for i in range(10, -1, -1):
                self.value = i / 10.0
                sleep(0.1)
            self._displayon = False

    @property
    def value(self):
         return super(LEDDisplay, self).value
    
    @value.setter
    def value(self, value):
        
        if self._displayon:
            LEDBarGraph.value.fset(self, value)
        else:
            self.this_value = value
            

class PiPlayBoard():
    
    def __init__(self, inverted = False):
        #persist pins
        if inverted:
            self.pins = INVERTEDPINS
        else:
            self.pins = PINS

        #create buttons
        self.middle = HoldableButton(self.pins["BUT_MID"], hold_time = 2)
        self.leftup = Button(self.pins["BUT_L_UP"])
        self.leftdown = Button(self.pins["BUT_L_DOWN"])
        self.rightup = Button(self.pins["BUT_R_UP"])
        self.rightdown = Button(self.pins["BUT_R_DOWN"])
        self.left = HoldableButton(self.pins["BUT_L"], hold_time = 0.1, repeat = True)
        self.right = HoldableButton(self.pins["BUT_R"], hold_time = 0.1, repeat = True)

        #create a tuple of the buttons
        self.buttons = (self.middle,
                        self.leftup,
                        self.leftdown,
                        self.rightup,
                        self.rightdown,
                        self.left,
                        self.right)

        #create the led bargraph
        self.ledbargraph = LEDDisplay(*self.pins["LEDBARGRAPH"])

#test
if __name__ == "__main__":

    def button_pressed(button):
        print("pressed {}".format(button.pin))
    
    piplayboard = PiPlayBoard(True)
    for button in piplayboard.buttons:
        button.when_pressed = button_pressed
    for v in range(-10, 10):
        piplayboard.ledbargraph.value = v
    while True:
        pass
    
