import time, threading 

CARD_MASK = 0b11111111111111110 # 16 ones
FACILITY_MASK = 0b1111111100000000000000000 # 8 ones

# Max pulse interval: 2ms
# pulse width: 50us

class Wiegand:
    def __init__(self, callback):
        """
        callback - the function called (with two args: card ID and cardcount)
                   when a card is detected.  Note that micropython interrupt
                   implementation limitations apply to the callback!
        """
        self.callback = callback
        self.last_card = None
        self.next_card = 0
        self._bits = 0
        self.last_bit_read = None
        self.cards_read = 0

    def on_pin(self, is_one, newstate):
        now = time.time()
        if self.last_bit_read is not None and now - self.last_bit_read < 0.0016:
            # too fast
            return
        
        if self.next_card:
            if now - self.last_bit_read > 0.25:
                self.next_card = 0
                self._bits = 0
        
        self.last_bit_read = now
        self.next_card <<= 1
        if is_one: self.next_card |= 1
        self._bits += 1
        if self._bits == 26:
            
            self._cardcheck()
        
        
    def get_card(self):
        if self.last_card is None:
            return None
        return ( self.last_card & CARD_MASK ) >> 1
        
    def get_facility_code(self):
        if self.last_card is None:
            return None
        # Specific to standard 26bit wiegand
        return ( self.last_card & FACILITY_MASK ) >> 17

    def _cardcheck(self):
        if self.last_bit_read is None: return
    
        # too slow - new start!
        self.last_bit_read = None
        self.last_card = self.next_card
        self.next_card = 0
        self._bits = 0
        self.cards_read += 1
        self.callback(self.get_card(), self.get_facility_code(), self.cards_read)


if __name__ == "__main__":
    def w_callback(card, facility_code, num_cards_read):
        print(card)
        
    w = Wiegand(callback=w_callback)
    
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    d0 = 26
    d1 = 27
    
    GPIO.setup(d0, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    GPIO.setup(d1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    
    def pin_change(x):
        
        pin_1 = False
        if x == d1:
            pin_1 = True
            
        pin_value = GPIO.input(x)    
        w.on_pin(pin_1, pin_value)
    
    GPIO.add_event_detect(d0, GPIO.FALLING, callback=pin_change)  
    GPIO.add_event_detect(d1, GPIO.FALLING, callback=pin_change)  
    
    while 1:
        time.sleep(.1)
