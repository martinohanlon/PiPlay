from gpiozero import Button, LEDBarGraph

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

class PiPlayBoard():
    
    def __init__(self, inverted = False):
        #persist pins
        if inverted:
            self.pins = INVERTEDPINS
        else:
            self.pins = PINS

        #create buttons
        self.middle = Button(self.pins["BUT_MID"])
        self.leftup = Button(self.pins["BUT_L_UP"])
        self.leftdown = Button(self.pins["BUT_L_DOWN"])
        self.rightup = Button(self.pins["BUT_R_UP"])
        self.rightdown = Button(self.pins["BUT_R_DOWN"])
        self.left = Button(self.pins["BUT_L"])
        self.right = Button(self.pins["BUT_R"])

        #create a tuple of the buttons
        self.buttons = (self.middle,
                        self.leftup,
                        self.leftdown,
                        self.rightup,
                        self.rightdown,
                        self.left,
                        self.right)

        #create the led bargraph
        self.ledbargraph = LEDBarGraph(*self.pins["LEDBARGRAPH"])

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
    
