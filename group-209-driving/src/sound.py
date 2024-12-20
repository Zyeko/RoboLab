import ev3dev.ev3 as ev3


def playSound(text):
    """
    This function will use text-to-speech to verbalise everything that is giving to it
    """

    sound = ev3.Sound()

    sound.set_volume = 100
    
    if text == "beep":
        sound.beep()
    elif text == "message":
        sound.beep("-l 100 -f 102 -D 100 -n -l 200 -f 102 -D 100 -n -l 200 -f 392 -D 100")
    elif text == "target":
        sound.beep("-l 500 -f 402 -D 100 -n -l 400 -f 402 -D 100 -n -l 200 -f 792 -D 100")
    elif text == "path":
        sound.beep("-l 70 -f 802 -D 100")

    elif text != "End":
        sound.speak(text)
    else:
        sound.beep("-f 130 -l 100 -n -f 262 -l 100 -n -f 330 -l 100 -n -f 392 -l 100 -n -f 523 -l 100 -n -f 660 -l 100 -n -f 784 -l 300 -n -f 660 -l 300 -n -f 146 -l 100 -n -f 262 -l 100 -n -f 311 -l 100 -n -f 415 -l 100 -n -f 523 -l 100 -n -f 622 -l 100 -n -f 831 -l 300 -n -f 622 -l 300 -n -f 155 -l 100 -n -f 294 -l 100 -n -f 349 -l 100 -n -f 466 -l 100 -n -f 588 -l 100 -n -f 699 -l 100 -n -f 933 -l 300 -n -f 933 -l 100 -n -f 933 -l 100 -n -f 933 -l 100 -n -f 1047 -l 400")
        
        
    """
        ("-l 350 -f 392 -D 100 -n -l 350 -f 392 -D 100 -n -l 350 \
     -f 392 -D 100 -n -l 250 -f 311.1 -D 100 -n -l 25 \
     -f 466.2 -D 100 -n -l 350 -f 392 -D 100 -n -l 250 \
     -f 311.1 -D 100 -n -l 25 -f 466.2 -D 100 -n -l 700 \
     -f 392 -D 100 -n -l 350 -f 587.32 -D 100 -n -l 350 \
     -f 587.32 -D 100 -n -l 350 -f 587.32 -D 100 -n -l 250 \
     -f 622.26 -D 100 -n -l 25 -f 466.2 -D 100 -n -l 350 \
     -f 369.99 -D 100 -n -l 250 -f 311.1 -D 100 -n -l 25 \
     -f 466.2 -D 100 -n -l 700 -f 392 -D 100 -n -l 350 \
     -f 784 -D 100 -n -l 250 -f 392 -D 100 -n -l 25 \
     -f 392 -D 100 -n -l 350 -f 784 -D 100 -n -l 250 \
     -f 739.98 -D 100 -n -l 25 -f 698.46 -D 100 -n -l 25 \
     -f 659.26 -D 100 -n -l 25 -f 622.26 -D 100 -n -l 50 \
     -f 659.26 -D 400 -n -l 25 -f 415.3 -D 200 -n -l 350 \
     -f 554.36 -D 100 -n -l 250 -f 523.25 -D 100 -n -l 25 \
     -f 493.88 -D 100 -n -l 25 -f 466.16 -D 100 -n -l 25 \
     -f 440 -D 100 -n -l 50 -f 466.16 -D 400 -n -l 25 \
     -f 311.13 -D 200 -n -l 350 -f 369.99 -D 100 -n -l 250 \
     -f 311.13 -D 100 -n -l 25 -f 392 -D 100 -n -l 350 \
     -f 466.16 -D 100 -n -l 250 -f 392 -D 100 -n -l 25 \
     -f 466.16 -D 100 -n -l 700 -f 587.32 -D 100 -n -l 350 \
     -f 784 -D 100 -n -l 250 -f 392 -D 100 -n -l 25 \
     -f 392 -D 100 -n -l 350 -f 784 -D 100 -n -l 250 \
     -f 739.98 -D 100 -n -l 25 -f 698.46 -D 100 -n -l 25 \
     -f 659.26 -D 100 -n -l 25 -f 622.26 -D 100 -n -l 50 \
     -f 659.26 -D 400 -n -l 25 -f 415.3 -D 200 -n -l 350 \
     -f 554.36 -D 100 -n -l 250 -f 523.25 -D 100 -n -l 25 \
     -f 493.88 -D 100 -n -l 25 -f 466.16 -D 100 -n -l 25 \
     -f 440 -D 100 -n -l 50 -f 466.16 -D 400 -n -l 25 \
     -f 311.13 -D 200 -n -l 350 -f 392 -D 100 -n -l 250 \
     -f 311.13 -D 100 -n -l 25 -f 466.16 -D 100 -n -l 300 \
     -f 392.00 -D 150 -n -l 250 -f 311.13 -D 100 -n -l 25 \
     -f 466.16 -D 100 -n -l 700 -f 392")
    """