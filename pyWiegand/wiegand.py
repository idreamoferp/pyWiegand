import time, threading

CARD_MASK = 0b11111111111111110 # 16 ones
FACILITY_MASK = 0b1111111100000000000000000 # 8 ones

class Wieagnd:
    def __init__(self, card_read_callback):
        self.card_read_callback = card_read_callback
        self.bits = ""
        self.last_bit = time.time()
        self.bit_timeout = 0.0019
        self.register_timeout = 0.500
        self.th_timer_clear = threading.Thread(target=self.timer_clear, daemon=True).start()
        
    def timer_clear(self):
        while 1:
            time.sleep(0.01)
            try:
                if time.time() - self.last_bit > self.register_timeout:
                    #time since last bit was loo long, clear bit buffer
                    if self.bits:
                        print(".")
                    self.bits = ""
            except:
                pass
    
    def shift_in_bit(self, bit):
        this_bit = time.time()
        
        bit_timing =  this_bit - self.last_bit
        
        if bit_timing < self.bit_timeout:
            #too fast to be valid bit input
            print(str(bit_timing) + "*")
            return None
        
        print(bit_timing)
        
        
        #mark the time of this 
        self.last_bit = this_bit
        
        #append bit stream with this bit
        self.bits += bit
        
        if len(self.bits) < 26:
            #not enough bits to make a card read
            return None
        
        #decode card, and call callback
        #conver bit string to int
        card_read = int(self.bits,2)
        
        #decode facility and card number
        facility = (card_read & FACILITY_MASK ) >> 17
        card = ( card_read & CARD_MASK ) >> 1
        
        #clear register
        self.bits = ""
        
        #execute callback method
        threading.Thread(target=self.card_read_callback, args=(facility, card)).start()
            
    def D0(self, x=None):
        self.shift_in_bit("0")
        pass
    
    def D1(self, x=None):
        self.shift_in_bit("1")
        pass
    
if __name__ == "__main__":
    import RPi.GPIO as GPIO #RPi libs for interupts
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)  
    GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def callback(facility_id, card_id):
        print(f"Facility - {facility_id} Card - {card_id}")
        
    reader = Wieagnd(callback)
    
    GPIO.add_event_detect(20, GPIO.FALLING, callback=reader.D0)
    GPIO.add_event_detect(21, GPIO.FALLING, callback=reader.D1)
    
    while 1:
        time.sleep(10)
