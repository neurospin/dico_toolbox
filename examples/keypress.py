from pynput import keyboard

choice = 'stay'

def on_press(key):
    # try:
    #     print('alphanumeric key {0} pressed'.format(
    #         key.char))
    #     print(type(key))
    # except AttributeError:
    #     print('special key {0} pressed'.format(
    #         key))
    allowed_keys = [keyboard.Key.esc, keyboard.Key.right, keyboard.Key.left]
    if key not in allowed_keys or str(key)[1] == 'q':
        print("press q or escape to quit; press -> to go forward; press <- to go backward")

def on_release(key):
    global choice
    # print('{0} released'.format(key))
    # print(type(key))
    if key == keyboard.Key.esc or str(key)[1] == 'q':
        # Stop listener
        choice = 'end'
        return False
    elif key == keyboard.Key.right:
        choice = 'forward'
        return False
    elif key == keyboard.Key.left:
        choice = 'backward'
        return False

def wait_for_keypress():
    # Collect events until released
    print("press q or escape to quit; press -> to go forward; press <- to go backward")
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()
