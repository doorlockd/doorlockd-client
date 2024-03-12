import gpiod
import time

# chip=gpiod.Chip('gpiochip0')
# lines = chip.get_lines([ 24 ])
c = "1"
l = [19, 18, 28]

print("GPIO chip:{} line:{} blinker".format(c, l))
chip = gpiod.Chip(c)
lines = chip.get_lines(l)

lines.request(
    consumer="blinker :-)", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0, 0, 0]
)


print("GPIO chip:{} line:{}   get_values... ".format(c, l))
print(lines.get_values())

while True:

    print("GPIO chip:{} line:{}   on ".format(c, l))
    lines.set_values([1, 1, 1])
    time.sleep(1)

    print("GPIO chip:{} line:{}   get_values... ".format(c, l))
    print(lines.get_values())

    print("GPIO chip:{} line:{}   off ".format(c, l))
    lines.set_values([0, 0, 0])
    time.sleep(1)
