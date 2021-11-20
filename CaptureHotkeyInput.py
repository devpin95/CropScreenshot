import keyboard

# https://github.com/boppreh/keyboard#keyboard.hook

key_list = []

def mycallback_release(e):
    pass


def mycallback_press(e):
    global key_list
    if e.name == 'esc':
        key_list = []

    if e.name not in key_list:
        key_list.append(e.name)
        hks = ''
        for i in range(0, len(key_list) - 1):
            hks += key_list[i] + '+'

        hks += key_list[-1]
        print(hks)


keyboard.on_press(mycallback_press)
keyboard.on_press(mycallback_release)

keyboard.wait()
