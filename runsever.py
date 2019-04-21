# -*- encoding=UTF-8 -*-
#from flask_script import Manager
from photowall2 import app


if __name__ == '__main__':
    #manage = Manager(app)
    app.run(debug=True)
