# Eel
Eel is a little Python library for making simple Electron-like offline HTML/JS GUI apps, with full access to Python capabilities and libraries. **It lets you annotate functions in Python so that they can be called from Javascript, and vice versa.**

It is designed to take the hassle out of writing short and simple GUI applications. If you are familiar with Python and Electron, probably just jump to one of the [examples](https://github.com/ChrisKnott/Eel/tree/master/examples/file_access).

### Intro

There are several options for making GUI apps in Python, but if you want to use HTML/JS (in order to use jQueryUI or Bootstrap, for example) then you generally have to write a lot of boilerplate code to communicate from the Client (Javascript) side to the Server (Python) side.

The closest Python equivalent to Electron (to my knowledge) is [cefpython](https://github.com/cztomczak/cefpython). It is a bit heavy weight for what I wanted.

Eel is not a fully-fledged as Electron or cefpython - it is probably not suitable for making full blown applications like Atom - but it is very suitable for making the GUI equivalent of little utility scrips you use yourself.

### Install

Install from pypi with `pip`:

    pip install eel

### Usage

#### Structure

An Eel application will be split into a frontend consisting of various web-technology files (.html, .js, .css) and a backend consisting of various Python scripts.

All the frontend files should be put in a single directory (they can be further divided into folders inside this if necessary).

```
my_python_script.py
other_python_module.py
static_web_folder/
  main_page.html
  css/
    style.css
  img/
    logo.png
```

#### Starting the app

Suppose you put all the frontend files in a directory called `web`, including your start page `main.html`, then app is started like this;

```python
import eel
eel.init('web')
eel.start('main.html')
```

This will start a webserver on the default settings (http://localhost:8000) and open a browser to http://localhost:8000/index.html.

If Chrome is installed then by default it will open in Chrome in App Mode (with the `--app` cmdline flag), regardless of what the OS's default browser is. It is possible to override this behaviour.

#### Exposing functions

In addition to the files in the frontend folder, a Javascript library will be served at `/eel.js`. You should include this in any pages:

```html
<script type="text/javascript" src="/eel.js"></script>
```
Including this library creates an `eel` object which can be used to communicate with the Python side.

Any functions in the Python code which are decorated with `@eel.expose` like this...
```python
@eel.expose
def my_python_function(a, b):
    print(a, b, a + b)
```
...will appear as methods on the `eel` object on the Javascript side, like this...
```javascript
console.log('Calling Python...');
eel.my_python_function(1, 2);   // This calls the Python function that was decorated
```

Similarly, any Javascript functions which are exposed like this...
```javascript
eel.expose(my_javascript_function);
function my_javascript_function(a, b, c, d) {
  if(a < b){
    console.log(c * d);
  }
}
```
can be called from the Python side like this...
```python
print('Calling Javascript...')
eel.my_javascript_function(1, 2, 3, 4)  # This calls the Javascript function
```
Any arguments are converted to JSON and send down a websocket (which potentially loses information, but is fine for most situations).

#### Eello, World!

Putting this together into a **Hello, World!** example, we have a short HTML page, `web/hello.html`:
```html
<!DOCTYPE html>
<html>
    <head>
        <title>Hello, World!</title>
        
        <!-- Include eel.js - note this file doesn't exist in the 'web' directory -->
        <script type="text/javascript" src="/eel.js"></script>
        <script type="text/javascript">
        
        eel.expose(say_hello_js);               // Expose this function to Python
        function say_hello_js(x) {
            console.log("Hello from " + x);
        }
        
        say_hello_js("Javascript World!");
        eel.say_hello_py("Javascript World!");  // Call a Python function
        
        </script>
    </head>
    
    <body>
        Hello, World!
    </body>
</html>
```

and a short Python script `hello.py`:
```python
import eel

eel.init('web')                     # Give folder containing web files

@eel.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
eel.say_hello_js('Python World!')   # Call a Javascript function

eel.start('hello.html')             # Start (this blocks and enters loop)
```

If we run the Python script (`python hello.py`), then a browser window will open displaying `hello.html`, and we will see:
```
Hello from Python World!
Hello from Javascript World!
```
in the terminal, and:
```
Hello from Javascript World!
Hello from Python World!
```
in the browser console (press F12 to open). You will notice that in the Python code, the Javascript function is called before the webserver is even started. Obviously this is impossible - any calls like this are queued up and then sent once the websocket has been established.

#### Return values

While we want to think of our code as comprising a single application, the Python interpreter and the browser window run in separate processes, which can make communicating back and forth between them a bit of a mess, if we always had to explicitly *send* values from one side to the other.

Eel supports two ways of retrieving *return values* from the other side of the app.

##### Callbacks

When you call an exposed function, you can immeadiately pass a callback function afterwards. This callback will automatically be called asynchrounously with the return value when the function has finished executing.

For example, if we have the following function defined and exposed in Javascript:
```javascript
eel.expose(js_random);
function js_random() {
  return Math.random();
}
```
Then in Python we can retrieve random values from the Javascript side like so:
```python
def print_num(n):
    print('Got this from Javascript:', n)

# Call Javascript function, and pass explicit callback function    
eel.js_random()(print_num)

# Do the same with an inline lambda as callback
eel.js_random()(lambda n: print('Got this from Javascript:', n))
```
(It works exactly the same the other way around).

##### Synchronous returns

In most situations, the calls to the other side are to quickly retrieve some piece of data, such as the state of a widget or contents of an input field. In these cases it is more convenient to just synchronously wait a few milliseconds then continue with your code, rather than breaking the whole thing up into callbacks.

To synchronously retrieve the return value, simply pass nothing to the second set of brackets. So in Python we would write:
```python
n = eel.js_random()()  # This immeadiately returns the value
print('Got this from Javascript:', n)
```
In Javascript, the language doesn't allow to us block while we wait for a callback, except by using `await` from an `async` function. So the equivalent code from the Javascript side would be:
```javascript
async function run() {
  // Inside an function marked 'async' we can use the 'await' keyword.
  
  let n = await eel.py_random()();    // Must prefix call with 'await', otherwise the same
  console.log('Got this from Python: ' + n);
}

run();
```

### Asynchronous Python

Eel is built on Bottle and Gevent. If you use Python's built in `thread.sleep()` you will block the entire interpreter. Instead you should use the methods provided by Gevent. For simplicity, the two most commonly needed methods, `sleep()` and `spawn()` are provided directly from Eel.

For example:
```python
import eel
eel.init('web')

def my_other_thread():
    print('I'm a thread')
    eel.sleep(1.0)                  # Must use eel.sleep()
    
eel.spawn(my_other_thread)

eel.start('main.html', block=False) # Don't block on this call

while True:
    print("I'm a main loop")
    eel.sleep(1.0)                  # Must use eel.sleep()
    