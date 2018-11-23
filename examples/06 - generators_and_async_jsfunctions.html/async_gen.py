import eel

eel.init('web')  # Give folder containing web files
eel.set_timeout(5)


def mycallback(x):
    print(x)


def communicate():
    eel.mygenerator()(mycallback)
    print("Non blocking : the generator will do its work and call my callback")
    
    val = eel.async_say_hello_js('Python World!')()  # Call a Javascript function
    print(val)


if __name__ == "__main__":
    eel.start('async_gen.html', size=(300, 200), block=False)  # Start
    eel.spawn(communicate)
    while True:
        eel.sleep(10)
