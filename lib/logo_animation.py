import framebuf
import time
from hardware import hw
import logo


def Logo(button):
    oled = hw.oled
    logo_fb = framebuf.FrameBuffer(
        logo.logo_data, logo.logo_width, logo.logo_height, framebuf.MONO_VLSB)

    # reveal line by line
    for row in range(logo.logo_height):
        # Draw one line from logo to OLed
        for i in range(logo.logo_width):
            # read pixel
            px = logo_fb.pixel(i, row)
            oled.pixel(i, row, px)
        # show every 2 rows
        if row % 2 == 1:
            oled.show()
            time.sleep_ms(30)

    oled.show()

    # freeze the full logo for 1 sec
    time.sleep_ms(1000)

    # blink the press to start text
    blink = True
    last_blink = time.ticks_ms()

    while True:
        now = time.ticks_ms()

        # Toggle blink every 500ms
        if time.ticks_diff(now, last_blink) >= 500:
            blink = not blink
            last_blink = now

            # Redraw logo
            oled.fill(0)
            oled.blit(logo_fb, 0, 0)

            # draw press to start txt
            if blink:
                oled.text("PRESS TO START", 8, 54)

            oled.show()

        # check if button
        if button.value() == 0:
            # Debounce
            time.sleep_ms(200)
            if button.value() == 0:
                break
        #buffer btw each loop            
        time.sleep_ms(50)

    # clear the screen
    oled.fill(0)
    oled.show()
